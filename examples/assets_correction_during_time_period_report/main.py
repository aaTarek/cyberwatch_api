from cbw_helper import *
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--groups', "--G", dest="groups", type=str, nargs='+', required=True, help='Space separated group list')
parser.add_argument('--start', "--S", dest="start_date", type=lambda d: datetime.strptime(d, '%d/%m/%Y'), required=True, help='Starting date')
parser.add_argument('--end', "--E", dest="end_date", type=lambda d: datetime.strptime(d, '%d/%m/%Y').replace(minute=59, hour=23, second=59), default=datetime.now(), help='Ending date (included)')
parser.add_argument('--output', "--O", dest="pdf_name", type=str, default="result.pdf", help='PDF report name')
options = parser.parse_args() 

# Retrieving searched groups data
GROUPS = [group for group in retrieve_groups() if group["name"] in options.groups]

# Printing every group not found
if len(GROUPS) != len(options.groups):
    print("[-] Not every searched group has been found :")
    for group in options.groups:
        print("\t{} : {}".format(group, group in [group["name"] for group in GROUPS]))

# Retrieving every asset contained in any searched group
ASSETS = []
for group in GROUPS:
    ASSETS = ASSETS + [asset for asset in retrieve_assets(group) if asset["hostname"] not in [asset["hostname"] for asset in ASSETS]]

# This list a dict of every asset and its fixed CVEs during the time period
FIXES = []
print('')
for index, ASSET in enumerate(ASSETS):
    print("\033[A\033[A\n[+] {}/{} | Retrieving {}".format(index + 1, len(ASSETS), ASSET["hostname"]))
    ASSET = retrieve_asset(ASSET["id"])

    FIXED_CVES = [ CVE for CVE in ASSET["cve_announcements"] 
        if CVE["fixed_at"] 
        and compare_dates(date = datetime.strptime(CVE["fixed_at"], "%Y-%m-%dT%H:%M:%S.%f%z"), is_after = options.start_date)
        and not compare_dates(date = datetime.strptime(CVE["fixed_at"], "%Y-%m-%dT%H:%M:%S.%f%z"), is_after = options.end_date)
        ]
    
    FIXES.append({
        "ASSET" : ASSET,
        "FIXED_CVES" : FIXED_CVES
    })

# Generating PDF
print("[+] Generating report file")
if generate_pdf(options.start_date, options.end_date, FIXES, options.pdf_name):
    print("\033[A\033[A\n[+] Report has been successfully generated : {}".format(options.pdf_name))