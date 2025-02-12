import requests
import json
import datetime
import hashlib
import hmac
import base64
import sys

API_KEY = ""
API_SECRET = ""
BASE_URL = "https://api.mimecast.com"

SEARCH_ENDPOINT = "/api/quarantine/search"
RELEASE_ENDPOINT = "/api/quarantine/release"

def generate_signature(method, endpoint, body, timestamp, api_secret):
    """
    Generates an HMAC signature.
    """
    canonical_string = f"{method}{endpoint}{timestamp}{body}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        canonical_string.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def get_headers(method, endpoint, body):
    """
    Prepares headers including the signature.
    """
    timestamp = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    signature = generate_signature(method, endpoint, body, timestamp, API_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "x-mc-app-id": API_KEY,
        "x-mc-date": timestamp,
        "Authorization": "MC " + signature
    }
    return headers

def search_quarantine(sender, subject):
    """
    Searches the Mimecast quarantine for emails matching the sender and subject.
    """
    payload = {
        "data": [
            {
                "criteria": {
                    "fromAddress": sender,
                    "subject": subject
                }
            }
        ]
    }
    body = json.dumps(payload)
    headers = get_headers("POST", SEARCH_ENDPOINT, body)
    url = BASE_URL + SEARCH_ENDPOINT

    print("Sending search request to Mimecast...")
    response = requests.post(url, data=body, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error searching quarantine: {response.status_code} {response.text}")
        return None

def release_message(message_id):
    """
    Releases a quarantined email identified by message_id.
    """
    payload = {
        "data": [
            {
                "id": message_id,
                "folder": "quarantine"
            }
        ]
    }
    body = json.dumps(payload)
    headers = get_headers("POST", RELEASE_ENDPOINT, body)
    url = BASE_URL + RELEASE_ENDPOINT

    print(f"Sending release request for message ID: {message_id}")
    response = requests.post(url, data=body, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error releasing message: {response.status_code} {response.text}")
        return None

def main():
    sender = input("Enter sender email from ticket: ").strip()
    subject = input("Enter subject (or part of subject) from ticket: ").strip()
    
    print("\nSearching for quarantined emails that match the criteria...")
    search_results = search_quarantine(sender, subject)
    if search_results is None:
        print("Search failed. Exiting.")
        sys.exit(1)
    
    matches = search_results.get("data", [])
    if not matches:
        print("No matching quarantined emails found.")
        sys.exit(0)
    
    print("\nFound the following matches:")
    for idx, msg in enumerate(matches):
        msg_id = msg.get("id")
        msg_from = msg.get("fromAddress", "N/A")
        msg_subject = msg.get("subject", "N/A")
        msg_date = msg.get("sentDate", "N/A")
        print(f"{idx+1}: ID: {msg_id}, From: {msg_from}, Subject: {msg_subject}, Date: {msg_date}")
    
    choice = input("\nEnter the number of the message to release (or 'all' to release all found): ").strip().lower()
    if choice == "all":
        for msg in matches:
            message_id = msg.get("id")
            print(f"\nReleasing message ID {message_id}...")
            result = release_message(message_id)
            print("Result:", result)
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                message_id = matches[idx].get("id")
                print(f"\nReleasing message ID {message_id}...")
                result = release_message(message_id)
                print("Result:", result)
            else:
                print("Invalid selection number.")
        except ValueError:
            print("Invalid input; please enter a valid number or 'all'.")

if __name__ == "__main__":
    main()
