#!/usr/bin/env python3
"""
Convertisseur Texte → Audio - Interface Épurée et Moderne
"""

import sys
import os
import subprocess
import threading
import tempfile
from pathlib import Path
import time

# Installation silencieuse des dépendances si nécessaire
def ensure_dependencies():
    """Vérifie et installe les dépendances nécessaires"""
    missing = []
    
    # Vérifier les packages Python
    packages = {
        'PyPDF2': 'PyPDF2',
        'docx': 'python-docx', 
        'pyttsx3': 'pyttsx3',
        'gtts': 'gTTS',
        'customtkinter': 'customtkinter'
    }
    
    for module, package in packages.items():
        try:
            if module == 'docx':
                import docx
            else:
                __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        for package in missing:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         capture_output=True, timeout=60)

ensure_dependencies()

import customtkinter as ctk
from tkinter import filedialog, messagebox

class AudioConverter:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        self.window = ctk.CTk()
        self.window.title("Convertisseur Audio")
        
        # Plein écran
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        self.window.geometry(f"{screen_w}x{screen_h}+0+0")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Container principal centré
        container = ctk.CTkFrame(self.window, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Titre
        ctk.CTkLabel(
            container,
            text="Convertisseur Texte → Audio",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=(0, 40))
        
        # Zone de drop / sélection fichier
        file_frame = ctk.CTkFrame(container, width=600, height=150, corner_radius=15)
        file_frame.pack(pady=(0, 20))
        file_frame.pack_propagate(False)
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="📂 Glissez-déposez un fichier ici\nou cliquez pour parcourir",
            font=ctk.CTkFont(size=16),
            text_color="gray60"
        )
        self.file_label.place(relx=0.5, rely=0.5, anchor="center")
        
        file_frame.bind("<Button-1>", lambda e: self.browse_file())
        self.file_label.bind("<Button-1>", lambda e: self.browse_file())
        
        # Nom du fichier sélectionné
        self.selected_file = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#2ecc71"
        )
        self.selected_file.pack(pady=(0, 30))
        
        # Options rapides
        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            options_frame,
            text="Moteur vocal :",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 15))
        
        self.engine_var = ctk.StringVar(value="pyttsx3")
        
        ctk.CTkRadioButton(
            options_frame, text="pyttsx3 (FR)", variable=self.engine_var,
            value="pyttsx3", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            options_frame, text="Google TTS", variable=self.engine_var,
            value="gtts", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        # Bouton principal
        self.convert_btn = ctk.CTkButton(
            container,
            text="Convertir en Audio",
            command=self.convert,
            width=300,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12
        )
        self.convert_btn.pack(pady=(0, 30))
        
        # Progression
        self.progress = ctk.CTkProgressBar(container, width=500)
        self.progress.pack(pady=(0, 30))
        self.progress.set(0)
        
        # Status
        self.status = ctk.CTkLabel(
            container,
            text="Prêt",
            font=ctk.CTkFont(size=13),
            text_color="gray60"
        )
        self.status.pack()
        
        self.file_path = None
    
    def log_status(self, message, color="gray60"):
        self.status.configure(text=message, text_color=color)
        self.window.update_idletasks()
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Documents", "*.pdf;*.txt;*.docx"),
                ("PDF", "*.pdf"),
                ("Texte", "*.txt"),
                ("Word", "*.docx")
            ]
        )
        if file_path:
            self.file_path = file_path
            self.selected_file.configure(text=f"📄 {Path(file_path).name}")
            self.log_status("Fichier sélectionné ✓", "#2ecc71")
    
    def convert(self):
        if not self.file_path:
            messagebox.showwarning("Erreur", "Sélectionnez un fichier d'abord")
            return
        
        if not os.path.exists(self.file_path):
            messagebox.showerror("Erreur", "Fichier introuvable")
            return
        
        self.convert_btn.configure(state="disabled", text="Conversion...")
        self.progress.set(0)
        
        thread = threading.Thread(target=self.process_file, daemon=True)
        thread.start()
    
    def process_file(self):
        try:
            file_path = self.file_path
            ext = Path(file_path).suffix.lower()
            output = str(Path(file_path).parent / f"{Path(file_path).stem}_audio.mp3")
            
            # Extraction
            self.log_status("📖 Lecture du document...", "#3498db")
            self.progress.set(0.2)
            
            if ext == '.txt':
                text = self.extract_txt(file_path)
            elif ext == '.pdf':
                text = self.extract_pdf(file_path)
            elif ext == '.docx':
                text = self.extract_docx(file_path)
            else:
                raise Exception("Format non supporté")
            
            if not text.strip():
                raise Exception("Aucun texte trouvé")
            
            # Synthèse vocale
            self.log_status("🎵 Synthèse vocale...", "#3498db")
            self.progress.set(0.6)
            
            engine = self.engine_var.get()
            if engine == "pyttsx3":
                self.pyttsx3_convert(text, output)
            else:
                self.gtts_convert(text, output)
            
            self.progress.set(1.0)
            self.log_status("✅ Conversion réussie !", "#2ecc71")
            
            self.window.after(0, lambda: self.on_complete(output))
            
        except Exception as e:
            self.log_status(f"❌ {str(e)}", "#e74c3c")
            self.window.after(0, lambda: self.on_error(str(e)))
    
    def extract_txt(self, path):
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(path, 'r', encoding=enc) as f:
                    return f.read()
            except:
                continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def extract_pdf(self, path):
        import PyPDF2
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages)
    
    def extract_docx(self, path):
        from docx import Document
        return "\n".join(p.text for p in Document(path).paragraphs)
    
    def pyttsx3_convert(self, text, output):
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 140)
        
        # Chercher voix française
        for voice in engine.getProperty('voices'):
            if any(x in voice.name.lower() or x in voice.id.lower() 
                   for x in ['french', 'fr', 'mb-fr']):
                engine.setProperty('voice', voice.id)
                break
        
        engine.save_to_file(text, output)
        engine.runAndWait()
    
    def gtts_convert(self, text, output):
        from gtts import gTTS
        tts = gTTS(text=text, lang='fr', slow=False, tld='fr')
        tts.save(output)
    
    def on_complete(self, output):
        self.convert_btn.configure(state="normal", text="Convertir en Audio")
        
        if messagebox.askyesno("Succès", "Fichier audio créé !\nVoulez-vous l'écouter ?"):
            try:
                if sys.platform == 'win32':
                    os.startfile(output)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', output])
                else:
                    subprocess.run(['xdg-open', output])
            except:
                pass
    
    def on_error(self, error):
        self.convert_btn.configure(state="normal", text="Convertir en Audio")
        self.progress.set(0)
        messagebox.showerror("Erreur", error)
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AudioConverter()
    app.run()
