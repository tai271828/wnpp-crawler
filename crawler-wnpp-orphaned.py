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

    if new_packages:
        print("New packages found:")
        for package_name in new_packages:
            print(f"- {package_name}: {new_packages[package_name]}")

        history.update(new_packages)
        save_history(history)

        # this is for github action: failed the job to highlight the new discovers
        sys.exit("Found new orphaned packages that you are potentially interested!!")
    else:
        print("No new packages found matching the keywords.")

if __name__ == "__main__":
    crawl_and_notify()

