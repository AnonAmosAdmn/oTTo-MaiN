import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import requests
import queue
import pkg_resources
import os
import json
import sqlite3
import sys
import re
import site
from bs4 import BeautifulSoup

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OLLAMA OTTO-DA.SH v 0.11.0")
        self.root.geometry("1200x950")

        self.queue = queue.Queue()
        self.create_menu()
        self.create_main_frame()
        self.otto_page()
        self.root.after(100, self.process_queue)

    ### MAIN LAYOUT ###
    def create_menu(self):
        menubar = tk.Menu(self.root)
        menubar.add_command(label="OTTO-DASH", command=self.otto_page)
        menubar.add_command(label="Ai-Page", command=self.ai_page)
        menubar.add_command(label="Exit", command=self.root.quit)
        self.root.config(menu=menubar)

    ### MAIN FRAME ###
    def create_main_frame(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

    ### OTTO PAGE ###
    def otto_page(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text=" OTTO-DA.SH ").pack(padx=20, pady=20)

    ### CLEAR FRAME ###
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    ### AI PAGE ###
    def ai_page(self):
        self.clear_frame()
        self.ai_frame = ttk.LabelFrame(self.main_frame, text="AI Query")
        self.ai_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.server_control_frame = tk.Frame(self.ai_frame)
        self.server_control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ttk.Button(self.server_control_frame, text="Start Ollama", command=self.start_ollama)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(self.server_control_frame, text="Stop Ollama", command=self.stop_ollama)
        self.stop_button.pack(side="left", padx=5)
        
        self.model_control_frame = tk.Frame(self.ai_frame)
        self.model_control_frame.pack(fill="x", padx=10, pady=10)
        
        self.model_label = tk.Label(self.model_control_frame, text="Models:")
        self.model_label.pack(side="left", padx=5)
        
        self.model_combobox = ttk.Combobox(self.model_control_frame)
        self.model_combobox.pack(side="left", padx=5)
        
        self.refresh_models_button = ttk.Button(self.model_control_frame, text="Refresh Models", command=self.refresh_models)
        self.refresh_models_button.pack(side="left", padx=5)
        
        self.pull_model_button = ttk.Button(self.model_control_frame, text="Pull Model", command=self.pull_model)
        self.pull_model_button.pack(side="left", padx=5)
        
        self.save_model_frame = tk.Frame(self.ai_frame)
        self.save_model_frame.pack(fill="x", padx=10, pady=10)
        
        self.new_model_name_entry = ttk.Entry(self.save_model_frame, width=50)
        self.new_model_name_entry.pack(side="left", padx=5)
        
        self.save_model_button = ttk.Button(self.save_model_frame, text="Save Model As", command=self.save_model)
        self.save_model_button.pack(side="left", padx=5)

        self.ai_output = tk.Text(self.ai_frame, height=20)
        self.ai_output.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.ai_input_frame = tk.Frame(self.ai_frame)
        self.ai_input_frame.pack(fill="x", padx=10, pady=10)
        
        self.ai_input = ttk.Entry(self.ai_input_frame, width=100)
        self.ai_input.pack(side="left", padx=5)
        self.ai_input.bind("<Return>", self.submit_ai_query)
        
        self.ai_submit = ttk.Button(self.ai_input_frame, text="Submit", command=self.submit_ai_query)
        self.ai_submit.pack(side="left", padx=5)

        self.refresh_models()  # Fetch models at startup
        self.model_combobox.set("mistral")  # Set default model to "mistral"

    def start_ollama(self):
        threading.Thread(target=self.run_subprocess, args=(["ollama", "serve"], "Ollama server started.\n")).start()

    def stop_ollama(self):
        threading.Thread(target=self.run_subprocess, args=(["pkill", "-f", "ollama"], "Ollama server stopped.\n")).start()

    def refresh_models(self):
        threading.Thread(target=self._fetch_models_thread).start()

    def _fetch_models_thread(self):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                models_output = result.stdout
                models = self.parse_model_names(models_output)
                self.queue.put(('update_models', models))
            else:
                self.queue.put(('error', f"Error fetching models: {result.stderr}"))
        except Exception as e:
            self.queue.put(('error', f"Error: {e}"))

    def parse_model_names(self, models_output):
        models = []
        lines = models_output.splitlines()
        for line in lines[1:]:  # Skip the first line (header)
            parts = line.split()
            if parts:
                model_name = parts[0]  # Assuming the model name is the first part
                models.append(model_name)
        return models

    def pull_model(self):
        model_name = self.model_combobox.get()
        if not model_name:
            self.queue.put(('error', "Please select a model to pull."))
            return
        threading.Thread(target=self.run_subprocess, args=(["ollama", "pull", model_name], f"Model '{model_name}' pulled successfully.\n")).start()

    def save_model(self):
        original_model = self.model_combobox.get()
        new_model_name = self.new_model_name_entry.get()
        if not original_model or not new_model_name:
            self.queue.put(('error', "Please select a model and enter a new model name."))
            return
        threading.Thread(target=self.run_subprocess, args=(["ollama", "cp", original_model, new_model_name], f"Model saved as '{new_model_name}'.\n")).start()

    def submit_ai_query(self, event=None):
        query = self.ai_input.get()
        self.queue.put(('output', f"You: {query}\n"))
        self.process_ai_query(query)
        self.ai_input.delete(0, tk.END)

    def process_ai_query(self, query):
        model_name = self.model_combobox.get()
        if not model_name:
            self.queue.put(('error', "Please select a model to use for the query."))
            return
        threading.Thread(target=self.run_subprocess, args=(["ollama", "run", model_name, query],)).start()

    def run_subprocess(self, command, success_message=None):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                if success_message:
                    self.queue.put(('output', success_message))
                else:
                    self.queue.put(('output', result.stdout))
            else:
                self.queue.put(('error', f"Error: {result.stderr}"))
        except Exception as e:
            self.queue.put(('error', f"Error: {e}"))

    def process_queue(self):
        while not self.queue.empty():
            message_type, message = self.queue.get()
            if message_type == 'output':
                self.ai_output.insert(tk.END, message)
                self.ai_output.see(tk.END)
            elif message_type == 'error':
                messagebox.showerror("Error", message)
            elif message_type == 'update_models':
                self.model_combobox['values'] = message
                self.ai_output.insert(tk.END, "Models refreshed.\n")
                self.ai_output.see(tk.END)
        self.root.after(100, self.process_queue)


    ### CLIENT PAGE ###
    def client_page(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Clients").pack(padx=20, pady=20)

    ### SERVER PAGE ###
    def server_page(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Servers").pack(padx=20, pady=20)

    ### SETTINGS PAGE ###
    def settings_page(self):
        self.clear_frame()
        ttk.Label(self.main_frame, text="Settings").pack(padx=20, pady=20)

### MAIN FUNCTION ###
if __name__ == "__main__":

    # Start the Tkinter main loop
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()