#!/usr/bin/env python

from cyberwatch_api import Cyberwatch_Pyhelper
from datetime import datetime
import requests
import pandas as pd
import json
import csv
import io
from configparser import ConfigParser
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def format_date(d):
    date_object = datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.%f%z')
    return date_object.strftime('%d/%m/%Y - %Hh%M')

def parseConfigurationFile():
    conf = ConfigParser()
    conf.read("api.conf")
    return {
        "API_URL" : conf.get("cyberwatch", "url"),
        "API_KEY" : conf.get("cyberwatch", "api_key"),
        "API_SECRET" : conf.get("cyberwatch", "secret_key"),
        "SMTP_SERVER" : conf.get("SMTP", "server"),
        "SMTP_PORT" : conf.get("SMTP", "port"),
        "SMTP_LOGIN" : conf.get("SMTP", "login"),
        "SMTP_PASSWORD" : conf.get("SMTP", "password"),
    }

def wprint(text):
    print(json.dumps(text, indent=4))

def retrieve_assets():
    assets = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/assets/servers",
        verify_ssl=False,
    )
    print("[+] Retrieving assets : 0")
    for page in apiResponse: 
        assets = assets + page.json()
        print("\033[A\033[A\n[+] Retrieving assets : " + str(len(assets)))
    return assets

def retrieve_asset(id):
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/assets/servers/" + str(id),
        verify_ssl=False
    )
    return next(apiResponse).json()

def createExcel(_SUMMARY_ASSETS):
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    writer.writerow(["ID", "Hostname", "Last communication"])
    for data in _SUMMARY_ASSETS:
        writer.writerow([data["ID"], data["HOSTNAME"], data["LAST_COMMUNICATION"]])

    csv_output.seek(0)
    data = pd.read_csv(csv_output)
    data.to_excel('Assets.xlsx', index=False, engine='xlsxwriter')