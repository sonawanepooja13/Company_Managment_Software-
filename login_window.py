import tkinter as tk
from tkinter import messagebox, ttk

import auth_manager
import subprocess
import datetime


def speak_greeting(username):
    try:
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        safe_name = str(username).replace("'", "''")
        # Add a short welcome phrase after the personalized greeting
        message = f"{greeting}, {safe_name}. Welcome to Saark Operating System"
        ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{message}')"
        subprocess.Popen(["powershell","-NoProfile","-Command",ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return


class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("System Login")
        self.geometry("360x240")
        self.minsize(360, 240)
        self.resizable(True, True)

        # Center on screen
        self.center_window()

        # Force window to stay on top
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        self.authenticated_user = None
        self.user_role = None

        # Build UI Frame
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="System Login",
            font=("Helvetica", 12, "bold"),
        ).pack(pady=(0, 15))

        # Username Field
        ttk.Label(frame, text="Username:").pack(anchor="w")
        self.entry_user = ttk.Entry(frame)
        self.entry_user.pack(fill="x", pady=(0, 10))
        self.entry_user.focus_set()

        # Password Field
        ttk.Label(frame, text="Password:").pack(anchor="w")
        self.entry_pwd = ttk.Entry(frame, show="*")
        self.entry_pwd.pack(fill="x", pady=(0, 15))

        # Bindings & Buttons
        self.entry_pwd.bind("<Return>", lambda event: self.handle_login())
        btn_login = ttk.Button(frame, text="Login", command=self.handle_login)
        btn_login.pack(fill="x")

        # Disable topmost shortly after render to allow normal dialog behavior
        self.after(200, lambda: self.attributes("-topmost", False))

        # Intercept window close (X)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self):
        """Centers the login window on the user screen."""
        self.update_idletasks()
        width = 360
        height = 240
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pwd.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Login Error",
                "Please enter both username and password.",
                parent=self,
            )
            return

        success, role = auth_manager.verify_login(username, password)

        if success:
            self.authenticated_user = username
            self.user_role = role

            # Play greeting (non-blocking)
            try:
                speak_greeting(username)
            except Exception:
                pass

            self.destroy()
        else:
            messagebox.showerror(
                "Access Denied",
                "Invalid username or password.",
                parent=self,
            )
            self.entry_pwd.delete(0, tk.END)

    def on_close(self):
        self.authenticated_user = None
        self.destroy()