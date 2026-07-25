import requests
import json
import time
from datetime import datetime, UTC
import os

# --- Configuration ---
API_KEY = "YOUR_API_KEY_HERE"  # جایگزین شده برای امنیت
API_URL = "https://api.netbeacon.org/submit/reports"
GEO = "IR"
DESCRIPTION = "Organized Pig Butchering (Sha Zhu Pan) cryptocurrency investment scam network. Victims are socially engineered into fake trading platforms and deposits are stolen."
PHISHING_TARGET = "Cryptocurrency Investors" # Required for phishing type
RATE_LIMIT = 3
INPUT_FILE = "domains.txt"
DONE_FILE = "reported.txt"
LOG_FILE = "netbeacon_final.log"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    with open(LOG_FILE, "a") as f:
        f.write(full_msg + "\n")

def send_report(domain):
    clean_url = domain.strip().replace("\r", "").replace("\n", "")
    if not clean_url.startswith(("http://", "https://")):
        clean_url = f"https://{clean_url}"

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Final Payload Construction
    payload = [{
        "type": "phishing",
        "date": timestamp,
        "ongoing": True,
        "url": clean_url,
        "geo": GEO,
        "description": DESCRIPTION,
        "target": PHISHING_TARGET,  # FIX: Added required target field
        "attachments": [
            {
                "name": "evidence.txt",
                "data": "RG9tYWluIGlzIGEgZmFrZSBjcnlwdG8gaW52ZXN0bWVudCBwbGF0Zm9ybSB1c2VkIGZvciBTaGEgWmh1IFBhbiBzY2Ftcy4="
            }
        ]
    }]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)

        if response.status_code in [200, 201]:
            res_data = response.json()

            # If the API still returns a 'bad' list, log the specific error
            if res_data.get("bad"):
                error_detail = json.dumps(res_data["bad"][0]["errors"])
                log_message(f"[REJECTED] {clean_url} - Errors: {error_detail}")
                return False

            log_message(f"[SUCCESS] {clean_url}")
            with open(DONE_FILE, "a") as f:
                f.write(domain + "\n")
            return True

        elif response.status_code == 429:
            log_message("Rate limited (429). Sleeping 60s...")
            time.sleep(60)
            return False
        else:
            log_message(f"[SERVER ERROR {response.status_code}] {response.text}")
            return False

    except Exception as e:
        log_message(f"[EXCEPTION] {str(e)}")
        return False

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    reported = set()
    if os.path.exists(DONE_FILE):
        with open(DONE_FILE, "r") as f:
            reported = {line.strip() for line in f}

    with open(INPUT_FILE, "r") as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    log_message(f"Starting Campaign: {len(domains)} domains.")

    for domain in domains:
        if domain in reported:
            continue

        success = send_report(domain)
        # Adaptive backoff: 3s on success, 5s on minor failure
        time.sleep(RATE_LIMIT if success else 5)

if __name__ == "__main__":
    main()
