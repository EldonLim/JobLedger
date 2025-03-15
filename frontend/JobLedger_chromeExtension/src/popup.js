'use strict';


let recordJobButton = document.getElementById('recordJobButton');
let getLinkButton = document.getElementById('getLinkButton');
console.log("popup.js page loaded");

recordJobButton.addEventListener("click", async() => {
    // get current active tab
    console.log("Button clicked");

    // Fetch user info
    const userEmail = await getUserInfo();
    console.log(userEmail)

    let [tab] = await chrome.tabs.query({active: true, currentWindow: true});

    // execute script to extract texts on webpage
    chrome.scripting.executeScript({
    target: {tabId: tab.id},
    func: extractTextFromPage,
    }, (injectionResults ) => {
        // After extracting text, send a message to content.js to trigger the prompt
        const extractedText = injectionResults [0].result;
        console.log("Extracted text:", extractedText);

        // Send the message to content.js to display the text area and get user input
        chrome.tabs.sendMessage(tab.id, { 
            type: 'start-process', 
            data: {
                userEmail,
                extractedText
            }
        });
    });
    
})
    
getLinkButton.addEventListener("click", async() => {
    console.log("button Pressed")
    try {
        const userEmail = await getUserInfo();
        console.log(userEmail)
        // userInfo structure = {email: 'eldonlimkaijie114@gmail.com', id: '111243636461832021658'}
        const response = await sendToBackend(userEmail)
        const google_sheet_link = response['sheet_url']
        if (google_sheet_link) {
            window.open(google_sheet_link, '_blank'); // Opens the link in a new tab
        } else {
            alert('No link returned from the server.');
        }
    } catch (error) {
        console.error('Failed to get user info:', error.message);
    }

})



// function to extract text
function extractTextFromPage() {
    const extractedText = document.body.innerText;
    // console.log(extractedText);
    return extractedText;
  }

// Function to fetch user info using Chrome Identity API
async function getUserInfo() {
    return new Promise((resolve, reject) => {
        chrome.identity.getProfileUserInfo({'accountStatus': 'ANY'}, function(info) {
            const email = info.email;
            resolve(email);
        });
    });
}

// Function to send data to the backend server
async function sendToBackend(user_email) {
    const serverUrl = 'https://jobledgerimg-167652472526.asia-southeast1.run.app/api/link';

    const data = {
        userEmail: user_email || 'anonymous', // Use "anonymous" if no email is available
    };

    try {
        const response = await fetch(serverUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const responseData = await response.json();
        console.log("Google Sheet Link: ", responseData);
        return responseData
    } catch (error) {
        console.error("Failed to send data to backend:", error);
    }
}