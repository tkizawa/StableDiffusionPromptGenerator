import tkinter as tk
from tkinter import ttk
import json
import pyperclip
import os
import requests
import uuid

class StableDiffusionPromptGenerator:
    def __init__(self, master):
        self.master = master
        master.title("Stable Diffusion Prompt Generator")

        # Load settings
        self.load_settings()

        # Create GUI elements
        self.create_widgets()

        # Load previous work and window settings
        self.load_work()

        # Configure row and column weights for resizing
        for i in range(7):
            master.grid_rowconfigure(i, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)

        # Bind the configure event to update_layout
        master.bind("<Configure>", self.update_layout)

    def load_settings(self):
        try:
            with open('setting.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.translator_endpoint = settings['TRANSLATOR_ENDPOINT']
                self.translator_key = settings['TRANSLATOR_KEY']
                self.translator_region = settings['TRANSLATOR_REGION']
        except FileNotFoundError:
            print("Settings file not found. Please create a setting.json file.")
        except json.JSONDecodeError:
            print("Error decoding the settings file. Please check the JSON format.")
        except KeyError as e:
            print(f"Missing key in settings file: {e}")

    def create_widgets(self):
        # Fixed text input
        ttk.Label(self.master, text="固定テキスト:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.fixed_text = tk.Text(self.master, height=3, width=50)
        self.fixed_text.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Keywords input
        ttk.Label(self.master, text="キーワード (1行に1つ):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.keywords = tk.Text(self.master, height=10, width=50)
        self.keywords.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Output
        ttk.Label(self.master, text="生成されたプロンプト:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.output = tk.Text(self.master, height=5, width=50)
        self.output.grid(row=5, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        # Buttons
        self.clear_button = ttk.Button(self.master, text="クリア", command=self.clear_fields)
        self.clear_button.grid(row=6, column=0, pady=10)

        self.generate_button = ttk.Button(self.master, text="プロンプト生成", command=self.generate_prompt)
        self.generate_button.grid(row=6, column=1, pady=10)

        self.copy_button = ttk.Button(self.master, text="コピー", command=self.copy_to_clipboard)
        self.copy_button.grid(row=6, column=2, pady=10)

    def update_layout(self, event=None):
        # Update text widget sizes
        width = self.master.winfo_width() - 20  # Subtract padding
        self.fixed_text.config(width=width)
        self.keywords.config(width=width)
        self.output.config(width=width)

    def generate_prompt(self):
        fixed_keywords = self.fixed_text.get("1.0", tk.END).strip().split('\n')
        user_keywords = self.keywords.get("1.0", tk.END).strip().split('\n')
        
        all_keywords = fixed_keywords + user_keywords
        
        # Create Japanese prompt
        japanese_prompt = self.create_prompt(all_keywords)
        
        # Translate prompt to English
        english_keywords = self.translate_to_english(japanese_prompt)
        
        # Format the English keywords
        formatted_prompt = self.format_prompt(english_keywords)
        
        # Set output
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, formatted_prompt)
        
        # Save work
        self.save_work()

    def create_prompt(self, keywords):
        prompt_parts = []
        for keyword in keywords:
            if ':' in keyword:
                base, weight = keyword.rsplit(':', 1)
                prompt_parts.append(f"({base.strip()}:{weight.strip()})")
            else:
                prompt_parts.append(f"({keyword.strip()})")
        
        return ','.join(prompt_parts)

    def translate_to_english(self, japanese_prompt):
        endpoint = self.translator_endpoint
        subscription_key = self.translator_key
        region = self.translator_region

        path = '/translate'
        constructed_url = endpoint + path

        params = {
            'api-version': '3.0',
            'from': 'ja',
            'to': ['en']
        }

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Ocp-Apim-Subscription-Region': region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{
            'text': japanese_prompt
        }]

        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()

        if request.status_code == 200:
            translated_text = response[0]['translations'][0]['text']
            return translated_text.split(',')
        else:
            print(f"Error translating prompt: {request.status_code}")
            return japanese_prompt.split(',')  # Fallback to original prompt

    def format_prompt(self, keywords):
        formatted_keywords = []
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword.startswith('(') and keyword.endswith(')'):
                # カッコが既に存在する場合は、そのまま使用
                formatted_keywords.append(keyword)
            elif ':' in keyword:
                base, weight = keyword.rsplit(':', 1)
                formatted_keywords.append(f"({base.strip()}:{weight.strip()})")
            else:
                formatted_keywords.append(f"({keyword})")
        return ', '.join(formatted_keywords)

    def copy_to_clipboard(self):
        prompt = self.output.get("1.0", tk.END).strip()
        pyperclip.copy(prompt)

    def clear_fields(self):
        self.keywords.delete("1.0", tk.END)
        self.output.delete("1.0", tk.END)

    def load_work(self):
        try:
            with open('work.json', 'r', encoding='utf-8') as f:
                work = json.load(f)
                self.fixed_text.delete("1.0", tk.END)
                self.fixed_text.insert(tk.END, work.get('fixed_text', ''))
                self.keywords.delete("1.0", tk.END)
                self.keywords.insert(tk.END, work.get('keywords', ''))
                self.output.delete("1.0", tk.END)
                self.output.insert(tk.END, work.get('output', ''))

                # Restore window position and size
                geometry = work.get('window_geometry', '')
                if geometry:
                    self.master.geometry(geometry)
        except FileNotFoundError:
            print("No previous work found.")
        except json.JSONDecodeError:
            print("Error decoding the work file. Please check the JSON format.")

    def save_work(self):
        work = {
            'fixed_text': self.fixed_text.get("1.0", tk.END).strip(),
            'keywords': self.keywords.get("1.0", tk.END).strip(),
            'output': self.output.get("1.0", tk.END).strip(),
            'window_geometry': self.master.geometry()
        }
        with open('work.json', 'w', encoding='utf-8') as f:
            json.dump(work, f, ensure_ascii=False, indent=2)

    def on_closing(self):
        self.save_work()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StableDiffusionPromptGenerator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()