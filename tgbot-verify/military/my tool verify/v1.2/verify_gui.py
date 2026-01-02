#!/usr/bin/env python3
"""
🎖️ Military Verification GUI Tool V1.1
Giao diện đồ họa để xác thực Military SheerID
Thêm tính năng Thùng Rác (Trash Bin) để lưu veteran đã xóa
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
TRASH_FILE = "trash_veterans.txt"

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


def load_trash():
    """Load veterans from trash file"""
    trash = []
    if os.path.exists(TRASH_FILE):
        with open(TRASH_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    trash.append(line)
    return trash


def save_trash(trash):
    """Save trash to file"""
    with open(TRASH_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(trash))


def parse_veteran(line):
    """Parse veteran line to dict - supports multiple formats"""
    parts = line.split("|")
    num_parts = len(parts)
    
    # Format 1: 6-field veteran data
    # FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear
    if num_parts == 6:
        return {
            "firstName": parts[0].strip(),
            "lastName": parts[1].strip(),
            "branch": parts[2].strip(),
            "birthMonth": parts[3].strip(),
            "birthDay": parts[4].strip(),
            "birthYear": parts[5].strip(),
            # Auto-generate discharge date (December 1, 2025)
            "dischargeMonth": "December",
            "dischargeDay": "1",
            "dischargeYear": "2025",
            "email": ""  # Will be filled from email_entry
        }
    
    # Format 2: 4-field account data  
    # email|password|refreshToken|clientId
    if num_parts == 4:
        return {
            "firstName": "",
            "lastName": "",
            "branch": "",
            "birthMonth": "",
            "birthDay": "",
            "birthYear": "",
            "dischargeMonth": "December",
            "dischargeDay": "1",
            "dischargeYear": "2025",
            "email": parts[0].strip(),
            "password": parts[1].strip(),
            "refreshToken": parts[2].strip(),
            "clientId": parts[3].strip(),
            "isAccountData": True  # Flag to identify account data
        }
    
    # Format 3: Original 10-field format
    # firstName|lastName|branch|birthMonth|birthDay|birthYear|dischargeMonth|dischargeDay|dischargeYear|email
    if num_parts >= 10:
        return {
            "firstName": parts[0].strip(),
            "lastName": parts[1].strip(),
            "branch": parts[2].strip(),
            "birthMonth": parts[3].strip(),
            "birthDay": parts[4].strip(),
            "birthYear": parts[5].strip(),
            "dischargeMonth": parts[6].strip(),
            "dischargeDay": parts[7].strip(),
            "dischargeYear": parts[8].strip(),
            "email": parts[9].strip()
        }
    
    return None


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
        self.root.title("🎖️ Military Verification Tool V1.1")
        self.root.geometry("850x750")
        self.root.configure(bg="#1a1a2e")
        
        # Load data
        self.veterans = load_veterans()
        self.trash = load_trash()
        self.current_index = 0
        
        self.setup_ui()
        self.update_veteran_display()
        self.update_trash_display()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root, 
            text="🎖️ MILITARY VERIFICATION TOOL V1.1",
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
            text=f"📊 Veterans: {len(self.veterans)} | 🗑 Trash: {len(self.trash)}",
            font=("Arial", 12),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.stats_label.pack(side="left")
        
        # === NOTEBOOK (TABS) ===
        style = ttk.Style()
        style.configure("TNotebook", background="#1a1a2e")
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[15, 5])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab 1: Main Verify
        self.main_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.main_tab, text="🎖️ Main Verify")
        
        # Tab 2: Trash Bin
        self.trash_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.trash_tab, text=f"🗑 Trash Bin ({len(self.trash)})")
        
        # Setup both tabs
        self.setup_main_tab()
        self.setup_trash_tab()
    
    def setup_main_tab(self):
        """Setup Main Verify Tab"""
        # === INPUT SECTION ===
        input_frame = tk.LabelFrame(
            self.main_tab, 
            text="📝 Input",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e",
            padx=10, pady=10
        )
        input_frame.pack(fill="x", padx=10, pady=10)
        
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
            self.main_tab,
            text="👤 Current Veteran",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e",
            padx=10, pady=10
        )
        vet_frame.pack(fill="x", padx=10, pady=10)
        
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
        btn_frame = tk.Frame(self.main_tab, bg="#1a1a2e")
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
            self.main_tab,
            text="📋 Log",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg="#16213e"
        )
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 10),
            bg="#0a0a1a",
            fg="#00ff88"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.main_tab,
            text="Ready",
            fg="#888",
            bg="#1a1a2e",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=10)
    
    def setup_trash_tab(self):
        """Setup Trash Bin Tab"""
        # Title
        trash_title = tk.Label(
            self.trash_tab,
            text="🗑 Thùng Rác - Veteran đã xóa",
            font=("Arial", 14, "bold"),
            fg="#ff8800",
            bg="#1a1a2e"
        )
        trash_title.pack(pady=10)
        
        # Trash count
        self.trash_count_label = tk.Label(
            self.trash_tab,
            text=f"Có {len(self.trash)} veteran trong thùng rác",
            font=("Arial", 11),
            fg="white",
            bg="#1a1a2e"
        )
        self.trash_count_label.pack()
        
        # Listbox with scrollbar
        list_frame = tk.Frame(self.trash_tab, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.trash_listbox = tk.Listbox(
            list_frame,
            font=("Consolas", 10),
            bg="#0a0a1a",
            fg="#ffaa00",
            selectbackground="#3366ff",
            selectforeground="white",
            height=15,
            yscrollcommand=scrollbar.set
        )
        self.trash_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.trash_listbox.yview)
        
        # Buttons
        btn_frame = tk.Frame(self.trash_tab, bg="#1a1a2e")
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="♻️ Re-verify Selected",
            command=self.reverify_from_trash,
            font=("Arial", 11, "bold"),
            bg="#00cc66",
            fg="white",
            width=18
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="❌ Delete Selected",
            command=self.delete_from_trash,
            font=("Arial", 11),
            bg="#ff4444",
            fg="white",
            width=15
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="🗑 Clear All Trash",
            command=self.clear_all_trash,
            font=("Arial", 11),
            bg="#880000",
            fg="white",
            width=15
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=self.refresh_trash,
            font=("Arial", 11),
            bg="#3366ff",
            fg="white",
            width=10
        ).pack(side="left", padx=10)
    
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
            self.update_stats()
            return
        
        if self.current_index >= len(self.veterans):
            self.current_index = 0
        
        line = self.veterans[self.current_index]
        vet = parse_veteran(line)
        
        if vet:
            # Check if this is account data (4-field format)
            if vet.get('isAccountData'):
                self.vet_name_label.config(text=f"Email: {vet['email']}")
                self.vet_branch_label.config(text="(Account data - needs veteran info)")
                self.vet_birth_label.config(text="---")
                self.vet_discharge_label.config(text=f"Discharge: {vet['dischargeMonth']} {vet['dischargeDay']}, {vet['dischargeYear']}")
            else:
                # Veteran data (6-field or 10-field format)
                name = f"{vet['firstName']} {vet['lastName']}".strip() or "---"
                branch = vet['branch'] or "---"
                birth = f"{vet['birthMonth']} {vet['birthDay']}, {vet['birthYear']}" if vet['birthMonth'] else "---"
                discharge = f"{vet['dischargeMonth']} {vet['dischargeDay']}, {vet['dischargeYear']}"
                
                self.vet_name_label.config(text=f"Name: {name}")
                self.vet_branch_label.config(text=f"Branch: {branch}")
                self.vet_birth_label.config(text=f"Birth: {birth}")
                self.vet_discharge_label.config(text=f"Discharge: {discharge}")
        
        self.update_stats()
    
    def update_stats(self):
        """Update statistics labels"""
        self.stats_label.config(
            text=f"📊 Veterans: {len(self.veterans)} | 🗑 Trash: {len(self.trash)} | Current: #{self.current_index + 1}"
        )
        self.notebook.tab(1, text=f"🗑 Trash Bin ({len(self.trash)})")
    
    def update_trash_display(self):
        """Update trash listbox"""
        self.trash_listbox.delete(0, tk.END)
        for i, line in enumerate(self.trash):
            vet = parse_veteran(line)
            if vet:
                display = f"{i+1}. {vet['firstName']} {vet['lastName']} | {vet['branch']} | {vet['birthYear']}"
                self.trash_listbox.insert(tk.END, display)
        
        self.trash_count_label.config(text=f"Có {len(self.trash)} veteran trong thùng rác")
        self.update_stats()
    
    def move_to_trash(self, veteran_line):
        """Move veteran to trash bin"""
        self.trash.append(veteran_line)
        save_trash(self.trash)
        self.update_trash_display()
    
    def next_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index + 1) % len(self.veterans)
            self.update_veteran_display()
    
    def prev_veteran(self):
        if self.veterans:
            self.current_index = (self.current_index - 1) % len(self.veterans)
            self.update_veteran_display()
    
    def remove_and_next(self):
        """Remove current veteran, move to trash, and go next"""
        if self.veterans:
            removed = self.veterans.pop(self.current_index)
            save_veterans(self.veterans)
            
            # Move to trash
            self.move_to_trash(removed)
            
            vet = parse_veteran(removed)
            if vet:
                self.log(f"🗑 Moved to trash: {vet['firstName']} {vet['lastName']}")
            
            if self.current_index >= len(self.veterans):
                self.current_index = 0
            self.update_veteran_display()
    
    def reload_data(self):
        """Reload veterans from file"""
        self.veterans = load_veterans()
        self.trash = load_trash()
        self.current_index = 0
        self.update_veteran_display()
        self.update_trash_display()
        self.log(f"🔄 Reloaded {len(self.veterans)} veterans, {len(self.trash)} in trash")
    
    # === TRASH TAB FUNCTIONS ===
    
    def reverify_from_trash(self):
        """Load selected trash veteran to main verify form"""
        selection = self.trash_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Vui lòng chọn veteran cần re-verify!")
            return
        
        idx = selection[0]
        veteran_line = self.trash[idx]
        vet = parse_veteran(veteran_line)
        
        if vet:
            # Update main form with this veteran
            self.vet_name_label.config(text=f"Name: {vet['firstName']} {vet['lastName']}")
            self.vet_branch_label.config(text=f"Branch: {vet['branch']}")
            self.vet_birth_label.config(text=f"Birth: {vet['birthMonth']} {vet['birthDay']}, {vet['birthYear']}")
            self.vet_discharge_label.config(text=f"Discharge: {vet['dischargeMonth']} {vet['dischargeDay']}, {vet['dischargeYear']}")
            
            # Store for verification
            self.trash_verify_line = veteran_line
            self.trash_verify_index = idx
            
            # Switch to main tab
            self.notebook.select(0)
            
            self.log(f"♻️ Re-verify from trash: {vet['firstName']} {vet['lastName']}")
            self.status_label.config(text="🔄 Re-verifying from trash...", fg="#ffaa00")
            messagebox.showinfo("Re-verify", f"Đã load veteran từ thùng rác:\n{vet['firstName']} {vet['lastName']}\n\nNhập link SheerID và email rồi click VERIFY NOW.")
    
    def delete_from_trash(self):
        """Delete selected veteran from trash permanently"""
        selection = self.trash_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Vui lòng chọn veteran cần xóa!")
            return
        
        idx = selection[0]
        vet = parse_veteran(self.trash[idx])
        
        if messagebox.askyesno("Confirm", f"Xóa vĩnh viễn:\n{vet['firstName']} {vet['lastName']}?"):
            self.trash.pop(idx)
            save_trash(self.trash)
            self.update_trash_display()
            self.log(f"❌ Deleted from trash: {vet['firstName']} {vet['lastName']}")
    
    def clear_all_trash(self):
        """Clear all veterans from trash"""
        if not self.trash:
            messagebox.showinfo("Info", "Thùng rác đã trống!")
            return
        
        if messagebox.askyesno("Confirm", f"Xóa vĩnh viễn {len(self.trash)} veteran trong thùng rác?"):
            self.trash = []
            save_trash(self.trash)
            self.update_trash_display()
            self.log("🗑 Cleared all trash")
    
    def refresh_trash(self):
        """Refresh trash list"""
        self.trash = load_trash()
        self.update_trash_display()
        self.log("🔄 Refreshed trash list")
    
    # === VERIFICATION ===
    
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
        
        # Check if re-verifying from trash
        if hasattr(self, 'trash_verify_line'):
            # Use trash veteran
            veteran_line = self.trash_verify_line
        elif not self.veterans:
            messagebox.showerror("Error", "No veteran data!")
            return
        else:
            veteran_line = self.veterans[self.current_index]
        
        verification_id = extract_verification_id(link)
        if not verification_id:
            messagebox.showerror("Error", "Invalid SheerID link!")
            return
        
        # Disable button
        self.verify_btn.config(state="disabled", text="⏳ Verifying...")
        self.status_label.config(text="Verifying...", fg="#ffaa00")
        
        # Run in thread
        thread = threading.Thread(target=self.do_verification, args=(verification_id, email, veteran_line))
        thread.start()
    
    def do_verification(self, verification_id, email, veteran_line):
        """Perform verification (runs in thread)"""
        try:
            vet = parse_veteran(veteran_line)
            
            self.log(f"🚀 Starting verification...")
            self.log(f"   ID: {verification_id}")
            self.log(f"   Veteran: {vet['firstName']} {vet['lastName']}")
            self.log(f"   Email: {email}")
            
            # Step 1
            result1 = self.step1_military_status(verification_id)
            
            if not result1:
                self.log("❌ Step 1 FAILED! (Link issue - data kept)")
                self.on_step1_fail()
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
                self.log(f"   Step 1 Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    # Log error details
                    try:
                        err = response.json()
                        self.log(f"   Error: {err.get('errorIds', err)}")
                    except:
                        self.log(f"   Error body: {response.text[:200]}")
        except Exception as e:
            self.log(f"   Exception: {str(e)}")
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
        
        # Clear trash verify if was re-verifying
        if hasattr(self, 'trash_verify_line'):
            delattr(self, 'trash_verify_line')
            if hasattr(self, 'trash_verify_index'):
                delattr(self, 'trash_verify_index')
        else:
            # Auto remove and next (move to trash)
            self.root.after(0, self.remove_and_next)
    
    def on_verify_fail(self):
        """Handle failed verification - remove data and move to trash"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 VERIFY NOW"))
        self.root.after(0, lambda: self.status_label.config(text="❌ Verification failed!", fg="#ff4444"))
        self.root.after(0, lambda: self.log("=" * 40))
        
        # Clear trash verify if was re-verifying
        if hasattr(self, 'trash_verify_line'):
            delattr(self, 'trash_verify_line')
            if hasattr(self, 'trash_verify_index'):
                delattr(self, 'trash_verify_index')
        else:
            # Auto remove and next (move to trash)
            self.root.after(0, self.remove_and_next)
    
    def on_step1_fail(self):
        """Handle Step 1 failure - DON'T remove data (link issue)"""
        self.root.after(0, lambda: self.verify_btn.config(state="normal", text="🚀 VERIFY NOW"))
        self.root.after(0, lambda: self.status_label.config(text="❌ Step 1 failed - Check link!", fg="#ff4444"))
        self.root.after(0, lambda: self.log("=" * 40))
        
        # Clear trash verify if was re-verifying
        if hasattr(self, 'trash_verify_line'):
            delattr(self, 'trash_verify_line')
            if hasattr(self, 'trash_verify_index'):
                delattr(self, 'trash_verify_index')


# ===================== MAIN =====================

if __name__ == "__main__":
    root = tk.Tk()
    app = MilitaryVerifyApp(root)
    root.mainloop()
