import base64
import os.path
import lxml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def instance_check_gmail(start=0, end=1, last=False):

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        result = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = result.get("messages")

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    if last:
        end = len(messages)
    result = []
    for msg in messages[start:end]:
        print(f'got letter with id:{msg["id"]}')
        result.append(msg["id"])
    return result


def check_gmail(start=0, end=1, last=False):

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        result = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
        messages = result.get("messages")

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    def unpack_multipart(payload):
        if "multipart" in payload["mimeType"]:
            a = []
            mult = payload.get("parts")
            for m in mult:
                if "multipart" in m["mimeType"]:
                    a.extend(unpack_multipart(m))
        a.extend(mult)
        return a

    if last:
        end = len(messages)
    result = []
    for msg in messages[start:end]:
        temp = {
            "id": msg["id"],
            "date": "",
            "topic": "",
            "sender": "",
            "text": "",
            "attachments": {},
        }
        txt = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = txt["payload"]
        headers = payload["headers"]
        # print(headers)
        for d in headers:
            if d["name"] == "Subject":
                temp["topic"] = d["value"]
                print(f'got subject for letter id:{ msg["id"]} -- {temp["topic"]}')
            if d["name"] == "From":
                temp["sender"] = d["value"]
        if "multipart" in payload["mimeType"]:
            parts = unpack_multipart(payload)
            for p in parts:
                if "multipart" not in p["mimeType"]:
                    if p["filename"] == "":
                        text = p["body"]["data"]
                    else:
                        # if 'attachment' in p['headers'][0]['value']:
                        filename = str(p["filename"])

                        att_id = p.get("body")["attachmentId"]
                        att = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(userId="me", messageId=msg["id"], id=att_id)
                            .execute()
                        )
                        data = att["data"]
                        temp["attachments"][filename] = str(data)

        else:
            text = payload.get("body")["data"]
        if text:
            text = text.replace("-", "+").replace("_", "/")
            text = base64.b64decode(text).decode("utf-8")
            soup = BeautifulSoup(text, "lxml")
            body = soup.find_all("div")
            real_text = ""
            for i in body:
                # print(i)
                i = i.text
                i = i.replace("\xa0", " ").strip()
                real_text += i + "\n"
            if real_text == "":
                temp["text"] = text
            else:
                temp["text"] = real_text
        else:
            text = ""
            temp["text"] = text
        result.append(temp)
    return result


def get_attachments(start, end):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        result = service.users().messages().list(userId="me").execute()
        messages = result.get("messages")

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
