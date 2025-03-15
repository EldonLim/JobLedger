
async function createTextArea(userEmail,
    jobData = {
    title: '',
    company: '',
    description: ''
    }) {
  // Create overlay background
  const overlay = document.createElement('div');
  overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10000;
  `;

  // Create modal container
  const modal = document.createElement('div');
  modal.style.cssText = `
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      width: 400px;
      position: relative;
  `;

  // Create title
  const title = document.createElement('h3');
  title.textContent = 'Confirm Job Details';
  title.style.cssText = `
      margin: 0 0 15px 0;
      font-size: 18px;
      color: #333;
  `;

  // Create title label
  const titleLabel = document.createElement('label');
  titleLabel.textContent = 'Job Title:';
  titleLabel.style.cssText = `
      font-size: 14px;
      color: #333;
      white-space: nowrap;
  `;

  // Create title textarea
  const title_textarea = document.createElement('textarea');
  title_textarea.style.cssText = `
      width: 100%;
      height: 36px;
      padding: 1 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 10px;
      font-family: inherit;
      box-sizing: border-box;
      vertical-align: middle;
      resize: none;
  `;
  title_textarea.value = jobData.title;
  title_textarea.placeholder = 'Enter job title...';

  // Create company label
  const companyLabel = document.createElement('label');
  companyLabel.textContent = 'Company:';
  companyLabel.style.cssText = `
      margin: 0px 0px 3px;
      font-size: 14px;
      color: #333;
      white-space: nowrap;
  `;

  // Create company textarea
  const company_textarea = document.createElement('textarea');
  company_textarea.style.cssText = `
      width: 100%;
      height: 36px;
      padding: 1 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 10px;
      font-family: inherit;
      box-sizing: border-box;
      vertical-align: middle;
      resize: none;
  `;
  company_textarea.value = jobData.company;
  company_textarea.placeholder = 'Company name...';

  // Create description label
  const descriptionLabel = document.createElement('label');
  descriptionLabel.textContent = 'Description:';
  descriptionLabel.style.cssText = `
      margin: 0px 0px 3px;
      font-size: 14px;
      color: #333;
      white-space: nowrap;
  `;

  // Create description textarea
  const description_textarea = document.createElement('textarea');
  description_textarea.style.cssText = `
      width: 100%;
      height: 100px;
      padding: 1 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 10px;
      font-family: inherit;
      box-sizing: border-box;
      resize: vertical;
  `;
  description_textarea.value = jobData.description;
  description_textarea.placeholder = 'Job Description...';

  // Create notes label
  const notesLabel = document.createElement('label');
  notesLabel.textContent = 'Additional Notes:';
  notesLabel.style.cssText = `
      margin: 0px 0px 3px;
      font-size: 14px;
      color: #333;
      white-space: nowrap;
  `;

  // Create description textarea
  const notes_textarea = document.createElement('textarea');
  notes_textarea.style.cssText = `
      width: 100%;
      height: 50px;
      padding: 1 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 15px;
      font-family: inherit;
      box-sizing: border-box;
      resize: vertical;
  `;
  notes_textarea.placeholder = 'Additional Notes (Optional)';

  // Create buttons container
  const buttonsContainer = document.createElement('div');
  buttonsContainer.style.cssText = `
      display: flex;
      justify-content: flex-end;
      gap: 10px;
  `;

  // Create submit button
  const submitButton = document.createElement('button');
  submitButton.textContent = 'Confirm';
  submitButton.style.cssText = `
      padding: 8px 16px;
      background-color: #4CAF50;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
  `;
  submitButton.onmouseover = () => submitButton.style.backgroundColor = '#45a049';
  submitButton.onmouseout = () => submitButton.style.backgroundColor = '#4CAF50';

  // Create cancel button
  const cancelButton = document.createElement('button');
  cancelButton.textContent = 'Cancel';
  cancelButton.style.cssText = `
      padding: 8px 16px;
      background-color: #f44336;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
  `;
  cancelButton.onmouseover = () => cancelButton.style.backgroundColor = '#da190b';
  cancelButton.onmouseout = () => cancelButton.style.backgroundColor = '#f44336';

  // Assemble the modal
  buttonsContainer.appendChild(cancelButton);
  buttonsContainer.appendChild(submitButton);
  modal.appendChild(title);
  modal.appendChild(titleLabel);
  modal.appendChild(title_textarea);
  modal.appendChild(companyLabel);
  modal.appendChild(company_textarea);
  modal.appendChild(descriptionLabel);
  modal.appendChild(description_textarea);
  modal.appendChild(notesLabel);
  modal.appendChild(notes_textarea);
  modal.appendChild(buttonsContainer);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Add click handlers
  submitButton.addEventListener('click', async () => {
    // TO CHANGE TO THE DETAILS INTO MY BACKEND
    const updatedJobDetails = {
        job_title: title_textarea.value, // Assuming you have a text area for title
        company_name: company_textarea.value, // Assuming you have a text area for company
        job_description: description_textarea.value, // Convert multi-line input back to an array
        notes: notes_textarea.value,
    };

    const date = new Date();
    const formattedDate = date.toISOString().split('T')[0];

    updatedJobDetails.status = "Pending";
    updatedJobDetails.date_applied = formattedDate;

    // Log or send updated details to the backend
    await addJobToSheet(userEmail, updatedJobDetails);

    document.body.removeChild(overlay);
  });

  cancelButton.addEventListener('click', () => {
      document.body.removeChild(overlay);
  });

  // Close modal when clicking outside
  overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
          document.body.removeChild(overlay);
      }
  });

  // Prevent closing when clicking inside modal
  modal.addEventListener('click', (e) => {
      e.stopPropagation();
  });

  // Focus textarea
  textarea.focus();
}

console.log('content.js loaded');

async function addJobToSheet(userEmail, finalJobDetails) {
    const backendUrl = "https://jobledgerimg-167652472526.asia-southeast1.run.app/api/sheets";

    const payload = {
        user_email: userEmail,
        updatedJobDetails: finalJobDetails
    }

    console.log(payload);

    // Make a POST request
    try {
        // Make a POST request
        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            mode: "cors",
            body: JSON.stringify(payload), // Convert payload to JSON string
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json(); // Parse the JSON response
        console.log(data)
        return data; // Return the parsed JSON object
    } catch (error) {
        console.error("Error sending data to backend:", error);
        alert(`Error sending data to backend: ${error.message}`);
        return null; // Return null if there's an error
    }
}

async function sendTextToBackend(userEmail, extractedText) {
    const backendUrl = "https://jobledgerimg-167652472526.asia-southeast1.run.app/api/query";

    // Prepare the payload matching the expected format
    const payload = {
        "query": extractedText,
        "user_email": userEmail
    };

    // Make a POST request
    try {
        // Make a POST request
        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            mode: "cors",
            body: JSON.stringify(payload), // Convert payload to JSON string
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json(); // Parse the JSON response
        console.log("Response from backend:", data);

        return data; // Return the parsed JSON object
    } catch (error) {
        console.error("Error sending data to backend:", error);
        alert(`Error sending data to backend: ${error.message}`);
        return null; // Return null if there's an error
    }
}

async function extractJobDetails(userEmail, extractedText){
    const jobDetails = await sendTextToBackend(userEmail, extractedText);

    if (jobDetails) {
        // Extract relevant fields
        const finalJobDetails = {
            title: jobDetails.job_title,
            company: jobDetails.company_name,
            description: jobDetails.job_description.map((item, index) => `${index + 1}. ${item}`).join("\n")
        };
        return finalJobDetails;
    } else {
        console.error("Failed to retrieve job details");
        return null;
    }
}

async function handleJobDetails(userEmail, extractedText) {
    try {
        const finalJobDetails = await extractJobDetails(userEmail, extractedText); // Wait for the job details
        // Pass the resolved finalJobDetails to createTextArea
        console.log(finalJobDetails)
        createTextArea(userEmail, finalJobDetails);
    } catch (error) {
        console.error("Error handling job details:", error);
    }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'start-process') {
        // Extracted text from popup.js
        const userEmail = message.data.userEmail;
        // const userEmail = userInfo.email || 'anonymous' // Use "anonymous" if no email is available
        
        const extractedText = message.data.extractedText;
        handleJobDetails(userEmail, extractedText);
    }
});

