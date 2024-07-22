import tkinter as tk
import customtkinter as ctk
import requests
import json
import threading
import tempfile
import os
from gtts import gTTS
from playsound import playsound
from tkinter import filedialog, messagebox
import random

# Local LLM server URL and port
server_url = 'http://192.168.1.187:9003/v1/chat/completions'

# Parameters
temperature = 0.7
max_tokens = -1 
top_p = 0.8
frequency_penalty = 0.0
presence_penalty = 0.0

# User Profile
class UserProfile:
    def __init__(self, name, avatar, char_class, level, strength, dexterity, constitution, intelligence, wisdom, charisma):
        self.name = name
        self.avatar = avatar
        self.char_class = char_class
        self.level = level
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma

# Dummy user profile (replace with actual implementation)
current_user = UserProfile(name="User", avatar="default_avatar.png", char_class="Rouge", level=5, strength=8, dexterity=14, constitution=10, intelligence=18, wisdom=12, charisma=10)

# Conversation history
conversation_history = []

# Functions
def make_inference_request():
    global conversation_history
    payload = {
        "messages": conversation_history,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "stream": True
    }

    try:
        with requests.post(server_url, json=payload, headers={"Content-Type": "application/json"}, stream=True) as response:
            if response.status_code == 200:
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            line_str = line_str[len('data: '):]

                        if line_str == '[DONE]':
                            break

                        try:
                            response_json = json.loads(line_str)
                            if 'choices' in response_json:
                                for choice in response_json['choices']:
                                    delta_content = choice.get('delta', {}).get('content', '')
                                    response_text += delta_content
                        except json.JSONDecodeError:
                            update_chat_window(f"Non-JSON response: {line_str}\n", sender="error")

                if response_text:
                    update_chat_window(response_text, sender="assistant")
                    speak(response_text)
            else:
                update_chat_window(f"Request failed with status code: {response.status_code}\n", sender="error")
                update_chat_window(f"Response: {response.text}\n", sender="error")
    except Exception as e:
        update_chat_window(f"An error occurred: {e}\n", sender="error")
    finally:
        loading_label.grid_forget()

def update_chat_window(message, sender="user"):
    chat_window.configure(state=tk.NORMAL)
    if sender == "user":
        chat_window.insert(tk.END, f"{current_user.name}: {message}\n", "user")
        conversation_history.append({"role": "user", "content": message})
    elif sender == "assistant":
        chat_window.insert(tk.END, f"GPT: {message}\n", "assistant")
        conversation_history.append({"role": "assistant", "content": message})
    elif sender == "error":
        chat_window.insert(tk.END, f"Error: {message}\n", "error")
    chat_window.configure(state=tk.DISABLED)
    chat_window.yview(tk.END)

def on_send(event=None):
    user_input = user_entry.get()
    if user_input.strip():
        update_chat_window(user_input, sender="user")
        loading_label.grid(pady=5)
        threading.Thread(target=make_inference_request).start()
        user_entry.delete(0, tk.END)

def clear_chat():
    chat_window.configure(state=tk.NORMAL)
    chat_window.delete(1.0, tk.END)
    chat_window.configure(state=tk.DISABLED)
    conversation_history.clear()

def update_settings():
    global temperature, max_tokens, top_p, frequency_penalty, presence_penalty
    try:
        temperature = float(temp_entry.get())
        max_tokens = int(tokens_entry.get())
        top_p = float(top_p_entry.get())
        frequency_penalty = float(freq_penalty_entry.get())
        presence_penalty = float(pres_penalty_entry.get())
        messagebox.showinfo("Settings Updated", "Settings have been updated successfully!")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numerical values for the settings.")

def save_chat():
    chat_text = chat_window.get(1.0, tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(chat_text)
        messagebox.showinfo("Chat Saved", "Chat history saved successfully!")

def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file_path = temp_file.name
            tts.save(temp_file_path)
            playsound(temp_file_path)
            os.remove(temp_file_path)
    except Exception as e:
        update_chat_window(f"Text-to-Speech Error: {e}\n", sender="error")

def toggle_theme():
    current_mode = ctk.get_appearance_mode()
    new_mode = "light" if current_mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)

def roll_dice(sides):
    roll_result = random.randint(1, sides)
    messagebox.showinfo(f"D{sides} Roll", f"You rolled a {roll_result}!")

def add_combatant():
    name = combatant_name_entry.get()
    initiative = initiative_entry.get()
    hp = hp_entry.get()
    ac = ac_entry.get()
    if name and initiative and hp and ac:
        combatants_listbox.insert(tk.END, f"{name} (Initiative: {initiative}, HP: {hp}, AC: {ac})")
        combatant_name_entry.delete(0, tk.END)
        initiative_entry.delete(0, tk.END)
        hp_entry.delete(0, tk.END)
        ac_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Please enter all details (name, initiative, HP, AC).")

def remove_combatant():
    selected_index = combatants_listbox.curselection()
    if selected_index:
        combatants_listbox.delete(selected_index)
    else:
        messagebox.showerror("Error", "Please select a combatant to remove.")

def perform_attack():
    attacker = combatants_listbox.get(tk.ACTIVE)
    if attacker:
        attack_roll = random.randint(1, 20)
        messagebox.showinfo("Attack Roll", f"{attacker.split()[0]} rolled a {attack_roll} to attack!")
    else:
        messagebox.showerror("Error", "Please select a combatant to attack.")

def start_combat():
    combatants = combatants_listbox.get(0, tk.END)
    if combatants:
        messagebox.showinfo("Combat Started", "Combat has started! Track initiatives and perform actions.")
    else:
        messagebox.showerror("Error", "No combatants available. Add combatants to start combat.")

# GUI setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Local LLM Chat")
root.geometry("1200x800")

# Chat frame
chat_frame = ctk.CTkFrame(root)
chat_frame.pack(pady=10, padx=10, fill="both", expand=True)

chat_window = ctk.CTkTextbox(chat_frame, wrap=tk.WORD, state=tk.DISABLED, width=580, height=400)
chat_window.tag_config("user", foreground="blue")
chat_window.tag_config("assistant", foreground="green")
chat_window.tag_config("error", foreground="red")
chat_window.pack(padx=10, pady=10, fill="both", expand=True)

# User entry frame
user_entry_frame = ctk.CTkFrame(root)
user_entry_frame.pack(pady=5, padx=10, fill="x")

user_entry = ctk.CTkEntry(user_entry_frame, width=450)
user_entry.grid(row=0, column=0, padx=10, pady=5)
user_entry.bind("<Return>", on_send)

send_button = ctk.CTkButton(user_entry_frame, text="Send", command=on_send)
send_button.grid(row=0, column=1, padx=5, pady=5)

clear_button = ctk.CTkButton(user_entry_frame, text="Clear Chat", command=clear_chat)
clear_button.grid(row=0, column=2, padx=5, pady=5)

save_button = ctk.CTkButton(user_entry_frame, text="Save Chat", command=save_chat)
save_button.grid(row=0, column=3, padx=5, pady=5)

theme_button = ctk.CTkButton(user_entry_frame, text="Toggle Theme", command=toggle_theme)
theme_button.grid(row=0, column=4, padx=5, pady=5)

loading_label = ctk.CTkLabel(user_entry_frame, text="Loading...", text_color="red")

# Dice roll frame
dice_frame = ctk.CTkFrame(root)
dice_frame.pack(pady=10, padx=10, fill="x")

dice_labels = ["D4", "D6", "D8", "D10", "D12", "D20"]
for i, sides in enumerate([4, 6, 8, 10, 12, 20]):
    button = ctk.CTkButton(dice_frame, text=dice_labels[i], command=lambda s=sides: roll_dice(s))
    button.grid(row=0, column=i, padx=5, pady=5)

# Settings frame
settings_frame = ctk.CTkFrame(root)
settings_frame.pack(pady=10, padx=10, fill="x")

ctk.CTkLabel(settings_frame, text="Temperature").grid(row=0, column=0, padx=10, pady=5)
temp_entry = ctk.CTkEntry(settings_frame)
temp_entry.insert(0, str(temperature))
temp_entry.grid(row=0, column=1, padx=10, pady=5)

ctk.CTkLabel(settings_frame, text="Max Tokens").grid(row=1, column=0, padx=10, pady=5)
tokens_entry = ctk.CTkEntry(settings_frame)
tokens_entry.insert(0, str(max_tokens))
tokens_entry.grid(row=1, column=1, padx=10, pady=5)

ctk.CTkLabel(settings_frame, text="Top P").grid(row=2, column=0, padx=10, pady=5)
top_p_entry = ctk.CTkEntry(settings_frame)
top_p_entry.insert(0, str(top_p))
top_p_entry.grid(row=2, column=1, padx=10, pady=5)

ctk.CTkLabel(settings_frame, text="Frequency Penalty").grid(row=3, column=0, padx=10, pady=5)
freq_penalty_entry = ctk.CTkEntry(settings_frame)
freq_penalty_entry.insert(0, str(frequency_penalty))
freq_penalty_entry.grid(row=3, column=1, padx=10, pady=5)

ctk.CTkLabel(settings_frame, text="Presence Penalty").grid(row=4, column=0, padx=10, pady=5)
pres_penalty_entry = ctk.CTkEntry(settings_frame)
pres_penalty_entry.insert(0, str(presence_penalty))
pres_penalty_entry.grid(row=4, column=1, padx=10, pady=5)

update_button = ctk.CTkButton(settings_frame, text="Update Settings", command=update_settings)
update_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Combatant Management
combatant_frame = ctk.CTkFrame(root)
combatant_frame.pack(pady=10, padx=10, fill="x")

combatant_name_entry = ctk.CTkEntry(combatant_frame, placeholder_text="Name")
combatant_name_entry.grid(row=0, column=0, padx=5, pady=5)
initiative_entry = ctk.CTkEntry(combatant_frame, placeholder_text="Initiative")
initiative_entry.grid(row=0, column=1, padx=5, pady=5)
hp_entry = ctk.CTkEntry(combatant_frame, placeholder_text="HP")
hp_entry.grid(row=0, column=2, padx=5, pady=5)
ac_entry = ctk.CTkEntry(combatant_frame, placeholder_text="AC")
ac_entry.grid(row=0, column=3, padx=5, pady=5)

add_combatant_button = ctk.CTkButton(combatant_frame, text="Add Combatant", command=add_combatant)
add_combatant_button.grid(row=0, column=4, padx=5, pady=5)
remove_combatant_button = ctk.CTkButton(combatant_frame, text="Remove Combatant", command=remove_combatant)
remove_combatant_button.grid(row=0, column=5, padx=5, pady=5)

combatants_listbox = tk.Listbox(combatant_frame)
combatants_listbox.grid(row=1, column=0, columnspan=6, pady=10, padx=5, sticky="nsew")

# Attack and Combat Management
attack_button = ctk.CTkButton(combatant_frame, text="Attack", command=perform_attack)
attack_button.grid(row=2, column=0, padx=5, pady=5)
start_combat_button = ctk.CTkButton(combatant_frame, text="Start Combat", command=start_combat)
start_combat_button.grid(row=2, column=1, padx=5, pady=5)

root.mainloop()
