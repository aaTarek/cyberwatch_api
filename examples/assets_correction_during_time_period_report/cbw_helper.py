from cyberwatch_api import Cyberwatch_Pyhelper
from datetime import datetime
import requests
from fpdf import FPDF
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def compare_dates(**kwargs):
    try:
        if not kwargs["date"] and not kwargs["is_after"]:
            raise Exception("custom function compare_dates need 'date' and 'is_before' argument")
        
        date = kwargs["date"]
        is_after = kwargs["is_after"]
        return date.replace(tzinfo=None) > is_after.replace(tzinfo=None)
    except Exception as e:
        return False

def print_date(date, hour = False):
    try:
        if hour:
            return date.strftime('%d/%m/%Y à %Hh%M')
        return date.strftime('%d/%m/%Y')
    except Exception as e:
        return "Undefined"

def retrieve_groups():
    """retrieve all groups for a cyberwatch node"""
    groups = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/groups",
        verify_ssl=False
    )
    print("Retrieving groups : 0")
    for page in apiResponse: 
        groups = groups + page.json()
        print("\033[A\033[A\nRetrieving groups : " + str(len(groups)))
    return groups

def retrieve_assets(group):
    """retrieve all assets for a cyberwatch node"""
    assets = []
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/assets/servers",
        verify_ssl=False,
        body_params={
            'group_id' : group["id"]
        }
    )
    print("{} | Retrieving assets : 0".format(group["name"]))
    for page in apiResponse: 
        assets = assets + page.json()
        print("\033[A\033[A\n{} | Retrieving assets : ".format(group["name"]) + str(len(assets)))
    return assets

def retrieve_asset(assetID):
    """retrieve a specific asset for a cyberwatch node"""
    apiResponse = Cyberwatch_Pyhelper().request(
        method="GET",
        endpoint="/api/v3/vulnerabilities/servers/" + str(assetID),
        verify_ssl=False
    )
    return next(apiResponse).json()


##################
# PDF GENERATION #
##################


SCORE_CRITICAL = 9
SCORE_HIGH = 7
SCORE_MEDIUM = 4
SCORE_LOW = 0

class PDF(FPDF):
    def __init__(self, start_date, end_date):
        super().__init__()
        self.sepHeight = 5
        self.start_date = start_date
        self.end_date = end_date

    def header(self):
        self.set_font('Arial', 'B', 10)
        if self.page_no() != 1:
            self.image('cyberwatch.jpg', 10, 10, 40)
            self.set_font('Arial', 'B', 10)
            self.cell(0, 5, "Vulnérabilités corrigées du {} au {} inclus".format(print_date(self.start_date), print_date(self.end_date)), 'R', 1, 'R')
            self.ln(20)

    def footer(self):
        self.set_font('Arial', 'B', 10)
        if self.page_no() != 1:
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def titlee(self, ELEMENT):
        self.ln(self.sepHeight * 2)
        self.set_font('Arial', 'B', 12)
        self.write(10, ELEMENT["ASSET"]["hostname"])
        self.set_font('Arial', '', 10)
        self.write(10, " - {} vulnérabilités corrigées".format(len(ELEMENT["FIXED_CVES"])))
        self.set_text_color(255,0,0)
        self.write(10, " {} ".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] >= 9])))
        self.set_text_color(253, 165, 15)
        self.write(10, " {} ".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] >= 5])))
        self.set_text_color(0,255,0)
        self.write(10, " {} ".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] < 5])))
        self.ln(self.sepHeight)

    def COLOR_RESET(self, textWhite=False):
        if textWhite:
            self.set_text_color(255, 255, 255)
        else:
            self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)

    def COLOR_CRITICAL(self, colorText=False):
        if colorText == False:
            self.set_text_color(255, 255, 255)
        else:
            self.set_text_color(186, 15, 38)
        self.set_fill_color(186, 15, 38)

    def COLOR_HIGH(self, colorText=False):
        if colorText == False:
            self.set_text_color(0, 0, 0)
        else:
            self.set_text_color(254, 87, 22)
        self.set_fill_color(254, 87, 22)

    def COLOR_MEDIUM(self, colorText=False):
        if colorText == False:
            self.set_text_color(0, 0, 0)
        else:
            self.set_text_color(255, 134, 29)
        self.set_fill_color(255, 134, 29)

    def COLOR_LOW(self, colorText=False):
        if colorText == False:
            self.set_text_color(0, 0, 0)
        else:
            self.set_text_color(255, 178, 16)
        self.set_fill_color(255, 178, 16)
    
    def CVE(self, CVE):
        self.set_text_color(0,0,0)
        self.set_font('Arial', 'B', 8)
        self.write(8, "{} ".format(CVE["cve_code"]), "https://nvd.nist.gov/vuln/detail/" + str(CVE["cve_code"]))
        if not CVE["score"]:
            self.COLOR_RESET()
        elif CVE["score"] >= SCORE_CRITICAL:
            self.COLOR_CRITICAL(colorText=True)
        elif CVE["score"] >= SCORE_HIGH:
            self.COLOR_HIGH(colorText=True)
        elif CVE["score"] >= SCORE_MEDIUM:
            self.COLOR_MEDIUM(colorText=True)
        else:
            self.COLOR_LOW(colorText=True)
        self.write(8, "{}  ".format(CVE["score"]), )
        self.set_font('Arial', '', 7)
        self.set_text_color(128,128,128)
        self.write(8, "- {}      ".format(datetime.strptime(CVE["fixed_at"], "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%d/%m/%Y à %H:%M')))
        self.set_text_color(0,0,0)

    def table(self, header, data):
        col_widths = (200 - 10) / len(header)
        for i in range(len(header)):
            self.cell(col_widths, 8, header[i], 1)
        self.ln()
        # Données
        for row in data:
            for i in range(len(header)):
                self.cell(col_widths, 8, str(row[i]), 1)
            self.ln()

def generate_pdf(start_date, end_date, FIXES, pdf_name):
    pdf = PDF(start_date, end_date)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Cover page
    pdf.COLOR_RESET(textWhite=True)
    pdf.set_fill_color(16, 54, 122)
    pdf.image('cyberwatch.jpg', 50, 20, 100)
    pdf.rect(30, 50, 140, 200, 'F')
    pdf.set_y(60)
    pdf.set_x(40)
    # Cyberwatch - Rapport
    pdf.set_font('Arial', '', 10)
    pdf.write(10, "Cyberwatch - Rapport")
    pdf.ln(12)
    pdf.set_x(40)
    # Titre
    pdf.set_font('Arial', 'B', 20)
    pdf.write(10, "Vulnérabilités corrigées")
    pdf.ln(10)
    pdf.set_x(40)
    pdf.write(10, "du {}".format(print_date(start_date)))
    pdf.ln(10)
    pdf.set_x(40)
    pdf.write(10, "au {}".format(print_date(end_date)))
    # Date
    pdf.set_font('Arial', '', 12)
    pdf.write(10, " - {} actifs".format(len(FIXES)))
    # Date
    pdf.ln(10)
    pdf.set_x(40)
    pdf.set_font('Arial', '', 8)
    pdf.write(10, "Rapport généré le : {}".format(print_date(datetime.now(), hour=True)))
    # Disclaimer
    pdf.ln(10)
    pdf.set_y(220)
    pdf.set_x(40)
    pdf.set_font('Arial', 'I', 8)
    pdf.write(10, "Attention : ce document est strictement confidentiel et établi à l'intention exclusive de ses")
    pdf.ln(5)
    pdf.set_x(40)
    pdf.write(10, "destinataires. Toute utilisation ou diffusion non autorisée, même partielle, est interdite et")
    pdf.ln(5)
    pdf.set_x(40)
    pdf.write(10, "passible de poursuites.")
    pdf.COLOR_RESET()

    pdf.add_page()

    for ELEMENT in FIXES:
        # Asset Title
        # pdf.ln(pdf.sepHeight * 2)
        pdf.set_font('Arial', 'B', 12)
        pdf.write(10, ELEMENT["ASSET"]["hostname"])
        pdf.set_font('Arial', '', 8)
        pdf.write(10, "{}".format(" | " + ELEMENT["ASSET"]["os"]["name"] if ELEMENT["ASSET"]["os"] else ""))
        pdf.cell(0, 10, "{} vulnérabilités restantes".format(ELEMENT["ASSET"]["cve_announcements_count"]), 0, 0, 'R')
        pdf.ln()
        pdf.ln(3)

        # CVE Summary Array
        pdf.set_font('Arial', 'B', 8)
        pdf.COLOR_RESET()
        pdf.cell(38, 7, "Vulnérabilités corrigées", 1, 0, 'C', True)
        pdf.COLOR_LOW()
        pdf.cell(38, 7, "Faible", 1, 0, 'C', True)
        pdf.COLOR_MEDIUM()
        pdf.cell(38, 7, "Moyenne", 1, 0, 'C', True)
        pdf.COLOR_HIGH()
        pdf.cell(38, 7, "Élevée", 1, 0, 'C', True)
        pdf.COLOR_CRITICAL()
        pdf.cell(38, 7, "Critique", 1, 0, 'C', True)
        pdf.COLOR_RESET()
        pdf.ln()
        pdf.cell(38, 7, "{}".format(len(ELEMENT["FIXED_CVES"] )), 1, 0, 'C')
        pdf.cell(38, 7, "{}".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] < SCORE_MEDIUM ])), 1, 0, 'C')
        pdf.cell(38, 7, "{}".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] >= SCORE_MEDIUM and CVE["score"] < SCORE_HIGH ])), 1, 0, 'C')
        pdf.cell(38, 7, "{}".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] >= SCORE_HIGH and CVE["score"] < SCORE_CRITICAL])), 1, 0, 'C')
        pdf.cell(38, 7, "{}".format(len([CVE for CVE in ELEMENT["FIXED_CVES"] if CVE["score"] and CVE["score"] >= SCORE_CRITICAL])), 1, 0, 'C')
        pdf.ln()
        
        for index, CVE in enumerate(sorted(ELEMENT["FIXED_CVES"], key=lambda d: d['score'] if d['score'] else 0, reverse=True)) :
            if index % 3 == 0: pdf.ln(5)
            pdf.CVE(CVE) 
        
        pdf.ln()
        pdf.ln(3)

    pdf.output(pdf_name, 'F')
    return True