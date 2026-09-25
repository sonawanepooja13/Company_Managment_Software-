import tkinter as tk
from tkinter import messagebox, ttk

# Create a minimal test window to verify GUI rendering
root = tk.Tk()
root.title("System Login Test")
root.geometry("350x220")

# Center on screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (350 // 2)
y = (screen_height // 2) - (220 // 2)
root.geometry(f"350x220+{x}+{y}")

# UI Elements
frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="System Login", font=("Helvetica", 12, "bold")).pack(pady=(0, 15))

ttk.Label(frame, text="Username:").pack(anchor="w")
entry_user = ttk.Entry(frame)
entry_user.pack(fill="x", pady=(0, 10))

ttk.Label(frame, text="Password:").pack(anchor="w")
entry_pwd = ttk.Entry(frame, show="*")
entry_pwd.pack(fill="x", pady=(0, 15))

def test_login():
    user = entry_user.get()
    pwd = entry_pwd.get()
    if user == "admin" and pwd == "admin123":
        messagebox.showinfo("Success", "Login Successful!")
        root.destroy()
    else:
        messagebox.showerror("Error", "Invalid Credentials")

ttk.Button(frame, text="Login", command=test_login).pack(fill="x")

print("Launching test window...")
root.mainloop()
print("Test window closed.")