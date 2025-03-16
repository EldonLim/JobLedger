import datetime
import firebase_admin
from google.cloud import firestore
from firebase_admin import credentials
import os.path
import json

class database:
    def __init__(self):
        try:
            # Check if the app is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Use the path to the secret-mounted file
            # cred_path = "/secrets/serviceAccountKey.json"
            try:
                data = ""
                with open(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), 'r') as file:
                    data = file.read()
                service_account_info = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid SERVICE_ACCOUNT_KEY JSON format: {str(e)}")
            # Initialize the app
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        self.db =  firestore.Client()

    def get_user_info(self, user_email):
        user_ref = self.db.collection('users_info').document(user_email)
        user_doc = user_ref.get()

        if user_doc.exists:
            return user_doc.to_dict()  # Returns a dictionary of user data
        else:
            print(f"No data found for user: {user_email}")
            return None

    def add_user_to_firestore(self, user_email, sheet_link):
        date = datetime.datetime.now()
        # Reference to the 'users' collection
        user_ref = self.db.collection('users_info').document(user_email)  # You can use the user's email as the document ID or another unique identifier

        # Data to store in the document
        user_data = {
            'user_email': user_email,
            'sheet_link': sheet_link,
            'subscription_date': date,
        }

        # Add data to the Firestore document
        user_ref.set(user_data)
        print(f"User {user_email} has been added to Firestore.")

    def delete_user_from_firestore(self, user_email):
        # Reference to the document in the 'users' collection
        user_ref = self.db.collection('users_info').document(user_email)

        # Delete the document
        user_ref.delete()
        print(f"User with ID {user_email} has been deleted from Firestore.")

    def update_user_info(self, user_email, updated_data: dict):
        user_ref = self.db.collection('users_info').document(user_email)
        user_ref.update(updated_data)
        print(f"User {user_email} has been updated.")




# TESTING PURPOSES
# db = database()

# print(db.get_user_info("A6FAta7lCJcgoL6rDCGX")['user_email'])



# def initialize_firebase(self):
#         # try:
#         #     # Check if the app is already initialized
#         #     firebase_admin.get_app()
#         # except ValueError:
#         #     # Path to your service account JSON file
#         #     cred_path = r"C:\Users\User\Desktop\JobLedger\JobLedger_server\app\jobledgerserverdeployment-387e327ba32b.json"
            
#         #     # Verify the file exists
#         #     if not os.path.exists(cred_path):
#         #         raise FileNotFoundError(f"Service account file not found at: {cred_path}")
                
#         #     # Initialize the app
#         #     cred = credentials.Certificate(cred_path)
#         #     firebase_admin.initialize_app(cred, {
#         #         'projectId': 'jobledgerserverdeployment',  # Add your project ID here
#         #         'databaseURL': 'https://jobledgerserverdeployment.firebaseio.com'  # Optional but recommended
#         #     })
        
#         # Get Firestore client
#         return firestore.Client()