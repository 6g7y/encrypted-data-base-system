import os
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

class SecureVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TERMINAL - SECURE DATABASE")
        self.root.geometry("750x550")
        self.root.configure(bg="#050505")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_dir = os.path.join(self.base_dir, "Database_Vault")
        self.auth_file = os.path.join(self.db_dir, ".auth")
        self.cipher = None
        self.current_profile = None

        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        self.start_boot_sequence()

    # --- LOADING SCREEN ---
    def start_boot_sequence(self):
        self.boot_frame = tk.Frame(self.root, bg="#050505")
        self.boot_frame.pack(fill=tk.BOTH, expand=True)

        self.log_label = tk.Label(self.boot_frame, text="> INITIALIZING SYSTEM...", bg="#050505", fg="#00ff00", font=("Courier", 14))
        self.log_label.pack(expand=True)

        # Timed loading messages
        stages = [
            (1000, "> LOADING ENCRYPTION KERNEL..."),
            (2000, "> ESTABLISHING OFFLINE VAULT..."),
            (3000, "> MOUNTING DATABASE_VAULT/"),
            (4000, "COMPLETE")
        ]

        for delay, msg in stages:
            if msg == "COMPLETE":
                self.root.after(delay, self.show_login_screen)
            else:
                self.root.after(delay, lambda m=msg: self.log_label.config(text=m))

    # --- LOGIN SCREEN ---
    def show_login_screen(self):
        self.boot_frame.destroy()
        self.login_frame = tk.Frame(self.root, bg="#050505")
        self.login_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.login_frame, text="ENCRYPTED ACCESS GATE", bg="#050505", fg="#00ff00", font=("Courier", 20, "bold")).pack(pady=(80, 40))

        # Username
        tk.Label(self.login_frame, text="ID:", bg="#050505", fg="white", font=("Courier", 12)).pack()
        self.user_entry = tk.Entry(self.login_frame, bg="#111", fg="#00ff00", font=("Courier", 14), insertbackground="white", borderwidth=1)
        self.user_entry.pack(pady=10)

        # Password
        tk.Label(self.login_frame, text="SECRET:", bg="#050505", fg="white", font=("Courier", 12)).pack()
        self.pass_entry = tk.Entry(self.login_frame, show="*", bg="#111", fg="#00ff00", font=("Courier", 14), insertbackground="white", borderwidth=1)
        self.pass_entry.pack(pady=10)

        tk.Button(self.login_frame, text="[ DECRYPT ]", bg="#003300", fg="#00ff00", font=("Courier", 12, "bold"), 
                  command=self.attempt_access, activebackground="#00ff00").pack(pady=30)

    def attempt_access(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()

        if not u or not p:
            messagebox.showwarning("Access Denied", "Credentials required.")
            return

        # Derive key from Username + Password
        salt = hashlib.sha256(u.encode()).digest()
        kdf = hashlib.pbkdf2_hmac('sha256', p.encode(), salt, 100000)
        key = base64.urlsafe_b64encode(kdf)
        self.cipher = Fernet(key)

        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'rb') as f:
                    self.cipher.decrypt(f.read())
            else:
                # First time setup
                with open(self.auth_file, 'wb') as f:
                    f.write(self.cipher.encrypt(b"VAL-SEC-OK"))
            
            self.show_main_db()
        except InvalidToken:
            messagebox.showerror("CRITICAL ERROR", "DECRYPTION FAILED: WRONG CREDENTIALS")

    # --- MAIN DATABASE UI ---
    def show_main_db(self):
        self.login_frame.destroy()
        self.main_frame = tk.Frame(self.root, bg="#111")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Side bar
        side = tk.Frame(self.main_frame, bg="#1a1a1a", width=220)
        side.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(side, text="PROFILES", bg="#1a1a1a", fg="#00ff00", font=("Courier", 12, "bold")).pack(pady=15)
        
        self.listbox = tk.Listbox(side, bg="#050505", fg="#00ff00", borderwidth=0, font=("Courier", 11), selectbackground="#004400")
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        self.listbox.bind("<<ListboxSelect>>", self.load_profile)

        tk.Button(side, text="+ NEW", bg="#222", fg="white", command=self.add_profile).pack(fill=tk.X, padx=10, pady=5)
        tk.Button(side, text="- DEL", bg="#300", fg="white", command=self.del_profile).pack(fill=tk.X, padx=10, pady=5)

        # Content area
        content = tk.Frame(self.main_frame, bg="#111")
        content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.head_label = tk.Label(content, text="No Profile Selected", bg="#111", fg="#00ff00", font=("Courier", 16))
        self.head_label.pack(pady=5)

        self.text_area = tk.Text(content, bg="#0a0a0a", fg="white", font=("Courier", 12), borderwidth=0, insertbackground="white")
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Button(content, text="[ SEND DATA TO VAULT ]", bg="#004400", fg="white", font=("Courier", 12, "bold"), command=self.save_profile).pack(fill=tk.X)

        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for d in os.listdir(self.db_dir):
            if os.path.isdir(os.path.join(self.db_dir, d)):
                self.listbox.insert(tk.END, d)

    def add_profile(self):
        name = simpledialog.askstring("System", "Input Profile Name:")
        if name:
            p = os.path.join(self.db_dir, name)
            if not os.path.exists(p):
                os.makedirs(p)
                with open(os.path.join(p, "data.enc"), 'wb') as f:
                    f.write(self.cipher.encrypt(f"Profile: {name}".encode()))
                self.refresh_list()

    def del_profile(self):
        sel = self.listbox.curselection()
        if sel:
            name = self.listbox.get(sel[0])
            if messagebox.askyesno("Confirm", f"Purge {name} from database?"):
                shutil.rmtree(os.path.join(self.db_dir, name))
                self.refresh_list()

    def load_profile(self, e):
        sel = self.listbox.curselection()
        if sel:
            self.current_profile = self.listbox.get(sel[0])
            self.head_label.config(text=f"ACTIVE: {self.current_profile}")
            path = os.path.join(self.db_dir, self.current_profile, "data.enc")
            with open(path, 'rb') as f:
                dec = self.cipher.decrypt(f.read()).decode()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, dec)

    def save_profile(self):
        if self.current_profile:
            path = os.path.join(self.db_dir, self.current_profile, "data.enc")
            data = self.text_area.get(1.0, tk.END).strip()
            with open(path, 'wb') as f:
                f.write(self.cipher.encrypt(data.encode()))
            messagebox.showinfo("Success", "Data Encrypted and Stored.")

if __name__ == "__main__":
    root = tk.Tk()
    SecureVaultApp(root)
    root.mainloop()