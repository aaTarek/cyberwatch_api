#!/usr/bin/env python
import requests
from cbw_helper import *
from cbw_mail import *
from urllib3.exceptions import InsecureRequestWarning
import sys
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

############################################################
# CONFIGURATION - USE THIS SECTION TO CONFIGURE SCRIPT
############################################################

GROUPS_TO_SUPERVISE = ["Web", "Active Directory"]

# MAIL OPTIONS

MAIL_SENDER = ""
MAIL_RECEIVER = ""
MAIL_SUBJECT = "Cyberwatch - Critical CVEs report"

############################################################

GROUPS = [GROUP for GROUP in retrieve_groups() if GROUP["name"] in GROUPS_TO_SUPERVISE]
if not GROUPS:
    print("[-] No specified group has been found")
    sys.exit(1)

CONFIG = parseConfigurationFile()
_SUMMARY_ARRAY = []
_OLD_CVE_ARRAY = []

for GROUP in GROUPS:
    # Retrieving every assets in a group 
    ASSETS = retrieve_assets(GROUP)

    # Retrieving CVEs linked to "linux_kernel"
    LINUX_KERNEL_CVES = retrieve_cves(GROUP = GROUP, level = "level_critical", product="linux_kernel")
    # RRetrieving CVEs linked to microsoft
    MICROSOFT_CVES = retrieve_cves(GROUP = GROUP, level = "level_critical", vendor="microsoft")
    # Keeping only CVEs published more than 60 days ago
    CVES = [CVE for CVE in LINUX_KERNEL_CVES + MICROSOFT_CVES if older_than_2_months(CVE["published"])]

    print("Retrieving CVE ")
    for counter, CVE_INDEX in enumerate(CVES):
        print("\033[A\033[A\nRetrieving " + CVE_INDEX["cve_code"] + " - " + str(counter + 1) + " / " + str(len(CVES)) + "     ")
        try:
            # Retrieving CVE data
            CVE = retrieve_cve(CVE_INDEX["cve_code"])
        except Exception as e:
            continue
        
        if counter > 10: break

        for SERVER in CVE["servers"]:
            ASSET = {
                "CVE_SERVER" : SERVER,
                "INDEX" : next((asset for asset in ASSETS if asset["id"] == SERVER["id"]), None)
            }

            # If the asset's data is uncomplete, ignoring
            if not ASSET["CVE_SERVER"] or not ASSET["INDEX"] : continue 

            # If we don't want to include CVE found less than 2 months ago, uncomment this line
            # if not older_than_2_months(ASSET["CVE_SERVER"]["detected_at"]): continue

            # If the CVE is not linked to a KB on a microsoft asset
            if "windows" in ASSET["CVE_SERVER"]["os"]["type"].lower() and not "packages::kb" in [update["target"]["type"].lower() for update in ASSET["CVE_SERVER"]["updates"]]: 
                continue

            _OLD_CVE_ARRAY.append({
                "CVE_CODE" : CVE["cve_code"],
                "AFFECTED_ASSET_ID" : ASSET["CVE_SERVER"]["id"],
                "AFFECTED_ASSET" : ASSET["CVE_SERVER"]["hostname"],
                "GROUPS" : " ".join([group["name"] for group in ASSET["INDEX"]["groups"]]),
                "LAST_ANALYZED" : format_date(ASSET["INDEX"]["analyzed_at"]),
                "CWE" : CVE["cwe"]["cwe_id"] + " : " + CVE["content"], 
                "CVSS" : CVE["score"],
                "CVSS_CONTEXT" : ASSET["CVE_SERVER"]["environmental_score"],
                "EPSS" : CVE["epss"],
                "AFFECTED_TECHNOLOGIES" : ", ".join([update["current"]["product"] for update in ASSET["CVE_SERVER"]["updates"] if update and update["current"]]),
                "EXPLOIT_AVAILABLE" : "Oui" if CVE["exploitable"] else "Non",
                "EXPLOIT_LEVEL" : format_exploit_maturity(CVE["exploit_code_maturity"]),
                "CVE_PRIORITY" : "Oui" if ASSET["CVE_SERVER"]["prioritized"] else "Non",
                "DETECTED_AT" : format_date(ASSET["CVE_SERVER"]["detected_at"])
            })

    _SUMMARY_ARRAY.append({
        "GROUP" : GROUP,
        "TOTAL" : len(ASSETS),
        "UNMAINTAINED" : len([asset for asset in ASSETS if is_eol(asset)]),
        "UNPATCHED" : len(list(set([affected_asset["AFFECTED_ASSET_ID"] for affected_asset in _OLD_CVE_ARRAY])))
    })

print("[+] Building excels reports")
createExcel(_SUMMARY_ARRAY, _OLD_CVE_ARRAY)

if CONFIG["SMTP_SERVER"] == "" or CONFIG["SMTP_PORT"] == "":
    print("[-] No SMTP configuration found")
    sys.exit(1)

print("[+] Sending the email")
emailBody = createEmailBody(_SUMMARY_ARRAY, _OLD_CVE_ARRAY, CBW_URL = CONFIG["API_URL"])


send_mail(MAIL_SENDER, MAIL_RECEIVER.split(","), MAIL_SUBJECT, emailBody, ["Groups.xlsx", "Assets.xlsx"], CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"], CONFIG["SMTP_LOGIN"], CONFIG["SMTP_PASSWORD"])