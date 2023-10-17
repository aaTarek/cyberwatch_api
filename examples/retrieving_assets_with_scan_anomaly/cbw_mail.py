import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.utils import COMMASPACE, formatdate


def send_mail(send_from, send_to, subject, message, files=[], server="localhost", port=587, username='', password='', use_tls=True):

    mail = MIMEMultipart()
    mail['From'] = send_from
    mail['To'] = COMMASPACE.join(send_to)
    mail['Date'] = formatdate(localtime=True)
    mail['Subject'] = subject

    mail.attach(MIMEText(message, "html"))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        mail.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, mail.as_string())
    smtp.quit()

def createEmailBody(_SUMMARY_ASSETS, CBW_URL = None):
    body = """
    <!doctype html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f8f8f8;
                padding: 20px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #dddddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #FF5602;
                color: white;
            }
            h2 {
                color: #FF5602;
            }
            header{
                width:100%;
                display:flex !important;
                flex-direction:column !important;
                gap:30px !important;
                justify-content:center !important;
                align-items:center;
                margin-bottom:20px;
            }
        </style>
    </head>
    <body>
    <header>
    <img src="data:image/jpeg;base64,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"/>
    <h2>Rapport Cyberwatch</h2>
    </header><br/>
    """
    # Tableau des CVEs non patchées depuis plus de deux mois

    body += """
        <h3>""" + str(len(_SUMMARY_ASSETS)) + """ assets with scanning issues found</h3>
        <table>
            <tr>
                <th><b>ID</b></th>
                <th><b>Hostname</b></th>
                <th><b>Last communication</b></th>
            </tr>
    """

    for data in _SUMMARY_ASSETS:
        body += """
            <tr>
                <td><a href="{}/servers/{}">{}</a></td>
                <td><a href="{}/servers/{}#server_analysis_scripts">{}</a></td>
                <td>{}</td>
            </tr>
        """.format(
            CBW_URL,
            str(data["ID"]),
            str(data["ID"]),
            CBW_URL,
            str(data["ID"]),
            str(data["HOSTNAME"]),
            str(data["LAST_COMMUNICATION"]),
        )

    body += "</table>"

    body += """
    </body>
    </html>
    """

    return body