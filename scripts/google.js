const fs = require("fs").promises;
const path = require("path");
const process = require("process");
const { google } = require("googleapis");
const TOKEN_PATH = path.join(process.cwd(), "token.json");
const TOPIC_NAME = "projects/servcy/topics/ServcyGmailInbox";

// Load the credentials from the token.json file
async function loadSavedCredentialsIfExist() {
  try {
    const content = await fs.readFile(TOKEN_PATH);
    const credentials = JSON.parse(content);
    return google.auth.fromJSON(credentials);
  } catch (err) {
    return null;
  }
}

// Function to log the data object to the console
function logCompleteJsonObject(jsonObject) {
  console.log(JSON.stringify(jsonObject, null, 4));
}

// Call the API to get message
async function getMessage(auth, messageId) {
  const gmail = google.gmail({ version: "v1", auth });
  const res = await gmail.users.messages.get({
    userId: "me",
    id: messageId,
  });
  logCompleteJsonObject(res.data);
}

// Connect to Pub Sub
async function connectPubSub(auth) {
  const gmail = google.gmail({ version: "v1", auth });
  const res = await gmail.users.watch({
    userId: "me",
    requestBody: {
      labelIds: ["INBOX"],
      topicName: TOPIC_NAME,
    },
  });
  console.log(res);
}

// Function to log the data object to the console
function logCompleteJsonObject(jsonObject) {
  console.log(JSON.stringify(jsonObject, null, 4));
}

// Get history details based on history ID
async function getHistory(auth, historyId) {
  const gmail = google.gmail({ version: "v1", auth });
  const res = await gmail.users.history.list({
    userId: "me",
    startHistoryId: historyId,
  });
  // The main part of the response comes
  // in the "data" attribute.
  logCompleteJsonObject(res.data);
}

// Run the script
(async () => {
  let cred = await loadSavedCredentialsIfExist();
  await connectPubSub(cred);
  let historyId = 8631681;
  await getHistory(cred, historyId);
  let messageId = "18510ea757da1719";
  await getMessage(cred, messageId);
})();
