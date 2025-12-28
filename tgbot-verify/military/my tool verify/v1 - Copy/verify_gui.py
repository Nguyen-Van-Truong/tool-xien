#!/usr/bin/env python3
"""
🎖️ Military Verification GUI Tool
Giao diện đồ họa để xác thực Military SheerID
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
DATA_FILE = "all_veterans.txt"

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


def extract_verification_id(url):
    """Extract verificationId from URL"""
    match = re.search(r'verificationId=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    # Try path format
    match = re.search(r'/verify/[^/]+/?\?verificationId=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None


# ===================== GUI CLASS =====================

class MilitaryVerifyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎖️ Military Verification Tool")
        self.root.geometry("800x700")
        self.root.configure(bg="#1a1a2e")
        
        # Load data
        self.veterans = load_veterans()
        self.current_index = 0
        
        self.setup_ui()
        self.update_veteran_display()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root, 
            text="🎖️ MILITARY VERIFICATION TOOL",
            font=("Arial", 18, "bold"),
            fg="#00ff88",
            bg="#1a1a2e"
        )
        title.pack(pady=10)
        
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
        
        # === INPUT SECTION ===
        input_frame = tk.LabelFrame(
            self.root, 
            text="📝 Input",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e",
            padx=10, pady=10
        )
        input_frame.pack(fill="x", padx=20, pady=10)
        
        # SheerID Link
        tk.Label(input_frame, text="🔗 SheerID Link:", fg="white", bg="#16213e").grid(row=0, column=0, sticky="w")
        self.link_entry = tk.Entry(input_frame, width=70, font=("Arial", 10))
        self.link_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Email
        tk.Label(input_frame, text="📧 Email:", fg="white", bg="#16213e").grid(row=1, column=0, sticky="w")
        self.email_entry = tk.Entry(input_frame, width=70, font=("Arial", 10))
        self.email_entry.grid(row=1, column=1, pady=5, padx=5)
        
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
        
        # Navigation buttons
        nav_frame = tk.Frame(vet_frame, bg="#16213e")
        nav_frame.pack(fill="x", pady=10)
        
        tk.Button(nav_frame, text="⏮ Prev", command=self.prev_veteran, bg="#444", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Next ⏭", command=self.next_veteran, bg="#444", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(nav_frame, text="🗑 Remove & Next", command=self.remove_and_next, bg="#ff4444", fg="white", width=15).pack(side="left", padx=5)
        
        # === ACTION BUTTONS ===
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=15)
        
        self.verify_btn = tk.Button(
            btn_frame,
            text="🚀 VERIFY NOW",
            command=self.run_verification,
            font=("Arial", 14, "bold"),
            bg="#00cc66",
            fg="white",
            width=20,
            height=2
        )
        self.verify_btn.pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Reload Data",
            command=self.reload_data,
            font=("Arial", 11),
            bg="#3366ff",
            fg="white",
            width=15
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
            height=12,
            font=("Consolas", 10),
            bg="#0a0a1a",
            fg="#00ff88"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            fg="#888",
            bg="#1a1a2e",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20)
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_veteran_display(self):
        """Update current veteran display"""
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
        
        self.stats_label.config(text=f"📊 Veterans: {len(self.veterans)} | Current: #{self.current_index + 1}")
    
    def next_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index + 1) % len(self.veterans)
            self.update_veteran_display()
    
    def prev_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index - 1) % len(self.veterans)
            self.update_veteran_display()
    
    def remove_and_next(self):
        """Remove current veteran and move to next"""
        if self.veterans:
            removed = self.veterans.pop(self.current_index)
            save_veterans(self.veterans)
            self.log(f"🗑 Removed: {removed[:50]}...")
            
            if self.current_index >= len(self.veterans):
                self.current_index = 0
            self.update_veteran_display()
    
    def reload_data(self):
        """Reload veterans from file"""
        self.veterans = load_veterans()
        self.current_index = 0
        self.update_veteran_display()
        self.log(f"🔄 Reloaded {len(self.veterans)} veterans")
    
    def run_verification(self):
        """Run verification in background thread"""
        link = self.link_entry.get().strip()
        email = self.email_entry.get().strip()
        
        if not link:
            messagebox.showerror("Error", "Please enter SheerID link!")
            return
        
        if not email:
            messagebox.showerror("Error", "Please enter email!")
            return
        
        if not self.veterans:
            messagebox.showerror("Error", "No veteran data!")
            return
        
        verification_id = extract_verification_id(link)
        if not verification_id:
            messagebox.showerror("Error", "Invalid SheerID link!")
            return
        
        # Disable button
        self.verify_btn.config(state="disabled", text="⏳ Verifying...")
        self.status_label.config(text="Verifying...", fg="#ffaa00")
        
        # Run in thread
        thread = threading.Thread(target=self.do_verification, args=(verification_id, email))
        thread.start()
    
    def do_verification(self, verification_id, email):
        """Perform verification (runs in thread)"""
        try:
            vet = parse_veteran(self.veterans[self.current_index])
            
            self.log(f"🚀 Starting verification...")
            self.log(f"   ID: {verification_id}")
            self.log(f"   Veteran: {vet['firstName']} {vet['lastName']}")
            self.log(f"   Email: {email}")
            
            # Step 1
            result1 = self.step1_military_status(verification_id)
            
            if not result1:
                self.log("❌ Step 1 FAILED!")
                self.on_verify_fail()
                return
            
            current_step = result1.get("currentStep", "")
            self.log(f"✅ Step 1 OK - Next: {current_step}")
            
            # Step 2
            if current_step == "collectInactiveMilitaryPersonalInfo":
                submission_url = result1.get("submissionUrl")
                result2 = self.step2_personal_info(verification_id, vet, email, submission_url)
                
                if result2:
                    final_step = result2.get("currentStep", "")
                    self.log(f"✅ Step 2 OK - Status: {final_step}")
                    
                    if final_step == "success":
                        self.on_verify_success()
                    elif final_step == "emailLoop":
                        self.log("📧 Check your email to complete verification!")
                        self.on_verify_success()
                    else:
                        self.on_verify_fail()
                else:
                    self.log("❌ Step 2 FAILED!")
                    self.on_verify_fail()
            else:
                self.log(f"⚠️ Unexpected step: {current_step}")
                self.on_verify_fail()
                
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            self.on_verify_fail()
    
    def step1_military_status(self, verification_id):
        url = f"{SHEERID_BASE_URL}/{verification_id}/step/collectMilitaryStatus"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json={"status": "VETERAN"})
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None
    
    def step2_personal_info(self, verification_id, vet, email, submission_url=None):
        url = submission_url or f"{SHEERID_BASE_URL}/{verification_id}/step/collectInactiveMilitaryPersonalInfo"
        
        branch = vet.get("branch", "Navy")
        org = ORGANIZATIONS.get(branch, ORGANIZATIONS["Navy"])
        
        birth_date = format_date(vet["birthYear"], vet["birthMonth"], vet["birthDay"])
        
        # If discharge year is 2025, use actual date. Otherwise use December 1, 2025
        if vet["dischargeYear"] == "2025":
            discharge_date = format_date(vet["dischargeYear"], vet["dischargeMonth"], vet["dischargeDay"])
        else:
            discharge_date = "2025-12-01"
            self.log(f"   📅 Using discharge: December 1, 2025 (original: {vet['dischargeYear']})")
        
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
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None
    
    def on_verify_success(self):
        """Handle successful verification"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 VERIFY NOW"))
        self.root.after(0, lambda: self.status_label.config(text="✅ Verification submitted!", fg="#00ff88"))
        self.root.after(0, lambda: self.log("=" * 40))
        
        # Auto remove and next
        self.root.after(0, self.remove_and_next)
    
    def on_verify_fail(self):
        """Handle failed verification"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 VERIFY NOW"))
        self.root.after(0, lambda: self.status_label.config(text="❌ Verification failed!", fg="#ff4444"))
        self.root.after(0, lambda: self.log("=" * 40))
        
        # Auto remove and next
        self.root.after(0, self.remove_and_next)


# ===================== MAIN =====================

if __name__ == "__main__":
    root = tk.Tk()
    app = MilitaryVerifyApp(root)
    root.mainloop()
