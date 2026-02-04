"""
Grok Signup Automation Tool - GUI Version
Graphical user interface using Tkinter
"""

import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from pathlib import Path
import threading
from typing import List, Dict
import random

from config import (
    DEFAULT_FIRST_NAMES,
    DEFAULT_LAST_NAMES,
    OUTPUT_SUCCESS_FILE,
    OUTPUT_FAILED_FILE,
    INPUT_ACCOUNTS_FILE
)
from utils.email_service import generate_email, check_email_for_code
from utils.browser_handler import GrokBrowser


class GrokSignupGUI:
    """GUI Application for Grok Signup Automation"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Grok Account Signup Automation Tool")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # State variables
        self.is_running = False
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'current': 0}
        self.signup_mode = tk.StringVar(value='browser')  # 'browser' or 'api_direct'
        
        # Setup UI
        self.setup_ui()
        
        # Ensure output directories exist
        Path(OUTPUT_SUCCESS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_FAILED_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # ==================== HEADER ====================
        header_frame = tk.Frame(self.root, bg='#1a1a1a', height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🚀 Grok Signup Automation", 
            font=('Arial', 20, 'bold'),
            bg='#1a1a1a',
            fg='#00ffaa'
        )
        title_label.pack(pady=20)
        
        # ==================== MAIN CONTAINER ====================
        main_container = tk.Frame(self.root, bg='#0d0d0d')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ==================== LEFT PANEL ====================
        left_panel = tk.Frame(main_container, bg='#1e1e1e', relief=tk.RAISED, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Input Section
        input_frame = tk.LabelFrame(left_panel, text="📝 Input Accounts", font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#00ffaa')
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Account input text area
        self.account_text = scrolledtext.ScrolledText(
            input_frame,
            height=15,
            font=('Consolas', 10),
            bg='#2d2d2d',
            fg='#e0e0e0',
            insertbackground='#00ffaa'
        )
        self.account_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.account_text.insert('1.0', '# Format: email|password|first_name|last_name\n# First/last name optional\n\n# Example:\nuser1@gmail.com|Password123\nuser2@gmail.com|Pass456|John|Doe\n')
        
        # Buttons row
        button_frame = tk.Frame(input_frame, bg='#1e1e1e')
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(
            button_frame,
            text="📂 Load File",
            command=self.load_accounts_file,
            bg='#0066cc',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#0052a3'
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="🎲 Generate Random",
            command=self.generate_random_accounts,
            bg='#7d3c98',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#6c2d7f'
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_accounts,
            bg='#c0392b',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#a93226'
        ).pack(side=tk.LEFT, padx=2)
        
        # Mode Selection
        mode_frame = tk.LabelFrame(left_panel, text="⚙️ Signup Mode", font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#00ffaa')
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        mode_container = tk.Frame(mode_frame, bg='#1e1e1e')
        mode_container.pack(pady=10, padx=10)
        
        tk.Radiobutton(
            mode_container,
            text="🌐 Browser Mode (Recommended - Auto Cloudflare)",
            variable=self.signup_mode,
            value='browser',
            bg='#1e1e1e',
            fg='#00ff00',
            selectcolor='#2d2d2d',
            activebackground='#1e1e1e',
            activeforeground='#00ffaa',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=2)
        
        tk.Radiobutton(
            mode_container,
            text="📡 API Direct Mode (Fast but needs Turnstile)",
            variable=self.signup_mode,
            value='api_direct',
            bg='#1e1e1e',
            fg='#ffaa00',
            selectcolor='#2d2d2d',
            activebackground='#1e1e1e',
            activeforeground='#00ffaa',
            font=('Arial', 10)
        ).pack(anchor=tk.W, pady=2)
        
        # Mode info label
        self.mode_info = tk.Label(
            mode_container,
            text="ℹ️ Browser mode: Slower but auto-solves Cloudflare",
            bg='#1e1e1e',
            fg='#888888',
            font=('Arial', 8),
            wraplength=350,
            justify=tk.LEFT
        )
        self.mode_info.pack(anchor=tk.W, pady=(5, 0))
        
        # Control Section
        control_frame = tk.LabelFrame(left_panel, text="🎮 Controls", font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#00ffaa')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Start/Stop buttons
        btn_container = tk.Frame(control_frame, bg='#1e1e1e')
        btn_container.pack(pady=10)
        
        self.start_button = tk.Button(
            btn_container,
            text="▶️ START",
            command=self.start_automation,
            bg='#00aa44',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#008833'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            btn_container,
            text="⏹️ STOP",
            command=self.stop_automation,
            bg='#cc6600',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED,
            activebackground='#b35900'
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # ==================== RIGHT PANEL ====================
        right_panel = tk.Frame(main_container, bg='#1e1e1e', relief=tk.RAISED, borderwidth=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Statistics Section
        stats_frame = tk.LabelFrame(right_panel, text="📊 Statistics", font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#00ffaa')
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats_container = tk.Frame(stats_frame, bg='#1e1e1e')
        stats_container.pack(fill=tk.X, pady=10)
        
        # Stats labels
        self.total_label = self.create_stat_label(stats_container, "Total", "0", "#3498db")
        self.success_label = self.create_stat_label(stats_container, "Success", "0", "#27ae60")
        self.failed_label = self.create_stat_label(stats_container, "Failed", "0", "#e74c3c")
        
        # Progress bar
        progress_frame = tk.Frame(stats_frame, bg='#1e1e1e')
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(progress_frame, text="Progress:", bg='#1e1e1e', fg='#cccccc', font=('Arial', 9)).pack(anchor=tk.W)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0/0 (0%)",
            bg='#1e1e1e',
            font=('Arial', 9),
            fg='#888888'
        )
        self.progress_label.pack()
        
        # Log Section
        log_frame = tk.LabelFrame(right_panel, text="📋 Activity Log", font=('Arial', 11, 'bold'), bg='#1e1e1e', fg='#00ffaa')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#00ff00',
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # ==================== FOOTER ====================
        footer_frame = tk.Frame(self.root, bg='#0d0d0d', height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            footer_frame,
            text="Ready",
            bg='#0d0d0d',
            fg='#00ffaa',
            font=('Arial', 9, 'bold')
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def create_stat_label(self, parent, title, value, color):
        """Create a statistic label"""
        frame = tk.Frame(parent, bg='#1e1e1e')
        frame.pack(side=tk.LEFT, expand=True, padx=5)
        
        tk.Label(
            frame,
            text=title,
            bg='#1e1e1e',
            fg='#888888',
            font=('Arial', 9)
        ).pack()
        
        label = tk.Label(
            frame,
            text=value,
            bg='#1e1e1e',
            fg=color,
            font=('Arial', 18, 'bold')
        )
        label.pack()
        
        return label
    
    def log(self, message, color='#00ff00'):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_stats(self):
        """Update statistics display"""
        self.total_label.config(text=str(self.stats['total']))
        self.success_label.config(text=str(self.stats['success']))
        self.failed_label.config(text=str(self.stats['failed']))
        
        if self.stats['total'] > 0:
            progress = (self.stats['current'] / self.stats['total']) * 100
            self.progress_var.set(progress)
            self.progress_label.config(
                text=f"{self.stats['current']}/{self.stats['total']} ({progress:.0f}%)"
            )
    
    def update_status(self, text):
        """Update status bar"""
        self.status_label.config(text=text)
    
    def load_accounts_file(self):
        """Load accounts from file"""
        filename = filedialog.askopenfilename(
            title="Select Accounts File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.account_text.delete('1.0', tk.END)
                self.account_text.insert('1.0', content)
                self.log(f"✅ Loaded accounts from {filename}", '#00ff00')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def generate_random_accounts(self):
        """Generate random accounts"""
        count = tk.simpledialog.askinteger(
            "Generate Accounts",
            "How many accounts to generate?",
            minvalue=1,
            maxvalue=100
        )
        
        if count:
            self.account_text.delete('1.0', tk.END)
            for i in range(1, count + 1):
                first = random.choice(DEFAULT_FIRST_NAMES)
                last = random.choice(DEFAULT_LAST_NAMES)
                email = f"grok_user_{i}@example.com"
                password = f"GrokPass{i}!2024"
                self.account_text.insert(tk.END, f"{email}|{password}|{first}|{last}\n")
            
            self.log(f"✅ Generated {count} random accounts", '#00ff00')
    
    def clear_accounts(self):
        """Clear account input"""
        self.account_text.delete('1.0', tk.END)
        self.log("🗑️ Cleared accounts", '#ffaa00')
    
    def parse_accounts(self) -> List[Dict[str, str]]:
        """Parse accounts from text input"""
        content = self.account_text.get('1.0', tk.END)
        accounts = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('|')
            if len(parts) < 2:
                continue
            
            account = {
                'email': parts[0].strip(),
                'password': parts[1].strip(),
                'first_name': parts[2].strip() if len(parts) >= 3 else random.choice(DEFAULT_FIRST_NAMES),
                'last_name': parts[3].strip() if len(parts) >= 4 else random.choice(DEFAULT_LAST_NAMES)
            }
            accounts.append(account)
        
        return accounts
    
    def start_automation(self):
        """Start the signup automation"""
        accounts = self.parse_accounts()
        
        if not accounts:
            messagebox.showwarning("No Accounts", "Please add some accounts first!")
            return
        
        # Confirm
        if not messagebox.askyesno(
            "Confirm",
            f"Start processing {len(accounts)} accounts?"
        ):
            return
        
        # Reset stats
        self.stats = {
            'total': len(accounts),
            'success': 0,
            'failed': 0,
            'current': 0
        }
        self.update_stats()
        
        # Update UI
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Running...")
        
        self.log(f"🚀 Starting automation for {len(accounts)} accounts", '#00ffff')
        
        # Run in background thread
        thread = threading.Thread(target=self.run_automation, args=(accounts,))
        thread.daemon = True
        thread.start()
    
    def stop_automation(self):
        """Stop the automation"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Stopped")
        self.log("⏹️ Automation stopped by user", '#ff6600')
    
    def run_automation(self, accounts):
        """Run automation in background (threaded)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.process_accounts(accounts))
        except Exception as e:
            self.log(f"❌ Error: {str(e)}", '#ff0000')
        finally:
            loop.close()
            
            # Update UI
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.update_status("Complete"))
            
            # Show summary
            self.root.after(0, self.show_summary)
    
    async def process_accounts(self, accounts):
        """Process accounts sequentially"""
        for i, account in enumerate(accounts, 1):
            if not self.is_running:
                self.log("⏹️ Stopped by user", '#ff6600')
                break
            
            self.stats['current'] = i
            self.root.after(0, self.update_stats)
            
            email = account['email']
            self.log(f"\n{'='*50}", '#ffffff')
            self.log(f"📧 Processing {i}/{self.stats['total']}: {email}", '#00ffff')
            
            try:
                result = await self.signup_account(account)
                
                if result['status'] == 'success':
                    self.stats['success'] += 1
                    self.log(f"✅ Success: {email}", '#00ff00')
                    self.save_result(result)
                else:
                    self.stats['failed'] += 1
                    self.log(f"❌ Failed: {email} - {result.get('error', 'Unknown')}", '#ff0000')
                    self.save_result(result)
            
            except Exception as e:
                # Log error but continue processing
                self.stats['failed'] += 1
                self.log(f"❌ Exception for {email}: {str(e)}", '#ff0000')
                self.save_result({
                    'status': 'failed',
                    'email': email,
                    'error': str(e),
                    'temp_email': None
                })
            
            self.root.after(0, self.update_stats)
            
            # Delay between accounts
            if i < len(accounts) and self.is_running:
                self.log("⏳ Waiting 30s before next account...", '#ffaa00')
                await asyncio.sleep(30)
    
    async def signup_account(self, account_data):
        """Signup single account using selected mode"""
        mode = self.signup_mode.get()
        
        if mode == 'browser':
            return await self.signup_browser_mode(account_data)
        else:
            return await self.signup_api_mode(account_data)
    
    async def signup_browser_mode(self, account_data):
        """Signup using browser automation"""
        email = account_data['email']
        password = account_data['password']
        first_name = account_data['first_name']
        last_name = account_data['last_name']
        
        browser = None
        temp_email = None
        
        try:
            # Generate temp email
            self.log("📧 [Browser Mode] Generating temporary email...", '#00ffff')
            temp_email = await generate_email()
            self.log(f"✅ Temp email: {temp_email}", '#00ff00')
            
            # Start browser
            self.log("🌐 Launching browser...", '#00ffff')
            browser = GrokBrowser(headless=False)
            await browser.start()
            
            # Navigate
            self.log("🔗 Navigating to signup page...", '#00ffff')
            await browser.navigate_to_signup()
            
            # Cloudflare - with longer timeout
            self.log("🔐 Handling Cloudflare (60s timeout)...", '#00ffff')
            await browser.wait_for_cloudflare(timeout=60)
            
            # Fill form
            self.log(f"📝 Filling form: {first_name} {last_name}", '#00ffff')
            await browser.fill_email_field(temp_email)
            await browser.fill_name_fields(first_name, last_name)
            await browser.request_verification_code()
            
            # Get code
            self.log("📬 Waiting for verification code...", '#00ffff')
            verification_code = await check_email_for_code(temp_email)
            
            if not verification_code:
                raise Exception("Failed to retrieve verification code")
            
            self.log(f"✅ Code received: {verification_code}", '#00ff00')
            
            # Submit code
            await browser.submit_verification_code(verification_code)
            
            # Set credentials
            self.log("🔑 Setting account credentials...", '#00ffff')
            await browser.set_account_credentials(email, password)
            
            # Check success
            await asyncio.sleep(3)
            success = await browser.check_signup_success()
            
            if not success:
                raise Exception("Signup validation failed")
            
            return {
                'status': 'success',
                'email': email,
                'password': password,
                'temp_email': temp_email,
                'verification_code': verification_code
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'email': email,
                'error': str(e),
                'temp_email': temp_email
            }
        finally:
            if browser:
                await browser.close()
    
    async def signup_api_mode(self, account_data):
        """Signup using API Direct mode"""
        from utils.api_direct import signup_account_api
        
        email = account_data['email']
        password = account_data['password']
        first_name = account_data['first_name']
        last_name = account_data['last_name']
        
        self.log("📡 [API Direct Mode] Starting...", '#ffaa00')
        self.log("⚠️ Note: Requires Turnstile token solving", '#ff6600')
        
        try:
            result = await signup_account_api(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            return result
        except Exception as e:
            return {
                'status': 'failed',
                'email': email,
                'error': str(e),
                'temp_email': None
            }
    
    def save_result(self, result):
        """Save result to file"""
        try:
            if result['status'] == 'success':
                with open(OUTPUT_SUCCESS_FILE, 'a', encoding='utf-8') as f:
                    line = f"{result['email']}|{result['password']}|{result['temp_email']}|{result['verification_code']}|{datetime.now().isoformat()}\n"
                    f.write(line)
            else:
                with open(OUTPUT_FAILED_FILE, 'a', encoding='utf-8') as f:
                    line = f"{result['email']}|{result.get('error', 'Unknown')}|{datetime.now().isoformat()}\n"
                    f.write(line)
        except Exception as e:
            self.log(f"⚠️ Failed to save result: {str(e)}", '#ff6600')
    
    def show_summary(self):
        """Show final summary"""
        total = self.stats['total']
        success = self.stats['success']
        failed = self.stats['failed']
        rate = (success / total * 100) if total > 0 else 0
        
        message = f"""
Signup Summary:
━━━━━━━━━━━━━━
Total: {total}
✅ Success: {success}
❌ Failed: {failed}
📊 Success Rate: {rate:.1f}%

Results saved to:
• {OUTPUT_SUCCESS_FILE}
• {OUTPUT_FAILED_FILE}
        """
        
        messagebox.showinfo("Summary", message)


def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = GrokSignupGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # Import simpledialog for random generation
    import tkinter.simpledialog
    main()
