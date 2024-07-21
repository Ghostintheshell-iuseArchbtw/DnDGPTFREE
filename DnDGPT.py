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
import queue

# Configuration for the local LLM server
SERVER_URL = 'http://192.168.1.187:9003/v1/chat/completions'
TEMPERATURE = 0.8
MAX_TOKENS = -1
TOP_P = 0.8
FREQ_PENALTY = 0.0
PRES_PENALTY = 0.0

# Global variables
conversation_history = []
response_queue = queue.Queue()
# Example definition of current_user
current_user = None
#current_user = UserProfile(name="Player1", avatar="", char_class="", level=1, strength=10, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10)

# User profile class
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
        self.skills = {}
        self.equipment = []
        self.inventory = []
        self.gold = 0

# Combatant class
class Combatant:
    def __init__(self, name, initiative, hp, ac):
        self.name = name
        self.initiative = initiative
        self.hp = hp
        self.ac = ac
        self.conditions = []

    def add_condition(self, condition):
        if condition not in self.conditions:
            self.conditions.append(condition)

    def remove_condition(self, condition):
        if condition in self.conditions:
            self.conditions.remove(condition)

# Combat and party management
combatants = []
party = []

# Helper functions
def make_inference_request():
    """Send a request to the LLM server and update the chat window with the response."""
    global conversation_history
    payload = {
        "messages": conversation_history,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "top_p": TOP_P,
        "frequency_penalty": FREQ_PENALTY,
        "presence_penalty": PRES_PENALTY,
        "stream": True
    }

    try:
        with requests.post(SERVER_URL, json=payload, headers={"Content-Type": "application/json"}, stream=True) as response:
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
        loading_label.pack_forget()

def update_chat_window(message, sender="user"):
    """Update the chat window with a new message."""
    chat_window.configure(state=ctk.NORMAL)
    global current_user
    if sender == "user":
        chat_window.insert(ctk.END, f"{current_user.name}: {message}\n", "user")
        conversation_history.append({"role": "user", "content": message})
    elif sender == "assistant":
        chat_window.insert(ctk.END, f"GPT: {message}\n", "assistant")
        conversation_history.append({"role": "assistant", "content": message})
    elif sender == "error":
        chat_window.insert(ctk.END, f"Error: {message}\n", "error")
    chat_window.configure(state=ctk.DISABLED)
    chat_window.yview(ctk.END)

def on_send(event=None):
    """Send the user's message when Enter is pressed or Send button is clicked."""
    user_input = user_entry.get()
    if user_input.strip():
        update_chat_window(user_input, sender="user")
        loading_label.pack(pady=5)
        threading.Thread(target=make_inference_request, daemon=True).start()
        user_entry.delete(0, ctk.END)

def clear_chat():
    """Clear the chat history."""
    chat_window.configure(state=ctk.NORMAL)
    chat_window.delete(1.0, ctk.END)
    chat_window.configure(state=ctk.DISABLED)
    conversation_history.clear()

def update_settings():
    """Update the settings based on user input."""
    global TEMPERATURE, MAX_TOKENS, TOP_P, FREQ_PENALTY, PRES_PENALTY
    try:
        TEMPERATURE = float(temp_entry.get())
        MAX_TOKENS = int(tokens_entry.get())
        TOP_P = float(top_p_entry.get())
        FREQ_PENALTY = float(freq_penalty_entry.get())
        PRES_PENALTY = float(pres_penalty_entry.get())
        messagebox.showinfo("Settings Updated", "Settings have been updated successfully!")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numerical values for the settings.")

def save_chat():
    """Save the chat history to a file."""
    chat_text = chat_window.get(1.0, ctk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(chat_text)
        messagebox.showinfo("Chat Saved", "Chat history saved successfully!")

def speak(text):
    """Convert text to speech and play it."""
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
    """Toggle between light and dark themes."""
    current_mode = ctk.get_appearance_mode()
    new_mode = "light" if current_mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)

def roll_dice(sides):
    """Roll a dice with the specified number of sides and show the result."""
    roll_result = random.randint(1, sides)
    messagebox.showinfo(f"D{sides} Roll", f"You rolled a {roll_result}!")

def add_combatant():
    """Add a new combatant to the combat tracker."""
    name = combatant_name_entry.get()
    initiative = initiative_entry.get()
    hp = hp_entry.get()
    ac = ac_entry.get()
    if name and initiative and hp and ac:
        combatant = Combatant(name, int(initiative), int(hp), int(ac))
        combatants.append(combatant)
        combatants_listbox.insert(tk.END, f"{name} (Initiative: {initiative}, HP: {hp}, AC: {ac})")
        combatant_name_entry.delete(0, tk.END)
        initiative_entry.delete(0, tk.END)
        hp_entry.delete(0, tk.END)
        ac_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Please enter all details (name, initiative, HP, AC).")

def remove_combatant():
    """Remove the selected combatant from the combat tracker."""
    selected_index = combatants_listbox.curselection()
    if selected_index:
        combatants.pop(selected_index[0])  # Use pop instead of del
        combatants_listbox.delete(selected_index)
    else:
        messagebox.showerror("Error", "Please select a combatant to remove.")

def start_combat():
    """Start the combat (placeholder for future functionality)."""
    messagebox.showinfo("Combat", "Combat has started!")

def show_about():
    """Display information about the application."""
    messagebox.showinfo("About", "D&D Tracker & Chatbot v1.0\nDeveloped by Joey")

# Main GUI setup
root = tk.Tk()
root.title("D&D Tracker & Chatbot")

# Chat frame
chat_frame = ctk.CTkFrame(root)
chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

chat_window = ctk.CTkTextbox(chat_frame, wrap=tk.WORD, state=ctk.DISABLED)
chat_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(chat_frame, command=chat_window.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_window.configure(yscrollcommand=scrollbar.set)

user_entry = ctk.CTkEntry(root, placeholder_text="Type your message...")
user_entry.pack(padx=10, pady=5, fill=tk.X)

send_button = ctk.CTkButton(root, text="Send", command=on_send)
send_button.pack(pady=5)

loading_label = ctk.CTkLabel(root, text="Loading...", state=tk.DISABLED)

# Settings frame
settings_frame = ctk.CTkFrame(root)
settings_frame.pack(padx=10, pady=10, fill=tk.X)

temp_label = ctk.CTkLabel(settings_frame, text="Temperature:")
temp_label.grid(row=0, column=0, padx=5, pady=5)
temp_entry = ctk.CTkEntry(settings_frame)
temp_entry.grid(row=0, column=1, padx=5, pady=5)
temp_entry.insert(0, str(TEMPERATURE))

tokens_label = ctk.CTkLabel(settings_frame, text="Max Tokens:")
tokens_label.grid(row=1, column=0, padx=5, pady=5)
tokens_entry = ctk.CTkEntry(settings_frame)
tokens_entry.grid(row=1, column=1, padx=5, pady=5)
tokens_entry.insert(0, str(MAX_TOKENS))

top_p_label = ctk.CTkLabel(settings_frame, text="Top P:")
top_p_label.grid(row=2, column=0, padx=5, pady=5)
top_p_entry = ctk.CTkEntry(settings_frame)
top_p_entry.grid(row=2, column=1, padx=5, pady=5)
top_p_entry.insert(0, str(TOP_P))

freq_penalty_label = ctk.CTkLabel(settings_frame, text="Frequency Penalty:")
freq_penalty_label.grid(row=3, column=0, padx=5, pady=5)
freq_penalty_entry = ctk.CTkEntry(settings_frame)
freq_penalty_entry.grid(row=3, column=1, padx=5, pady=5)
freq_penalty_entry.insert(0, str(FREQ_PENALTY))

pres_penalty_label = ctk.CTkLabel(settings_frame, text="Presence Penalty:")
pres_penalty_label.grid(row=4, column=0, padx=5, pady=5)
pres_penalty_entry = ctk.CTkEntry(settings_frame)
pres_penalty_entry.grid(row=4, column=1, padx=5, pady=5)
pres_penalty_entry.insert(0, str(PRES_PENALTY))

update_settings_button = ctk.CTkButton(settings_frame, text="Update Settings", command=update_settings)
update_settings_button.grid(row=5, columnspan=2, pady=10)

# Combat tracker frame
combat_frame = ctk.CTkFrame(root)
combat_frame.pack(padx=10, pady=10, fill=tk.X)

combatant_name_label = ctk.CTkLabel(combat_frame, text="Name:")
combatant_name_label.grid(row=0, column=0, padx=5, pady=5)
combatant_name_entry = ctk.CTkEntry(combat_frame)
combatant_name_entry.grid(row=0, column=1, padx=5, pady=5)

initiative_label = ctk.CTkLabel(combat_frame, text="Initiative:")
initiative_label.grid(row=1, column=0, padx=5, pady=5)
initiative_entry = ctk.CTkEntry(combat_frame)
initiative_entry.grid(row=1, column=1, padx=5, pady=5)

hp_label = ctk.CTkLabel(combat_frame, text="HP:")
hp_label.grid(row=2, column=0, padx=5, pady=5)
hp_entry = ctk.CTkEntry(combat_frame)
hp_entry.grid(row=2, column=1, padx=5, pady=5)

ac_label = ctk.CTkLabel(combat_frame, text="AC:")
ac_label.grid(row=3, column=0, padx=5, pady=5)
ac_entry = ctk.CTkEntry(combat_frame)
ac_entry.grid(row=3, column=1, padx=5, pady=5)

add_combatant_button = ctk.CTkButton(combat_frame, text="Add Combatant", command=add_combatant)
add_combatant_button.grid(row=4, columnspan=2, pady=5)

remove_combatant_button = ctk.CTkButton(combat_frame, text="Remove Combatant", command=remove_combatant)
remove_combatant_button.grid(row=5, columnspan=2, pady=5)

combatants_listbox = tk.Listbox(combat_frame)
combatants_listbox.grid(row=0, column=2, rowspan=5, padx=5, pady=5, sticky="nsew")

start_combat_button = ctk.CTkButton(combat_frame, text="Start Combat", command=start_combat)
start_combat_button.grid(row=6, columnspan=2, pady=10)

# Menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save Chat", command=save_chat)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

settings_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Toggle Theme", command=toggle_theme)

help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=show_about)

# Start the GUI event loop
root.mainloop()
                      
