import tkinter as tk
from tkinter import messagebox

# Function to check login credentials
def check_login():
    username = username_entry.get()
    password = password_entry.get()
    
    if username == "admin" and password == "password":
        messagebox.showinfo("Login Success", "Welcome!")
    else:
        messagebox.showerror("Login Failed", "Invalid Username or Password")

# Main GUI Window
root = tk.Tk()
root.title("Login GUI")
root.geometry("3000x150000")

# Username Label and Entry
tk.Label(root, text="Username:").pack(pady=5)
username_entry = tk.Entry(root)
username_entry.pack(pady=5)

# Password Label and Entry
tk.Label(root, text="Password:").pack(pady=5)
password_entry = tk.Entry(root, show="*")
password_entry.pack(pady=5)

# Login Button
login_button = tk.Button(root, text="Login", command=check_login)
login_button.pack(pady=10)

# Run the GUI
root.mainloop()
