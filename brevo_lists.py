###############################################################################
#                          BREVO FULL DEBUG SCRIPT                            #
#                Fetch campaigns, lists, and write to Excel                   #
#          WITH A 15s DELAY TO KEEP UNDER 250 CALLS PER HOUR (240 MAX)        #
###############################################################################

import sys
import time
import logging

# -----------------------------------------------------------------------------
# 1) CHECK ENVIRONMENT
# -----------------------------------------------------------------------------
try:
    import requests
except ImportError:
    print("[ERROR] 'requests' library not found. Install with 'pip install requests'.")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[ERROR] 'pandas' library not found. Install with 'pip install pandas'.")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("[ERROR] 'openpyxl' library not found. Install with 'pip install openpyxl'.")
    sys.exit(1)

print("[INFO] Successfully imported 'requests', 'pandas', and 'openpyxl'.")
print("[INFO] Python version:", sys.version)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("All required libraries are present. Continuing...")

# -----------------------------------------------------------------------------
# 2) BREVO (Sendinblue) API SETUP
# -----------------------------------------------------------------------------
API_KEY = "YOUR API KEY GOES HERE"  # <-- Replace this with your real key
BASE_URL = "https://api.brevo.com/v3"

HEADERS = {
    "accept": "application/json",
    "api-key": API_KEY,
    "content-type": "application/json"
}

# -----------------------------------------------------------------------------
# 3) GLOBAL THROTTLING
# -----------------------------------------------------------------------------
# 3600 seconds / 250 calls = 14.4 seconds per call to stay under 250/hour.
# We'll round up to 15 seconds to be safe. That results in max 240 calls/hour.
SLEEP_SECONDS = 15

def brevo_get(url, headers=None, params=None, timeout=30):
    """
    A wrapper for requests.get() that sleeps for 15 seconds before every call
    to keep the total rate under 250 calls per hour (~240 calls/hour).
    """
    time.sleep(SLEEP_SECONDS)
    return requests.get(url, headers=headers, params=params, timeout=timeout)

# -----------------------------------------------------------------------------
# HELPER FUNCTION: TEST SIMPLE CONNECTIVITY
# -----------------------------------------------------------------------------
def test_connectivity(url="https://www.google.com", timeout=5):
    print(f"[INFO] Testing basic connectivity to {url} with timeout={timeout} seconds...")
    try:
        # For external checks like Google, you might skip the throttle delay.
        # But we'll keep it here for consistency.
        time.sleep(SLEEP_SECONDS) 
        r = requests.get(url, timeout=timeout)
        print(f"[INFO] Received status code: {r.status_code} from {url}")
        logging.debug(f"Response from {url}: {r.text[:200]}... (truncated)")
        return True
    except Exception as e:
        print(f"[ERROR] Connectivity test failed: {e}")
        return False

# -----------------------------------------------------------------------------
# HELPER FUNCTION: TEST BREVO API KEY VALIDITY
# -----------------------------------------------------------------------------
def test_brevo_api_key():
    test_url = f"{BASE_URL}/emailCampaigns"
    print(f"[INFO] Testing Brevo API with {test_url} (limit=1) ...")
    try:
        resp = brevo_get(test_url, headers=HEADERS, params={"limit": 1}, timeout=30)
        logging.debug(f"Raw response text: {resp.text[:300]}... (truncated)")
        if resp.status_code == 200:
            print("[INFO] Brevo API key seems valid (HTTP 200).")
            return True
        else:
            print(f"[ERROR] Brevo API key test got HTTP {resp.status_code} - check your API key.")
            return False
    except requests.exceptions.RequestException as ex:
        print(f"[ERROR] Could not connect to Brevo: {ex}")
        return False

# -----------------------------------------------------------------------------
# 4) GET ALL CAMPAIGNS (WITH PAGINATION)
# -----------------------------------------------------------------------------
def get_all_campaigns(limit=50):
    logging.debug("Entering get_all_campaigns()")
    campaigns = []
    offset = 0
    while True:
        print(f"[INFO] Requesting campaigns batch with limit={limit}, offset={offset}...")
        url = f"{BASE_URL}/emailCampaigns"
        params = {"limit": limit, "offset": offset}

        try:
            response = brevo_get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"[ERROR] HTTP error when fetching campaigns: {http_err}")
            break
        except requests.exceptions.RequestException as req_err:
            print(f"[ERROR] Network error when fetching campaigns: {req_err}")
            break

        data = response.json()
        batch = data.get("campaigns", [])
        print(f"[INFO] Received {len(batch)} campaigns in this batch.")
        logging.debug(f"Batch data snippet: {str(batch)[:500]}...")

        if not batch:
            print("[INFO] No campaigns returned in this batch. Stopping pagination.")
            break

        campaigns.extend(batch)

        if len(batch) < limit:
            print("[INFO] Fewer campaigns than 'limit' returned - end of data.")
            break

        offset += limit

    logging.info(f"Total campaigns fetched: {len(campaigns)}")
    return campaigns

# -----------------------------------------------------------------------------
# 5) GET DETAILS FOR ONE CAMPAIGN
# -----------------------------------------------------------------------------
def get_campaign_details(campaign_id):
    logging.debug(f"Fetching details for campaign ID={campaign_id}")
    url = f"{BASE_URL}/emailCampaigns/{campaign_id}"
    try:
        response = brevo_get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        details = response.json()
        logging.debug(f"Details for campaign {campaign_id}: {str(details)[:500]}...")
        return details
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch campaign ID={campaign_id}: {e}")
        return None

# -----------------------------------------------------------------------------
# 6) GET LIST DETAILS
# -----------------------------------------------------------------------------
def get_list_details(list_id):
    logging.debug(f"Fetching list details for list ID={list_id}")
    url = f"{BASE_URL}/contacts/lists/{list_id}"
    try:
        response = brevo_get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        list_data = response.json()
        logging.debug(f"Raw list data from API: {list_data}")
        return list_data
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch list ID={list_id}: {e}")
        return None

# -----------------------------------------------------------------------------
# 7) MAIN FUNCTION
# -----------------------------------------------------------------------------
def main():
    start_time = time.time()
    print("======================================================================")
    print("[INFO] Starting Brevo campaign-to-Excel script (FULL DEBUG + 15s delay).")
    print(f"[INFO] This limit ensures we stay below 250 calls/hour (~240 calls/hour).")
    print("======================================================================")

    # 7a) TEST BASIC CONNECTIVITY FIRST
    if not test_connectivity():
        print("[ERROR] Basic connectivity test failed. Exiting script.")
        return

    # 7b) TEST BREVO API KEY
    if not test_brevo_api_key():
        print("[ERROR] Brevo API key test failed. Exiting script.")
        return

    # 7c) FETCH ALL CAMPAIGNS
    all_campaigns = get_all_campaigns(limit=20)  # Adjust limit as desired
    print(f"[INFO] Finished fetching campaigns. Total: {len(all_campaigns)}")

    # Prepare a list of rows to store in Excel
    output_rows = []

    # 7d) LOOP THROUGH CAMPAIGNS
    for i, camp in enumerate(all_campaigns, start=1):
        campaign_id = camp.get("id")
        campaign_name = camp.get("name", "No Name")
        print(f"[INFO] Processing Campaign #{i}: ID={campaign_id}, Name='{campaign_name}'")

        details = get_campaign_details(campaign_id)
        if not details:
            print(f"[WARNING] No details found for campaign {campaign_id}. Skipping...")
            continue

        recipients_info = details.get("recipients", {})
        list_ids = recipients_info.get("lists", [])
        segment_ids = recipients_info.get("segments", [])

        if not list_ids and not segment_ids:
            print(f"[INFO] Campaign ID={campaign_id} has no lists or segments.")
            output_rows.append([campaign_id, campaign_name, "No List IDs", "No Segments"])
        else:
            # For each list, fetch details
            for lid in list_ids:
                list_data = get_list_details(lid)
                if list_data and "name" in list_data:
                    list_name = list_data["name"]
                else:
                    list_name = f"Unknown list ID={lid}"
                print(f"[INFO]  - Associated list: ID={lid}, Name='{list_name}'")

                output_rows.append([campaign_id, campaign_name, list_name, None])

            # For each segment
            for seg_id in segment_ids:
                print(f"[INFO]  - Associated segment ID={seg_id}")
                output_rows.append([campaign_id, campaign_name, None, f"Segment ID={seg_id}"])

    # 7e) WRITE TO EXCEL
    df = pd.DataFrame(output_rows, columns=["Campaign ID", "Campaign Name", "List Name", "Segment Info"])

    filename = "brevo_campaigns.xlsx"
    print(f"[INFO] Writing results to '{filename}' in the current directory. Please wait...")
    try:
        df.to_excel(filename, index=False)
        print(f"[INFO] Successfully wrote {len(df)} rows to '{filename}'.")
    except Exception as exc:
        print(f"[ERROR] Failed to write Excel file: {exc}")
        return

    elapsed = time.time() - start_time
    print("[INFO] Script execution completed.")
    print(f"[INFO] Total execution time: {elapsed:.2f} seconds.")
 
# 8) ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
