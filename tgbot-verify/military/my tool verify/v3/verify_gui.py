#!/usr/bin/env python3
"""
🎖️ Military Verification GUI Tool V3
Auto-get SheerID link từ ChatGPT API và auto-retry
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import httpx
import json
import re
import os
import threading
from datetime import datetime

# ===================== CONFIG =====================
SHEERID_BASE_URL = "https://services.sheerid.com/rest/v2/verification"
CHATGPT_API_URL = "https://chatgpt.com/backend-api/veterans/create_verification"
DATA_FILE = "all_veterans.txt"
CONFIG_FILE = "config.json"

# Default config
DEFAULT_CONFIG = {
    "bearer_token": "",
    "oai_device_id": "b0f9c294-745d-434a-bf42-71d8116ebc1b",
    "max_retries": 10,  # Maximum failed attempts per veteran
    "cookies": ""
}

ORGANIZATIONS = {
    "Army": {"id": 4070, "name": "Army"},
    "Navy": {"id": 4072, "name": "Navy"},
    "Air Force": {"id": 4073, "name": "Air Force"},
    "Marine Corps": {"id": 4071, "name": "Marine Corps"},
    "Coast Guard": {"id": 4074, "name": "Coast Guard"},
}

MONTH_TO_NUM = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
}

# ===================== FUNCTIONS =====================

def load_config():
    """Load config from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Merge with defaults
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save config to file"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_veterans():
    """Load veterans from file"""
    veterans = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    veterans.append(line)
    return veterans


def save_veterans(veterans):
    """Save veterans to file"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(veterans))


def parse_veteran(line):
    """Parse veteran line to dict"""
    parts = line.split("|")
    if len(parts) < 10:
        return None
    return {
        "firstName": parts[0],
        "lastName": parts[1],
        "branch": parts[2],
        "birthMonth": parts[3],
        "birthDay": parts[4],
        "birthYear": parts[5],
        "dischargeMonth": parts[6],
        "dischargeDay": parts[7],
        "dischargeYear": parts[8],
        "email": parts[9]
    }


def format_date(year, month, day):
    """Format to YYYY-MM-DD"""
    month_num = MONTH_TO_NUM.get(month, "01")
    return f"{year}-{month_num.zfill(2)}-{day.zfill(2)}"


def extract_verification_id(url_or_data):
    """Extract verificationId from URL or API response"""
    # Try URL format
    match = re.search(r'verificationId=([a-f0-9]+)', str(url_or_data))
    if match:
        return match.group(1)
    # Try JSON response format
    if isinstance(url_or_data, dict):
        return url_or_data.get("verificationId") or url_or_data.get("verification_id")
    return None


# ===================== GUI CLASS =====================

class MilitaryVerifyAppV3:
    def __init__(self, root):
        self.root = root
        self.root.title("🎖️ Military Verification Tool V3 - Auto Mode")
        self.root.geometry("900x800")
        self.root.configure(bg="#1a1a2e")
        
        # Load data
        self.config = load_config()
        self.veterans = load_veterans()
        self.current_index = 0
        self.is_running = False
        self.retry_count = 0
        
        self.setup_ui()
        self.update_veteran_display()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root, 
            text="🎖️ MILITARY VERIFICATION TOOL V3",
            font=("Arial", 18, "bold"),
            fg="#00ff88",
            bg="#1a1a2e"
        )
        title.pack(pady=10)
        
        subtitle = tk.Label(
            self.root, 
            text="🔄 Auto-Get Link & Auto-Retry Mode",
            font=("Arial", 11),
            fg="#ffaa00",
            bg="#1a1a2e"
        )
        subtitle.pack()
        
        # Stats Frame
        stats_frame = tk.Frame(self.root, bg="#1a1a2e")
        stats_frame.pack(fill="x", padx=20)
        
        self.stats_label = tk.Label(
            stats_frame,
            text=f"📊 Veterans: {len(self.veterans)}",
            font=("Arial", 12),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.stats_label.pack(side="left")
        
        # === CONFIG SECTION ===
        config_frame = tk.LabelFrame(
            self.root, 
            text="⚙️ Configuration",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e",
            padx=10, pady=10
        )
        config_frame.pack(fill="x", padx=20, pady=10)
        
        # Bearer Token
        tk.Label(config_frame, text="🔑 Bearer Token:", fg="white", bg="#16213e").grid(row=0, column=0, sticky="w")
        self.token_entry = tk.Entry(config_frame, width=80, font=("Arial", 9), show="*")
        self.token_entry.grid(row=0, column=1, pady=5, padx=5)
        self.token_entry.insert(0, self.config.get("bearer_token", ""))
        
        # Show/Hide token
        tk.Button(config_frame, text="👁", command=self.toggle_token, width=3).grid(row=0, column=2)
        
        # Device ID
        tk.Label(config_frame, text="📱 Device ID:", fg="white", bg="#16213e").grid(row=1, column=0, sticky="w")
        self.device_entry = tk.Entry(config_frame, width=80, font=("Arial", 9))
        self.device_entry.grid(row=1, column=1, pady=5, padx=5)
        self.device_entry.insert(0, self.config.get("oai_device_id", ""))
        
        # Email
        tk.Label(config_frame, text="📧 Email:", fg="white", bg="#16213e").grid(row=2, column=0, sticky="w")
        self.email_entry = tk.Entry(config_frame, width=80, font=("Arial", 9))
        self.email_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # Max Retries
        tk.Label(config_frame, text="🔄 Max Retries:", fg="white", bg="#16213e").grid(row=3, column=0, sticky="w")
        self.retry_spinbox = tk.Spinbox(config_frame, from_=1, to=50, width=10, font=("Arial", 10))
        self.retry_spinbox.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        self.retry_spinbox.delete(0, tk.END)
        self.retry_spinbox.insert(0, self.config.get("max_retries", 10))
        
        # Save config button
        tk.Button(config_frame, text="💾 Save Config", command=self.save_config_ui, bg="#3366ff", fg="white").grid(row=3, column=2)
        
        # Cookies (new row)
        tk.Label(config_frame, text="🍪 Cookies:", fg="white", bg="#16213e").grid(row=4, column=0, sticky="nw")
        self.cookies_text = tk.Text(config_frame, width=80, height=3, font=("Arial", 8))
        self.cookies_text.grid(row=4, column=1, pady=5, padx=5)
        self.cookies_text.insert("1.0", self.config.get("cookies", ""))
        
        # === VETERAN INFO SECTION ===
        vet_frame = tk.LabelFrame(
            self.root,
            text="👤 Current Veteran",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e",
            padx=10, pady=10
        )
        vet_frame.pack(fill="x", padx=20, pady=10)
        
        # Veteran Info Labels
        self.vet_name_label = tk.Label(vet_frame, text="Name: ---", fg="white", bg="#16213e", font=("Arial", 11))
        self.vet_name_label.pack(anchor="w")
        
        self.vet_branch_label = tk.Label(vet_frame, text="Branch: ---", fg="cyan", bg="#16213e", font=("Arial", 11))
        self.vet_branch_label.pack(anchor="w")
        
        self.vet_birth_label = tk.Label(vet_frame, text="Birth: ---", fg="white", bg="#16213e", font=("Arial", 11))
        self.vet_birth_label.pack(anchor="w")
        
        self.vet_discharge_label = tk.Label(vet_frame, text="Discharge: ---", fg="white", bg="#16213e", font=("Arial", 11))
        self.vet_discharge_label.pack(anchor="w")
        
        self.retry_label = tk.Label(vet_frame, text="Retries: 0/10", fg="#ffaa00", bg="#16213e", font=("Arial", 11))
        self.retry_label.pack(anchor="w")
        
        # Navigation buttons
        nav_frame = tk.Frame(vet_frame, bg="#16213e")
        nav_frame.pack(fill="x", pady=10)
        
        tk.Button(nav_frame, text="⏮ Prev", command=self.prev_veteran, bg="#444", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Next ⏭", command=self.next_veteran, bg="#444", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(nav_frame, text="🗑 Remove & Next", command=self.remove_and_next, bg="#ff4444", fg="white", width=15).pack(side="left", padx=5)
        
        # === ACTION BUTTONS ===
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=15)
        
        self.auto_btn = tk.Button(
            btn_frame,
            text="🚀 START AUTO VERIFY",
            command=self.toggle_auto_verify,
            font=("Arial", 14, "bold"),
            bg="#00cc66",
            fg="white",
            width=22,
            height=2
        )
        self.auto_btn.pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="🔗 Test Get Link",
            command=self.test_get_link,
            font=("Arial", 11),
            bg="#ff9900",
            fg="white",
            width=15
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Reload",
            command=self.reload_data,
            font=("Arial", 11),
            bg="#3366ff",
            fg="white",
            width=10
        ).pack(side="left", padx=10)
        
        # === LOG SECTION ===
        log_frame = tk.LabelFrame(
            self.root,
            text="📋 Log",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e"
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Consolas", 10),
            bg="#0a0a1a",
            fg="#00ff88"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready - Configure Bearer Token and Email to start",
            fg="#888",
            bg="#1a1a2e",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20)
    
    def toggle_token(self):
        """Toggle token visibility"""
        if self.token_entry.cget("show") == "*":
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")
    
    def save_config_ui(self):
        """Save config from UI"""
        self.config["bearer_token"] = self.token_entry.get().strip()
        self.config["oai_device_id"] = self.device_entry.get().strip()
        self.config["max_retries"] = int(self.retry_spinbox.get())
        self.config["cookies"] = self.cookies_text.get("1.0", tk.END).strip()
        save_config(self.config)
        self.log("💾 Config saved!")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_veteran_display(self):
        """Update current veteran display"""
        max_retries = int(self.retry_spinbox.get())
        
        if not self.veterans:
            self.vet_name_label.config(text="Name: NO DATA")
            self.vet_branch_label.config(text="Branch: ---")
            self.vet_birth_label.config(text="Birth: ---")
            self.vet_discharge_label.config(text="Discharge: ---")
            return
        
        if self.current_index >= len(self.veterans):
            self.current_index = 0
        
        line = self.veterans[self.current_index]
        vet = parse_veteran(line)
        
        if vet:
            self.vet_name_label.config(text=f"Name: {vet['firstName']} {vet['lastName']}")
            self.vet_branch_label.config(text=f"Branch: {vet['branch']}")
            self.vet_birth_label.config(text=f"Birth: {vet['birthMonth']} {vet['birthDay']}, {vet['birthYear']}")
            self.vet_discharge_label.config(text=f"Discharge: {vet['dischargeMonth']} {vet['dischargeDay']}, {vet['dischargeYear']}")
        
        self.retry_label.config(text=f"Retries: {self.retry_count}/{max_retries}")
        self.stats_label.config(text=f"📊 Veterans: {len(self.veterans)} | Current: #{self.current_index + 1}")
    
    def next_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index + 1) % len(self.veterans)
            self.retry_count = 0
            self.update_veteran_display()
    
    def prev_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index - 1) % len(self.veterans)
            self.retry_count = 0
            self.update_veteran_display()
    
    def remove_and_next(self):
        """Remove current veteran and move to next"""
        if self.veterans:
            removed = self.veterans.pop(self.current_index)
            save_veterans(self.veterans)
            self.log(f"🗑 Removed: {removed[:50]}...")
            
            if self.current_index >= len(self.veterans):
                self.current_index = 0
            self.retry_count = 0
            self.update_veteran_display()
    
    def reload_data(self):
        """Reload veterans from file"""
        self.veterans = load_veterans()
        self.current_index = 0
        self.retry_count = 0
        self.update_veteran_display()
        self.log(f"🔄 Reloaded {len(self.veterans)} veterans")
    
    def get_verification_link(self):
        """Get new verification link from ChatGPT API"""
        token = self.token_entry.get().strip()
        device_id = self.device_entry.get().strip()
        cookies_raw = self.cookies_text.get("1.0", tk.END).strip()
        
        if not token:
            self.log("❌ No Bearer Token configured!")
            return None
        
        # Build cookie string from JSON or raw format
        cookie_str = ""
        if cookies_raw:
            try:
                # Try parsing as JSON array from Cookie Editor
                cookies_list = json.loads(cookies_raw)
                cookie_parts = []
                for c in cookies_list:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        cookie_parts.append(f"{c['name']}={c['value']}")
                cookie_str = "; ".join(cookie_parts)
            except:
                # Use as raw cookie string
                cookie_str = cookies_raw
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "oai-device-id": device_id,
            "oai-language": "en-US",
            "Origin": "https://chatgpt.com",
            "Referer": "https://chatgpt.com/veterans-claim",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "sec-ch-ua": '"Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        
        if cookie_str:
            headers["Cookie"] = cookie_str
            self.log(f"   Using cookies ({len(cookie_str)} chars)")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(CHATGPT_API_URL, headers=headers, json={})
                self.log(f"   API Response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"   Data: {json.dumps(data)}")
                    return data
                else:
                    self.log(f"   Error: {response.text[:200]}")
        except Exception as e:
            self.log(f"   Exception: {str(e)}")
        
        return None
    
    def test_get_link(self):
        """Test getting verification link"""
        self.log("🔗 Testing get verification link...")
        result = self.get_verification_link()
        if result:
            self.log(f"✅ Got response: {result}")
        else:
            self.log("❌ Failed to get link")
    
    def toggle_auto_verify(self):
        """Toggle auto verification mode"""
        if self.is_running:
            self.is_running = False
            self.auto_btn.config(text="🚀 START AUTO VERIFY", bg="#00cc66")
            self.status_label.config(text="Stopped", fg="#ff4444")
            self.log("⏹ Auto-verify stopped")
        else:
            email = self.email_entry.get().strip()
            token = self.token_entry.get().strip()
            
            if not email:
                messagebox.showerror("Error", "Please enter email!")
                return
            
            if not token:
                messagebox.showerror("Error", "Please enter Bearer Token!")
                return
            
            if not self.veterans:
                messagebox.showerror("Error", "No veteran data!")
                return
            
            self.is_running = True
            self.retry_count = 0
            self.auto_btn.config(text="⏹ STOP", bg="#ff4444")
            self.status_label.config(text="Running...", fg="#00ff88")
            self.log("🚀 Auto-verify started")
            
            # Run in thread
            thread = threading.Thread(target=self.auto_verify_loop)
            thread.start()
    
    def auto_verify_loop(self):
        """Main auto verification loop"""
        email = self.email_entry.get().strip()
        max_retries = int(self.retry_spinbox.get())
        
        while self.is_running and self.veterans:
            vet = parse_veteran(self.veterans[self.current_index])
            if not vet:
                self.log("⚠️ Invalid veteran data, skipping...")
                self.root.after(0, self.remove_and_next)
                continue
            
            self.log(f"\n{'='*50}")
            self.log(f"🎯 Trying: {vet['firstName']} {vet['lastName']} (Attempt {self.retry_count + 1}/{max_retries})")
            
            # Step 1: Get new verification link
            self.log("📥 Getting new SheerID link...")
            link_data = self.get_verification_link()
            
            if not link_data:
                self.retry_count += 1
                self.root.after(0, self.update_veteran_display)
                
                if self.retry_count >= max_retries:
                    self.log(f"❌ Max retries reached for {vet['firstName']} {vet['lastName']}")
                    self.retry_count = 0
                    self.root.after(0, self.remove_and_next)
                    continue
                
                self.log("⏳ Waiting 3s before retry...")
                import time
                time.sleep(3)
                continue
            
            # Extract verification ID or URL from response
            verification_id = None
            verification_url = None
            
            if isinstance(link_data, dict):
                verification_id = link_data.get("verificationId") or link_data.get("verification_id")
                verification_url = link_data.get("url") or link_data.get("verification_url") or link_data.get("sheerid_url")
                
                if verification_url:
                    verification_id = extract_verification_id(verification_url)
            
            if not verification_id:
                self.log(f"⚠️ Could not extract verificationId from response: {link_data}")
                self.retry_count += 1
                continue
            
            self.log(f"✅ Got verificationId: {verification_id}")
            
            # Step 2: Submit military status
            result1 = self.step1_military_status(verification_id)
            
            if not result1:
                self.log("❌ Step 1 failed!")
                self.retry_count += 1
                self.root.after(0, self.update_veteran_display)
                
                if self.retry_count >= max_retries:
                    self.log(f"❌ Max retries reached!")
                    self.retry_count = 0
                    self.root.after(0, self.remove_and_next)
                
                import time
                time.sleep(2)
                continue
            
            current_step = result1.get("currentStep", "")
            self.log(f"✅ Step 1 OK - Next: {current_step}")
            
            # Step 3: Submit personal info
            if current_step == "collectInactiveMilitaryPersonalInfo":
                submission_url = result1.get("submissionUrl")
                result2 = self.step2_personal_info(verification_id, vet, email, submission_url)
                
                if result2:
                    final_step = result2.get("currentStep", "")
                    self.log(f"✅ Step 2 OK - Status: {final_step}")
                    
                    if final_step in ["success", "emailLoop"]:
                        self.log("🎉 VERIFICATION SUCCESS!")
                        self.retry_count = 0
                        self.root.after(0, self.remove_and_next)
                        
                        # Small delay before next
                        import time
                        time.sleep(2)
                        continue
                    else:
                        self.log(f"⚠️ Unexpected status: {final_step}")
                else:
                    self.log("❌ Step 2 failed! (Bad veteran data)")
                    self.retry_count = 0
                    self.root.after(0, self.remove_and_next)
            else:
                self.log(f"⚠️ Unexpected step: {current_step}")
            
            import time
            time.sleep(2)
        
        # Finished
        self.is_running = False
        self.root.after(0, lambda: self.auto_btn.config(text="🚀 START AUTO VERIFY", bg="#00cc66"))
        self.root.after(0, lambda: self.status_label.config(text="Finished", fg="#888"))
        self.log("✅ Auto-verify finished!")
    
    def step1_military_status(self, verification_id):
        url = f"{SHEERID_BASE_URL}/{verification_id}/step/collectMilitaryStatus"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json={"status": "VETERAN"})
                self.log(f"   Step 1 Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    try:
                        err = response.json()
                        self.log(f"   Error: {err.get('errorIds', err)}")
                    except:
                        self.log(f"   Error: {response.text[:200]}")
        except Exception as e:
            self.log(f"   Exception: {str(e)}")
        return None
    
    def step2_personal_info(self, verification_id, vet, email, submission_url=None):
        url = submission_url or f"{SHEERID_BASE_URL}/{verification_id}/step/collectInactiveMilitaryPersonalInfo"
        
        branch = vet.get("branch", "Navy")
        org = ORGANIZATIONS.get(branch, ORGANIZATIONS["Navy"])
        
        birth_date = format_date(vet["birthYear"], vet["birthMonth"], vet["birthDay"])
        
        # Always use actual discharge date if year is 2025, otherwise Dec 1, 2025
        if vet["dischargeYear"] == "2025":
            discharge_date = format_date(vet["dischargeYear"], vet["dischargeMonth"], vet["dischargeDay"])
        else:
            discharge_date = "2025-12-01"
        
        payload = {
            "firstName": vet["firstName"],
            "lastName": vet["lastName"],
            "birthDate": birth_date,
            "email": email,
            "organization": org,
            "dischargeDate": discharge_date,
            "metadata": {}
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                self.log(f"   Step 2 Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    try:
                        err = response.json()
                        self.log(f"   Error: {err.get('errorIds', err)}")
                    except:
                        pass
        except Exception as e:
            self.log(f"   Exception: {str(e)}")
        return None


# ===================== MAIN =====================

if __name__ == "__main__":
    root = tk.Tk()
    app = MilitaryVerifyAppV3(root)
    root.mainloop()
