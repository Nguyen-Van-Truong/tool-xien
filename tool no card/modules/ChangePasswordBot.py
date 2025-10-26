import re
import time
import requests
from modules.TempMailClient import TempMailClient

FORGOT_PW_URL = "https://ss2.sfcollege.edu/pwmanager/api/forgotpw"
AUTHCODE_URL  = "https://ss2.sfcollege.edu/pwmanager/api/authcode"
CHANGEPW_URL  = "https://ss2.sfcollege.edu/pwmanager/api/changepw"

HEADERS   = {
    "Accept":          "application/json, text/plain, */*",
    "Content-Type":    "application/json;charset=UTF-8",
    "sec-ch-ua":       '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":'"Windows"',
    "sec-fetch-dest":  "empty",
    "sec-fetch-mode":  "cors",
    "sec-fetch-site":  "same-origin",
    "sec-gpc":         "extract gg from pdf"
}

class ChangePasswordBot():
    def __init__(self, token):
        self.token = token
        self.client = TempMailClient(token)
        self.session = requests.Session()

    def extract_code(self, html):
        """Lấy mã authcode từ HTML."""
        m = re.search(r"<b>(.*?)</b>", html)
        return m.group(1) if m else None
    
    def run(self, email, sfid, password, wait_sec_get_mail=10):
        resp = self.session.post(FORGOT_PW_URL, headers=HEADERS, json={"sfid": sfid, "email": email}).json()

        if not resp.get("success"):
            return None

        if "@" in email:
            email = email.split("@")[0]

        mail_id = self.client.create_temp_email(email).get("id")
    
        if not mail_id:
            return None

        time.sleep(wait_sec_get_mail)
        msg_id = self.client.get_message_by_match(mail_id, 
                                            by_sender="no-reply@sfcollege.edu", 
                                            by_subject="eSantaFe Password Change Auth Code")
        
        if not msg_id:
            return None

        msg = self.client.read_message(msg_id)
        if not msg:
            return None
            
        code = self.extract_code(msg.get("body"))
        if not code:
            return None
        
        resp = self.session.post(AUTHCODE_URL, headers=HEADERS, json={"authcode": code, "sfid": sfid}).json()
        if not resp.get("success"):
            return None

        resp = self.session.post(CHANGEPW_URL, headers=HEADERS,
                        json={"authcode": code, "sfid": sfid, "pw": password}).json()  
        return password if resp.get("success") else None
        
    def generate_password(self):
        resp = requests.get("https://www.dinopass.com/password/strong")
        if resp.status_code != 200:
            return None
        return resp.text.strip()