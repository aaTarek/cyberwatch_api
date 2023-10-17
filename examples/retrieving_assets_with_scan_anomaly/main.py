#!/usr/bin/env python

import requests
from cbw_helper import *
from cbw_mail import *
import sys
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# This script will gather every assets without any packages returned, meaning 
# there was some issues during scanning

############################################################
# CONFIGURATION - USE THIS SECTION TO CONFIGURE SCRIPT
############################################################

# Add the following block to api.conf and use it to set the SMTP variables:
#
# [SMTP]
# server =
# port = 
# login =
# password =

# MAIL PARAMETERS

MAIL_SENDER = ""
MAIL_RECEIVER = ""
MAIL_SUBJECT = "Cyberwatch - Report of assets with scanning issues"

############################################################

CONFIG = parseConfigurationFile()
ASSETS = retrieve_assets()
_SUMMARY_ASSETS = []

print("")
for counter, ASSET_INDEX in enumerate(ASSETS):
    try:
        print("\033[A\033[A\n[+] ID : {} | Retrieving asset : {}/{}".format(str(ASSET_INDEX["id"]), str(counter), str(len(ASSETS))))
        ASSET = retrieve_asset(ASSET_INDEX["id"])
    except Exception as e:
        sys.stderr.write("[-] ID {} | An error occured : {}\n\n".format(str(ASSET_INDEX["id"]), str(e)))
        continue

    if len(ASSET["packages"]) == 0:
        _SUMMARY_ASSETS.append({
            "ID" : ASSET["id"],
            "HOSTNAME" : ASSET["hostname"],
            "LAST_COMMUNICATION" : format_date(ASSET["last_communication"])
        })

print("[+] Generating Excel report")
createExcel(_SUMMARY_ASSETS)

if CONFIG["SMTP_SERVER"] == "" or CONFIG["SMTP_LOGIN"] == "" or CONFIG["SMTP_PASSWORD"] == "":
    print("[-] No SMTP configuration found in api.conf")
    sys.exit(1)

print("[+] Generating and sending the report email")
emailBody = createEmailBody(_SUMMARY_ASSETS, CBW_URL = CONFIG["API_URL"])
send_mail(MAIL_SENDER, MAIL_RECEIVER.split(","), MAIL_SUBJECT, emailBody, ["Assets.xlsx"], CONFIG["SMTP_SERVER"], CONFIG["SMTP_PORT"], CONFIG["SMTP_LOGIN"], CONFIG["SMTP_PASSWORD"])