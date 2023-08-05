import csv
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from PIL import ImageTk, Image

def submit_phone_number():
    phone_number = phone_entry.get()
    if phone_number:
        display_user_data(phone_number)
        
def display_user_data(phone_number):
    try:
        with open('data.csv', mode='r') as file:
            reader = csv.DictReader(file)
            user_data = [row for row in reader if row['phone_number'] == phone_number]
            
            if not user_data:
                messagebox.showerror("Error", "Phone number not found.")
            else:
                create_table(user_data)
    except FileNotFoundError:
        messagebox.showerror("Error", "CSV file not found.")

def create_table(user_data):
    table_frame = Frame(window)
    table_frame.pack(padx=10, pady=10)

    table = ttk.Treeview(table_frame, columns=('weight', 'success', 'time'))
    table.heading('#0', text='Phone Number')
    table.heading('weight', text='Weight (g)')
    table.heading('success', text='Successfully Dispensed')
    table.heading('time', text='Time')

    table.column('#0', width=100)
    table.column('weight', width=100)
    table.column('success', width=150)
    table.column('time', width=150)

    table.pack()

    for data in user_data:
        phone_number = data['phone_number']
        weight = data['weight']
        success = data['success']
        time_created = data['time']
        
        table.insert('', 'end', text=phone_number, values=(weight, success, time_created))

window = Tk()
window.title("Smart Paws GUI")
window.minsize(width=800, height=500)

frame = Frame(window, width=200, height=400)
frame.pack()
frame.place(anchor='center', relx=0.5, rely=0.5)
img = Image.open("Walter_White_S5B.png")
img = img.resize((800, 200), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)

label = Label(frame, image = img)
label.pack()

title_label = Label(window, text="Smart Paws GUI", font=("Arial", 16))
title_label.pack(pady=5)

description_label = Label(window, text="Check your feeding history!", font=("Arial", 12))
description_label.pack(pady=5)

phone_label = Label(window, text="Enter your phone number:")
phone_label.pack(pady=5)

# Phone Number Entry
phone_entry = Entry(window)
phone_entry.pack(pady=5)

# Submit Button
submit_button = Button(window, text="Submit", command=submit_phone_number)
submit_button.pack()

window.mainloop()
