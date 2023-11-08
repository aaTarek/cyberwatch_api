### This script retrieves every critical CVEs linked to 'linux_kernel' or any Windows KB update on every specified asset's group

1. Install all dependencies specified in `requirements.txt`.

2. Add the following blocks to `api.conf` and set SMTP variables to send mails:

```
[cyberwatch] # Configure Cyberwatch's API access
api_key = 
secret_key = 
url = 

[SMTP] # Configure SMTP 
server = 
port = 
login =
password =
```

3. Configure options in the headers of the `main.py` file.