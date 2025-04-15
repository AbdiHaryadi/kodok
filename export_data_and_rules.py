import json
import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def service():
    # If modifying these scopes, delete the file token.json.
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]

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
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        return build("sheets", "v4", credentials=creds)
    except HttpError as err:
        print(err)
        raise err

def exported_cells_for_rules():
    with open("rules.json") as fp:
        data = json.load(fp)
        data = data["general_specific"]

    exported_cells = []
    for x in data:
        general_questions = x["general_questions"]
        assert len(general_questions) == 1
        general_question = general_questions[0]
        specific_questions = x["specific_questions"]

        is_first_row = True
        for q in specific_questions:
            if is_first_row:
                exported_cells.append([general_question, q])
            else:
                exported_cells.append(["", q])
            is_first_row = False
    return exported_cells

def exported_cells_for_data():
    with open("data.json") as fp:
        data = json.load(fp)

    exported_cells = []
    for x in data:
        name = x["name"]
        questions = x["positive_questions"]

        is_first_row = True
        for q in questions:
            if is_first_row:
                exported_cells.append([name, q])
            else:
                exported_cells.append(["", q])
            is_first_row = False
    return exported_cells

if __name__ == "__main__":
    context = sys.argv[1]
    if context == "data":
        exported_cells = exported_cells_for_data()
        top_cell = "Penyakit!A2"
    elif context == "rules":
        exported_cells = exported_cells_for_rules()
        top_cell = "Aturan Umum-Spesifik!A2"
    else:
        raise ValueError(f"Unknown context: {context}")

    service = service()
    body = {"values": exported_cells}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId="1czLxK26b_N9jmRz4_pxf4N80VUa9Mwa0JZLntZTQmOY",
            range=top_cell,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    print(f"{result.get('updatedCells')} cells updated.")
    print(result)