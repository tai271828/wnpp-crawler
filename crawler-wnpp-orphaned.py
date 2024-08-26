#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import re
from fuzzywuzzy import fuzz
import pickle
import os

# URL of the page to crawl
url = "https://www.debian.org/devel/wnpp/orphaned"

# Keywords to search for
keywords = ["science", "scientific", "physics", "performance", "hcp", "cfd", "fluid", "MRI", "computational"]

# Fuzzy match threshold (0-100)
threshold = 80

# File to store previously found packages
history_file = "package_history.pkl"


# Fetch the API key from the environment variable
api_key = os.getenv("SENDGRID_API_KEY")
email_from = os.getenv("SENDGRID_EMAIL_FROM")
email_to = os.getenv("SENDGRID_EMAIL_TO")
email_subject = os.getenv("SENDGRID_EMAIL_SUBJECT")

if not (api_key and email_from and email_to and email_subject):
    raise ValueError("Necessary environment variables are not set.")

# SendGrid API endpoint
url_sendgrid_api = "https://api.sendgrid.com/v3/mail/send"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def send_result_notification(email_content):
    # Email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": f"{email_to}"}]
            }
        ],
        "from": {"email": f"{email_from}"},
        "subject": f"email_subject",
        "content": [
            {"type": "text/plain", "value": f"{email_content}"}
        ]
    }

    # Send the POST request
    response = requests.post(url_sendgrid_api, json=payload, headers=headers)

    # Check the response
    if response.status_code == 202:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email: {response.status_code}")
        print(response.text)

def load_history():
    if os.path.exists(history_file):
        with open(history_file, "rb") as f:
            return pickle.load(f)
    return set()

def save_history(history):
    with open(history_file, "wb") as f:
        pickle.dump(history, f)

def fuzzy_match(package_name, keyword):
    score = fuzz.partial_ratio(package_name.lower(), keyword.lower())
    if score >= threshold:
        #print(f"Matched {package_name} with {keyword} (score: {score})")
        return True
    else:
        #print(f"Did not match {package_name} with {keyword} (score: {score})")
        return False

def crawl_and_notify():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a", href=lambda href: href and href.startswith("https://bugs.debian.org/"))

    history = load_history()
    new_packages = dict()

    for link in links:
        link_description = link.text.strip()
        package_name = link_description.split(":")[0]
        try:
            package_description = link_description.split(":")[1]
        except:
            package_description = "No description available"
            #print(f"Failed to parse description for {package_name}")

        for keyword in keywords:
            if fuzzy_match(package_name, keyword) and package_name not in history:
                new_packages[package_name] = package_description
                break

    email_content=""
    if new_packages:
        email_content="New packages found:\n"
        for package_name in new_packages:
            email_content += f"- {package_name}: {new_packages[package_name]}\n"

        history.update(new_packages)
        save_history(history)

        print(email_content)
        send_result_notification(email_content)

    else:
        print("No new packages found matching the keywords.")

if __name__ == "__main__":
    crawl_and_notify()

