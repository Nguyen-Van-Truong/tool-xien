from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import string
import random
import re
from modules.TempMailClient import TempMailClient
from faker import Faker

BASE_URL = "https://ss2.sfcollege.edu/sr/AdmissionApplication/#/citizenship#top"
SELECTORS = {
    "us_citizen":             ("css", "label[for='us-citizen']"),
    "next_button":            ("xpath", "//button[normalize-space(text())='Next']"),
    "first_time_college":     ("css", "label[for='freshman']"),
    "no_diploma":             ("css", "label[for='no-diploma']"),

    "first_name":             ("css", "input#fstNameSTR"),
    "last_name":              ("css", "input#lstNameSTR"),
    "month":                  ("css", "select#month"),
    "day":                    ("css", "select#day"),
    "year":                   ("css", "select#year"),
    "email":                  ("css", "input#email"),
    "confirm_email":          ("css", "input#emailC"),
    "country_of_birth":       ("css", "select[name='birthctrySTR']"),
    "ssn":                    ("css", "input#ssn"),
    "confirm_ssn":            ("css", "input#ssnC"),
    "ssn_notice":             ("css", "input#ssnNoticeCB"),
    "verification_code":      ("css", "input#tokenInput"),
    "password":               ("css", "input#psdSTR"),
    "confirm_password":       ("css", "input#cpsdSTR"),
    "create_account":         ("css", "button#createAcctButton"),
    "student_id":             ("css", "strong.ng-binding"),
    "continue_app":           ("css", ".clearfix .button"),

    "country":                ("css", "select#country-select"),
    "street":                 ("css", "input#street-name"),
    "city":                   ("css", "input#city-name"),
    "state":                  ("css", "select#state-select"),
    "zipcode":                ("css", "input#zip-cd"),
    "county":                 ("css", "select#county"),

    "semester":               ("css", "select[name=firstTermCdSTR]"),
    "pronouns":               ("css", "select#pronouns"),
    "year_to_enter":          ("css", "select[name=firstYrNumSTR]"),
    "degree":                 ("css", "select#degreeSelect"),
    "english_primary":        ("css", "input#english-primary-yes"),
    "disciplinary_no":        ("css", "input#disciplinaryViolenceIndNo"),
    "education1":             ("css", "select[name=educationSelect1]"),
    "education2":             ("css", "select[name=educationSelect2]"),
    "military":               ("css", "select[name=statusSelect]"),
    "gender":                 ("css", "select#gender"),
    "ethnicity":              ("css", "select#ethnicity"),
    "agree_submit":           ("css", "button[ng-click='summaryNext()']"),
    "final_continue":         ("css", "button[ng-click='submitApplicationNext()']")

}

class Bot:
    def __init__(self, token, chromedriver: str ="driver/chromedriver.exe", wait_sec=2, timeout=30, headless_mode: bool=False):
        # Lưu các biến không thay đổi và cần dùng cho các hàm khác
        self.token = token
        self.chromedriver = chromedriver
        self.WAIT_SEC = wait_sec
        self.TIMEOUT = timeout
        self.headless_mode = headless_mode

    def _setup_driver(self):
        """Khởi tạo driver khi cần thiết"""
        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument("--start-maximized")
        opts.add_extension("driver/captchasolver.crx")
        opts.add_extension("driver/extract gg from pdf.crx")
        opts.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        if self.headless_mode:
            opts.add_argument('--headless')

        self.driver = webdriver.Chrome(service=Service(str(self.chromedriver)), options=opts)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        self.client = TempMailClient(self.token)

    def _loc(self, key):
        by, sel = SELECTORS[key]
        return (By.CSS_SELECTOR, sel) if by == "css" else (By.XPATH, sel)

    def click(self, key):
        el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        el.click()
        time.sleep(self.WAIT_SEC)

    def type(self, key, txt):
        el = self.wait.until(EC.element_to_be_clickable(self._loc(key)))
        el.clear()
        el.send_keys(txt)
        time.sleep(self.WAIT_SEC)

    def select(self, key, *, by_value=None, by_text=None, by_index=None, timeout=None):
        if not timeout:
            timeout = self.TIMEOUT

        el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(self._loc(key)))
        sel = Select(el)
        time.sleep(self.WAIT_SEC)
        if by_value is not None:
            sel.select_by_value(by_value)
        elif by_text is not None:
            sel.select_by_visible_text(by_text)
        elif by_index is not None:
            sel.select_by_index(by_index)

    def fake_profile(self):
        f = Faker()
        dob = f.date_of_birth(minimum_age=18, maximum_age=30)
        return {
            "first_name": f.first_name(),
            "last_name":  f.last_name(),
            "gender":     f.random_element(["Male", "Female"]),
            "birthdate":  dob,
            "ssn":        f.ssn(),
            "street":     f.street_address(),
            "city":       f.city(),
            "state":      f.state(),
            "zip":        f.zipcode()
        }

    def generate_username(self, length=9):
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def generate_password(self, username="", length=12):
        if length < 8:
            raise ValueError("Password must be ≥ 8 chars")
        pools = {
            "upper": random.choice(string.ascii_uppercase),
            "lower": random.choice(string.ascii_lowercase),
            "digit": random.choice(string.digits),
            "spec":  random.choice("~!@#$%&*")
        }
        pwd = list(pools.values())
        extra = random.choices("".join(pools.values()), k=length - len(pwd))
        pwd += extra
        random.shuffle(pwd)
        s = "".join(pwd)
        return s if username.lower() not in s.lower() else self.generate_password(username, length)

    def create_email(self, user, tries=5):
        for _ in range(tries):
            j = self.client.create_temp_email(user)
            if j:
                return j
        return {}

    def read_message(self, msg_id, tries=5):
        for _ in range(tries):
            j = self.client.read_message(msg_id)
            body = j.get("body")
            if body:
                return body
            time.sleep(5)
        return ""

    def extract_code(self, html):
        m = re.search(r'<strong>(\d+)</strong>', html)
        return m.group(1) if m else ""

    def run(self, profile=None):
        # Khởi tạo driver khi bắt đầu chạy
        self._setup_driver()
        drv = self.driver
        drv.get(BASE_URL)

        profile = self.fake_profile() if not profile else profile
        email_info = self.create_email(self.generate_username())
        
        if not email_info:
            return None
        
        email = email_info["email"]
        mail_id = email_info["id"]

        # --- Citizenship ---
        for step in ("us_citizen","next_button","first_time_college","next_button","no_diploma","next_button"):
            self.click(step)

        # --- Personal Info ---
        self.type("first_name", profile["first_name"])
        self.type("last_name",  profile["last_name"])
        self.select("pronouns", by_index=1)
        self.select("month",   by_text=profile["birthdate"].strftime("%b"))
        self.select("day",     by_text=profile["birthdate"].strftime("%d"))
        self.select("year",    by_text=str(profile["birthdate"].year))
        self.type("email",         email)
        self.type("confirm_email", email)
        self.select("country_of_birth", by_value="045")
        self.type("ssn",         profile["ssn"])
        self.type("confirm_ssn", profile["ssn"])
        self.click("ssn_notice")
        self.click("next_button")

        # --- Email Verification ---
        self.wait.until(EC.visibility_of_element_located(self._loc("verification_code")))
        msg_id = self.client.get_message_by_match(mail_id, by_sender="no-reply@sfcollege.edu", by_subject="Application Code")
        code = self.extract_code(self.read_message(msg_id))

        self.type("verification_code", code)
        self.click("next_button")

        # --- Account Setup ---
        pwd = self.generate_password(profile["first_name"])
        self.type("password",        pwd)
        self.type("confirm_password",pwd)
        self.click("next_button")
        self.click("create_account")

        # --- Capture Student ID & Continue ---
        sid = self.wait.until(
            EC.visibility_of_element_located(self._loc("student_id"))
        ).text
        self.click("continue_app")

        # --- Address ---
        self.select("country", by_text="United States Of America")
        self.type("street",  profile["street"])
        self.type("city",    profile["city"])
        try:
            self.select("state", by_text=profile["state"])
        except:
            self.select("state", by_index=1)
        self.type("zipcode", profile["zip"])

        try:
            self.select("county", by_index=1, timeout=5)
        except: pass

        for _ in range(5):
            self.click("next_button")

        # --- Academic & Final ---
        sem_sel = self.driver.find_element(By.NAME, "firstTermCdSTR")
        sem_sel.click()
# xuống extract gg from pdf lần tới “Fall”
        sem_sel.send_keys(Keys.ARROW_DOWN)
        sem_sel.send_keys(Keys.ENTER)

        yr_sel = self.driver.find_element(By.NAME, "firstYrNumSTR")
        yr_sel.click()
# xuống extract gg from pdf lần tới “2025”
        yr_sel.send_keys(Keys.ARROW_DOWN)
        yr_sel.send_keys(Keys.ENTER)
        self.click("next_button")
        self.select("degree", by_value="ABE")
        self.click("next_button")
        self.click("english_primary")
        self.click("next_button")

        self.click("disciplinary_no")
        drv.execute_script("document.querySelectorAll('button.button.float-right')[extract gg from pdf].click()")
        
        self.select("education1", by_value="X")
        self.select("education2", by_value="X")
        self.click("next_button")

        
        self.select("military", by_value="Y")
        self.click("next_button")

        self.select("gender", by_text=profile["gender"])
        self.select("ethnicity", by_value="X")
        self.click("next_button")

        self.click("agree_submit")
        # self.click("final_continue")
        
        result = {
            "Email":        email,
            "Student ID":   sid,
            "Password":     pwd,
            "Full Name":    f"{profile['first_name']} {profile['last_name']}",
            "Gender":       profile['gender'],
            "Birthdate":    profile['birthdate'].strftime("%Y-%m-%d"),
            "Street":       profile['street'],
            "City":         profile['city'],
            "State":        profile['state'],
            "Zipcode":      profile['zip'],
            "SSN":          profile['ssn'],
            "Password changed": "n"
        }

        drv.quit()
        return result

    def exit(self):
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
