import requests
from typing import Union, List
import time

class TempMailClient:
    def __init__(self, token: str):
        # Lưu token đúng cách
        self.token = token
        self.base_url = "https://tempmail.id.vn/api"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_temp_email(self, user: str, domain: str = "mail.accngon.io.vn") -> dict:
        payload = {"user": user, "domain": domain}

        resp = requests.post(f"{self.base_url}/email/create",
                             headers=self.headers,
                             json=payload,
                             timeout=60)
        try:
            data = resp.json()
        except ValueError:
            return {}

        if d := data.get("data"):
            return d
        return {}

    def get_message_list(self, mail_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/email/{mail_id}",
                            headers=self.headers,
                            timeout=60)
        try:
            data = resp.json()
        except ValueError:
            return {}
        
        return data.get("data")

    def read_message(self, message_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/message/{message_id}",
                            headers=self.headers,
                            timeout=60)
        try:
            data = resp.json()
        except ValueError:
            return {}
        try:
            return data["data"]
        except KeyError:
            return None

    def get_message_by_match(
        self,
        email_id: str,
        by_sender: Union[str, List[str]] = None,
        by_subject: Union[str, List[str]] = None,
        by_sender_name: Union[str, List[str]] = None,
        tries: int = 5,
        delay: int = 5
    ) -> dict:
        def _matches(field_value: str, criteria: Union[str, List[str]]) -> bool:
            if criteria is None:
                return True
            if isinstance(criteria, (list, tuple)):
                return any(c in field_value for c in criteria)
            return criteria in field_value

        for attempt in range(1, tries + 1):
            data = self.get_message_list(email_id)
            
            if data == []:
                continue
            
            messages = data.get("items")

            for msg in messages:
                sender       = msg.get("from", "")
                subject      = msg.get("subject", "")
                sender_name  = msg.get("from_name") or msg.get("senderName") or ""

                if not _matches(sender, by_sender):
                    continue
                if not _matches(subject, by_subject):
                    continue
                if not _matches(sender_name, by_sender_name):
                    continue

                return msg.get("id")

            time.sleep(delay)
        return {}