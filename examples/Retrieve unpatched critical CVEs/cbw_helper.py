#!/usr/bin/env python
from cyberwatch_api import Cyberwatch_Pyhelper
from datetime import datetime, timezone, timedelta
import pandas as pd
import json
import csv
import io
from configparser import ConfigParser

def convert_date(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")

def older_than_2_months(date):
    try:
        return convert_date(date) < (datetime.now(timezone.utc) - timedelta(days=60))
    except Exception as e:
        return True

def format_date(d):
    try:
        date_object = convert_date(d)
        return date_object.strftime('%d/%m/%Y à %Hh%M')
    except Exception as e:
        return str(d)

def parseConfigurationFile():
    conf = ConfigParser()
    conf.read("api.conf")
    return {
        "API_URL" : conf.get("cyberwatch", "url"),
        "API_KEY" : conf.get("cyberwatch", "api_key"),
        "API_SECRET" : conf.get("cyberwatch", "secret_key"),
        "SMTP_SERVER" : conf.get("SMTP", "server") if conf.has_option("SMTP", "server") else "",
        "SMTP_PORT" : conf.get("SMTP", "port") if conf.has_option("SMTP", "port") else "",
        "SMTP_LOGIN" : conf.get("SMTP", "login") if conf.has_option("SMTP", "login") else "",
        "SMTP_PASSWORD" : conf.get("SMTP", "password") if conf.has_option("SMTP", "password") else "",
    }

def format_exploit_maturity(maturity):
    if maturity == "unproven":
        return "Non disponible"
    if maturity == "functional":
        return "Fonctionnel"
    if maturity == "proof_of_concept":
        return "Démonstration"
    if maturity == "high":
        return "Élevé"
    return maturity
        
def wprint(text):
    print(json.dumps(text, indent=4))

def retrieve_groups():
    groups = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/groups",
        verify_ssl=False,
    )
    print("Retrieving groups : 0")
    for page in apiResponse: 
        groups = groups + page.json()
        print("\033[A\033[A\nRetrieving groups : " + str(len(groups)))
    return groups

def retrieve_assets(GROUP):
    assets = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/vulnerabilities/servers",
        body_params={
            "group_id" : GROUP["id"]
        },
        verify_ssl=False,
    )
    print("[+] " + GROUP["name"] + " | Retrieving assets : 0")
    for page in apiResponse: 
        assets = assets + page.json()
        print("\033[A\033[A\n[+] " + (GROUP["name"] or "") + " | Retrieving assets : " + str(len(assets)))
    return assets

def retrieve_asset(id):
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/vulnerabilities/servers/" + str(id),
        verify_ssl=False
    )
    return next(apiResponse).json()

def retrieve_cves(GROUP = None, product = None, vendor = None, level = None):
    # Filtering parameters
    query_params = {"active" : True}
    if GROUP: query_params["groups"] = [GROUP["name"]]
    if product : query_params["technology_product"] = product
    if vendor : query_params["technology_vendor"] = vendor
    if level : query_params["level"] = level

    CVES = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/cve_announcements",
        body_params=query_params,
        verify_ssl=False,
    )
    print("Retrieving CVEs '" + (vendor or product or "") + "' : 0")
    for page in apiResponse: 
        CVES = CVES + page.json()
        print("\033[A\033[A\nRetrieving CVEs '" + (vendor or product or "") + "' : " + str(len(CVES)))
    return CVES

def retrieve_cve(CVE_CODE):
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/cve_announcements/" + str(CVE_CODE),
        verify_ssl=False
    )
    return next(apiResponse).json()

def is_eol(ASSET):
    if not ASSET["os"] or not ASSET["os"]["eol"]:
        return False
    eol = convert_date(ASSET["os"]["eol"])
    now = datetime.now()
    return True if eol < now else False

def createExcel(_SUMMARY_ARRAY, _OLD_CVE_ARRAY):

    # Generating the summary
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    for data in _SUMMARY_ARRAY:
        writer.writerow(["GROUPE", data["GROUP"]["name"]])
        writer.writerow(["TOTAL", data["TOTAL"]])
        writer.writerow(["Obsolète", data["UNMAINTAINED"]])
        writer.writerow(["Maintenus", data["TOTAL"] - data["UNMAINTAINED"]])
        writer.writerow(["Défaut de patch", data["UNPATCHED"]])
        writer.writerow(["", ""])

    csv_output.seek(0)
    data = pd.read_csv(csv_output)
    data.to_excel('Groups.xlsx', index=False, engine='xlsxwriter')

    # Generating the unpatched CVEs excel file
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    writer.writerow(["Vulnérabilité", "Actif affecté", "Groupes de l'actif affecté", "Dernière analyse de l'actif affecté", "CWE", "Score CVSS", "Score CVSS contextuel", "Score EPSS", "Technologies affectées", "Exploit public disponible", "Niveau de l'exploit", "Vulnérabilité prioritaire", "Date de détection"])
    for data in _OLD_CVE_ARRAY:
        writer.writerow([data["CVE_CODE"], data["AFFECTED_ASSET"], data["GROUPS"], data["LAST_ANALYZED"], data["CWE"], data["CVSS"], data["CVSS_CONTEXT"], data["EPSS"], data["AFFECTED_TECHNOLOGIES"], data["EXPLOIT_AVAILABLE"], data["EXPLOIT_LEVEL"], data["CVE_PRIORITY"], data["DETECTED_AT"]])

    csv_output.seek(0)
    data = pd.read_csv(csv_output)
    data.to_excel('Assets.xlsx', index=False, engine='xlsxwriter')