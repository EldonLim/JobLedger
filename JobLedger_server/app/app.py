# Main entry point for the server
from huggingface_hub import InferenceClient
import config
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import firestore_setup
from googleapiclient.errors import HttpError
from google.cloud import secretmanager
from google.oauth2 import service_account

class Server:
    def __init__(self):
        repo_id = "mistralai/Mistral-7B-Instruct-v0.3"
        api_key = os.environ.get('HF_API_KEY')

        self.llm_client = InferenceClient(
            model=repo_id,
            api_key=api_key,
            timeout=60
        )

        self.SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.metadata'
        ]

        self.project_id = "jobledgerserverdeployment"

        # Get credentials and initialize services
        credentials = self._get_credentials()
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def _get_credentials(self):
        # Retrieve credentials.json from Secret Manager
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=self.SCOPES
        )

        return credentials

    def jsonResult(self, response: str):
        # Regular expression to match JSON objects
        json_matches = re.findall(r'\{\s*"job_title":.*?\}', response, re.DOTALL)

        if json_matches:
            # Select the last JSON object
            last_json_string = json_matches[-1]
            
            # Parse the JSON string to verify it's valid JSON (optional)
            try:
                parsed_json = json.loads(last_json_string)
                parsed_json["status"] = "New"
                parsed_json["notes"] = ""
                # testing purposes
                # print("Extracted JSON:")
                # print(json.dumps(parsed_json, indent=4))  # Pretty print the JSON
                return parsed_json
            except json.JSONDecodeError:
                print("Failed to parse JSON.")
        else:
            print("No JSON found in the text.")

    def call_llm(self, prompt: str):
        response = self.llm_client.post(
            json={
                "inputs": 
                f"""
                    Process the following text and extract only the job details. Return the details in the JSON format below, strictly without any additional text, explanation, or the original query:
                    {{
                        "job_title": "title of the job",
                        "company_name": "company name",
                        "job_description": [
                            "description of the job in point form"
                        ]
                    }}

                    Text to process:   
                    {prompt}
                """,
                "task": "text-generation",
                "parameters": {"max_new_tokens": 700},
            },
        )
        response = json.loads(response.decode())[0]["generated_text"]
        # print(response)
        return self.jsonResult(response)
      
    def append_to_sheet(self, spreadsheet_id: str, range_name: str, job_data: dict):
        print(f"Appending data to sheet...")  # Debugging line
        values = [
            [
                job_data.get('job_title', ''),
                job_data.get('company_name'),
                job_data.get('date_applied', ''),
                job_data.get('job_description', []),
                job_data.get('status', 'Pending'),
                job_data.get('notes', '')
            ]
        ]
        
        body = {
            'values': values
        }
        
        try:
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return result
        except Exception as e:
            print(f"Error appending to sheet: {e}")
            return None
        
    def add_status_data_validation(self, spreadsheet_id: str):
        try:
            # Define the data validation rule for the 'Status' column (e.g., column F)
            requests = [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": 0,  # Assuming the first sheet, change if necessary
                            "startRowIndex": 1,
                            "endRowIndex": 1000,
                            "startColumnIndex": 4,  # Column F is index 5 (zero-based)
                            "endColumnIndex": 5   # End column is F
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": "Pending"},
                                    {"userEnteredValue": "Approved"},
                                    {"userEnteredValue": "Rejected"}
                                ]
                            },
                        }
                    }
                }
            ]

            # Apply the data validation rule to the status column
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": requests
                }
            ).execute()

            print("Data validation applied successfully!")
        except Exception as e:
            print(f"Error applying data validation: {e}")

    def add_status_conditional_formatting(self, spreadsheet_id: str):
        try:
            requests = [
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{
                                "sheetId": 0,
                                "startRowIndex": 1,
                                "endRowIndex": 1000,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": "Pending"}]
                                },
                                "format": {
                                    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0}
                                }
                            }
                        },
                        "index": 0,
                    }
                },
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{
                                "sheetId": 0,
                                "startRowIndex": 1,
                                "endRowIndex": 1000,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": "Approved"}]
                                },
                                "format": {
                                    "backgroundColor": {"red": 0, "green": 0.85, "blue": 0}
                                }
                            }
                        }
                    }
                },
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{
                                "sheetId": 0,
                                "startRowIndex": 1,
                                "endRowIndex": 1000,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5
                            }],
                            "booleanRule": {
                                "condition": {
                                    "type": "TEXT_EQ",
                                    "values": [{"userEnteredValue": "Rejected"}]
                                },
                                "format": {
                                    "backgroundColor": {"red": 0.85, "green": 0, "blue": 0}
                                }
                            }
                        }
                    }
                }
            ]

            body={"requests": requests}
            response = (
                self.sheets_service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )


            print(f"Formatting applied successfully: {response}")

        except Exception as e:
            print(f"Error applying conditional formatting: {e}")

    def create_and_share_sheet(self, sheet_title: str):
        try:
            # Step 1: Create a new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': sheet_title
                }
            }
            spreadsheet = self.sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            print(f"Spreadsheet created with ID: {spreadsheet_id}")
            
            # Step 2: Set permissions to "anyone with the link can edit"
            permission_body = {
                'type': 'anyone',
                'role': 'writer',
                'allowFileDiscovery': False
            }
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission_body,
                supportsAllDrives=True,
                sendNotificationEmail=False
            ).execute()
            
            # Step 3: Generate and return the link
            share_link = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            print(f"Spreadsheet link: {share_link}")
            return share_link
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    # run this only for new users
    def trigger_new_sheet(self, user_email: str):
        sheet_title = f"User_{user_email}_Sheet"
        sheet_link = self.create_and_share_sheet(sheet_title)
        if sheet_link:
            print(f"New sheet created and shared: {sheet_link}")
            spreadsheet_id = sheet_link.split("/")[5]  # The ID is typically in the URL at this position
            new_sheet_title = {
                "job_title": "Job Title",
                "company_name": "Company",
                "job_description": "Job Description",
                "date_applied": "Date Applied",
                "status": "Status",
                "notes": "Additional Notes"
            }
            self.append_to_sheet(spreadsheet_id, 'Sheet1!A:F', new_sheet_title)
            return {
                "spreadsheetId": spreadsheet_id,
                "spreadsheetUrl": sheet_link
            }
        else:
            print("Failed to create and share the sheet.")
        
    def append_to_existing_sheet(self, spreadsheet_id: str, job_data: dict):
        self.append_to_sheet(spreadsheet_id, 'Sheet1!A:F', job_data)
        self.add_status_data_validation(spreadsheet_id)
        self.add_status_conditional_formatting(spreadsheet_id)

app = Flask(__name__)
CORS(app)

server = Server()
db = firestore_setup.database()

@app.route("/api/query", methods=['POST'])
def handle_query():
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query']
        user_email = data['user_email']

        result = server.call_llm(query)

        userExist = db.get_user_info(user_email)
        
        if not userExist:
            # Create a new Google Sheet and get the link
            # sheet_info = server.trigger_new_sheet(user_email)
            # sheet_url = sheet_info["spreadsheetUrl"]
            # db.add_user_to_firestore(user_email, sheet_url, 'paid')
            return None
        else:
            sheet_url = userExist['sheet_link']
            if not sheet_url:
                sheet_info = server.trigger_new_sheet(user_email)
                sheet_url = sheet_info["spreadsheetUrl"]
                db.add_user_to_firestore(user_email, sheet_url)
            
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/api/sheets", methods=['POST'])
def handle_google_sheets():
    try:
        job_data = request.get_json()
        if not job_data:
            return jsonify({'error': 'No data provided'}), 400
            
        # job_data format
        # job_data = {
        #     user_email: "abc123@gmail.com",
        #     updatedJobDetails: {
        #          company: "TikTok",
        #          description: Array
        #          notes: "",
        #          status: "new",
        #          timestamp: "2024-12-08",
        #          title: "Software Engineer"
        #       }
        # }

        userEmail = job_data['user_email']
        job_details = job_data['updatedJobDetails']
        userExist = db.get_user_info(userEmail)

        if not userExist or userExist == 'anonymous':
             # Create a new Google Sheet and get the link
            sheet_info = server.trigger_new_sheet(userEmail)
            spreadsheet_id = sheet_info["spreadsheetId"]
            sheet_url = sheet_info["spreadsheetUrl"]
            db.add_user_to_firestore(userEmail, sheet_url)
            server.append_to_existing_sheet(spreadsheet_id, job_details)
            return jsonify({
                'message': 'New sheet created and data appended successfully!',
                'sheet_url': sheet_url
            }), 200
        else:
            # Found user in database
            sheet_url = userExist['sheet_link']
            spreadsheet_id = sheet_url.split("/")[5]
            server.append_to_existing_sheet(spreadsheet_id, job_details)
            return jsonify({
                'message': 'Existing sheet found and data appended successfully!',
                'sheet_url': sheet_url
            }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/link", methods=['POST'])
def handle_sheet_link():
    # get from database
    try:
        userEmail = request.get_json().get("userEmail")
        if not userEmail:
            return jsonify({'error': 'No data provided'}), 400
            
        userExist = db.get_user_info(userEmail)
        
        if not userExist or userExist == 'anonymous':
            # Create a new Google Sheet and get the link
            # sheet_info = server.trigger_new_sheet(userEmail)
            # sheet_url = sheet_info["spreadsheetUrl"]
            # db.add_user_to_firestore(userEmail, sheet_url, 'paid')
            # return jsonify({
            #     'message': 'New sheet created successfully!',
            #     'sheet_url': sheet_url
            # }), 200
            return None
        else:
            sheet_url = userExist['sheet_link']
            if not sheet_url:
                sheet_info = server.trigger_new_sheet(userEmail)
                sheet_url = sheet_info["spreadsheetUrl"]
                db.add_user_to_firestore(userEmail, sheet_url)
            return jsonify({
                'message': 'Existing sheet found!',
                'sheet_url': sheet_url
            }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
    



# server = Server()
# server.call_llm("0 notifications total Skip to search Skip to main content Keyboard shortcuts Close jump menu Search by title, skill, or company City, state, or zip code Home My Network Jobs 2 2 new messages notifications Messaging 16 16 new notifications Notifications Me For Business Try Premium for SGD0 Top job picks for you Based on your profile, preferences, and activity like applies, searches, and saves 62 results Jump to active job details Jump to active search result Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start with verification TikTok Singapore 1 connection works here Viewed Promoted Be an early applicant iOS/Android Engineer Intern - Intelligent Creation - 2025 Start iOS/Android Engineer Intern - Intelligent Creation - 2025 Start with verification TikTok Singapore 95 company alumni work here 95 Nanyang Technological University Singapore company alumni work here Promoted Be an early applicant Uni Internship Jan to Jun 2025 - Software Engineering Internship Uni Internship Jan to Jun 2025 - Software Engineering Internship with verification Synapxe Singapore, Singapore (Hybrid) 36 company alumni work here 36 Nanyang Technological University Singapore company alumni work here Promoted Salesforce Engineer Intern Salesforce Engineer Intern with verification ShopBack Singapore, Singapore (Hybrid) 2 company alumni work here 2 Nanyang Technological University Singapore company alumni work here Promoted PowerApps developer Intern PowerApps developer Intern with verification CMA CGM Singapore, Singapore (On-site) 69 school alumni work here 69 Nanyang Technological University Singapore school alumni work here Promoted Easy Apply Uni Internship Jan to May 2025 - Enhancement to Inventory Management Systems Uni Internship Jan to May 2025 - Enhancement to Inventory Management Systems with verification Synapxe Singapore, Singapore (Hybrid) 334 school alumni work here 334 Nanyang Technological University Singapore school alumni work here Promoted AI Scientist Intern AI Scientist Intern with verification ADVANCE.AI Singapore, Singapore (On-site) 9 school alumni work here 9 Nanyang Technological University Singapore school alumni work here Promoted 1 2 3 TikTok Share Show more options Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start Singapore · 1 week ago · 3 people clicked apply Dismiss job tip We highlight job details that match your preferences and skills. Click below to view and edit them. Internship Matches your job preferences, job type is Internship. Apply Save Save Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start at TikTok Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start TikTok · Singapore Apply Save Save Algorithm Engineer Intern (Intelligent Customer Service), TikTok Global e-Commerce - 2025 Start at TikTok Show more options How your profile and resume fit this job Get AI-powered advice on this job and more exclusive features with Premium. Try Premium for SGD0 Tailor my resume to this job Am I a good fit for this job? How can I best position myself for this job? People you can reach out to Brett and others in your network Show all About the job Responsibilities TikTok will be prioritizing applicants who have a current right to work in Singapore, and do not require TikTok's sponsorship of a visa. TikTok is the leading destination for short-form mobile video. At TikTok, our mission is to inspire creativity and bring joy. TikTok's global headquarters are in Los Angeles and Singapore, and its offices include New York, London, Dublin, Paris, Berlin, Dubai, Jakarta, Seoul, and Tokyo. Why Join Us Creation is the core of TikTok's purpose. Our platform is built to help imaginations thrive. This is doubly true of the teams that make TikTok possible. Together, we inspire creativity and bring joy - a mission we all believe in and aim towards achieving every day. To us, every challenge, no matter how difficult, is an opportunity; to learn, to innovate, and to grow as one team. Status quo? Never. Courage? Always. At TikTok, we create together and grow together. That's how we drive impact - for ourselves, our company, and the communities we serve. Join us. About The Team Our team is responsible for developing state-of-the-art NLP/ML algorithms and strategies to improve user consumption experience, inspire merchants' service quality and revenue, and build a fair and flourishing ecosystem on our E-commerce Platform. More specifically, our team is responsible for the algorithms of Intelligent Customer Service and machine translation under TikTok's global e-commerce business. Candidates can apply to a maximum of two positions and will be considered for jobs in the order you apply. The application limit is applicable to TikTok and its affiliates' jobs globally. Applications will be reviewed on a rolling basis - we encourage you to apply early. Successful candidates must be able to commit to at least 3 months long internship period. What You Will Do: Participate in the development of AI customer service within the TikTok e-commerce ecosystem to help our sellers better serve our customers. Responsible for the language quality of the TikTok shopping platform, including improving machine translation quality of product information, IM of buyers and sellers, and supporting scenario of cross-lingual searching. Collaborate with product managers, data scientists, and the product strategy & operation team to define product strategies and features. Responsibilities: Build an intelligent dialogue system, including mining questions and answers. Language understanding, including intention recognition, emotion recognition, FAQ, etc. Develop multilingual text generation such as products' copy, dialogue summary, email reply, etc. Construct knowledge graphs of buyers and products. Qualifications Minimum Qualifications Undergraduate, who is currently pursuing a degree/master in Computer Science or related technical field Internship experience in one of the following fields: Machine Learning, NLP, and Computer Vision Experience with software development in at least one of the following programming languages: C++, Python, Go, Java Preferred Qualifications Good sense of teamwork and communication skills, practical experience in relevant business scenarios is preferred. TikTok is committed to creating an inclusive space where employees are valued for their skills, experiences, and unique perspectives. Our platform connects people from across the globe and so does our workplace. At TikTok, our mission is to inspire creativity and bring joy. To achieve that goal, we are committed to celebrating our diverse voices and to creating an environment that reflects the many communities we reach. We are passionate about this and hope you are too. By submitting an application for this role, you accept and agree to our global applicant privacy policy, which may be accessed here: https://careers.tiktok.com/legal/privacy. If you have any questions, please reach out to us at apac-earlycareers@tiktok.com. Job search faster with Premium Access company insights like strategic priorities, headcount trends, and more Surbhi and millions of other members use Premium Try Premium for SGD0 1-month free trial. We’ll send you a reminder 7 days before your trial ends. About the company TikTok 3,130,983 followers Following Entertainment Providers 10,001+ employees 71,023 on LinkedIn TikTok is the world's leading destination for short-form video. Our platform is built to help imaginations thrive. This is doubly true of the teams that make TikTok possible. Our employees lead with curiosity, and move at the speed of culture. Combined with our company's flat structure, you'll be given dynamic opportunities to make a real impact on a rapidly expanding company as you grow your career. We have offices across Asia Pacific, the Middle East, Europe, and the Americas – and we're just getting started. … show more Interested in working with us in the future? Privately share your profile with our recruiters – you’ll be noted as expressing interest for up to a year and be notified about jobs and updates. Learn more Learn more about Interested in working for our company I’m interested Company photos Page 1 of 3 Previous Next May 19, 2021 May 20, 2021 January 16, 2019 Show more Status is online Messaging You are on the messaging overlay. Press enter to open the list of conversations. 2 Compose message You are on the messaging overlay. Press enter to open the list of conversations.")