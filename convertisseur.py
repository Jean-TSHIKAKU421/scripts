#!/usr/bin/env python3
"""
Convertisseur Texte → Audio - Version Compilable
"""

import sys
import os
import subprocess
import threading
import tempfile
from pathlib import Path
import time
import platform

# ===== FONCTIONS UTILITAIRES =====

def get_resource_path(relative_path):
    """Obtient le chemin absolu pour les ressources (pour PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def ensure_dependencies_silent():
    """Installe silencieusement les dépendances au premier lancement"""
    missing = []
    packages = {
        'PyPDF2': 'PyPDF2',
        'docx': 'python-docx',
        'pyttsx3': 'pyttsx3',
        'gtts': 'gTTS',
        'customtkinter': 'customtkinter',
        'PIL': 'Pillow'
    }
    
    for module, package in packages.items():
        try:
            if module == 'docx':
                import docx
            elif module == 'PIL':
                from PIL import Image
            else:
                __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        for package in missing:
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--user', package],
                    capture_output=True,
                    timeout=60
                )
            except:
                pass

# Installation silencieuse
if not getattr(sys, 'frozen', False):
    ensure_dependencies_silent()

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
        
        # Icône de l'application (si disponible)
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        self.file_path = None
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
        
        # Zone de sélection fichier
        file_frame = ctk.CTkFrame(container, width=600, height=150, corner_radius=15)
        file_frame.pack(pady=(0, 20))
        file_frame.pack_propagate(False)
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="📂 Cliquez pour sélectionner un fichier\nPDF, TXT ou DOCX",
            font=ctk.CTkFont(size=16),
            text_color="gray60"
        )
        self.file_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Rendre la zone cliquable
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
        
        # Options du moteur
        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            options_frame,
            text="Moteur vocal :",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 15))
        
        self.engine_var = ctk.StringVar(value="pyttsx3")
        
        ctk.CTkRadioButton(
            options_frame, text="pyttsx3 (Recommandé)", 
            variable=self.engine_var, value="pyttsx3", 
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            options_frame, text="Google TTS", 
            variable=self.engine_var, value="gtts", 
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=10)
        
        # Bouton principal
        self.convert_btn = ctk.CTkButton(
            container,
            text="🎯 Convertir en Audio",
            command=self.convert,
            width=350,
            height=60,
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
            text="Prêt à convertir",
            font=ctk.CTkFont(size=13),
            text_color="gray60"
        )
        self.status.pack()
    
    def log_status(self, message, color="gray60"):
        self.status.configure(text=message, text_color=color)
        self.window.update_idletasks()
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Sélectionner un document",
            filetypes=[
                ("Tous les documents", "*.pdf;*.txt;*.docx"),
                ("Fichiers PDF", "*.pdf"),
                ("Fichiers Texte", "*.txt"),
                ("Fichiers Word", "*.docx")
            ]
        )
        if file_path:
            self.file_path = file_path
            filename = Path(file_path).name
            self.selected_file.configure(text=f"📄 {filename}")
            self.log_status("Fichier sélectionné ✓", "#2ecc71")
    
    def convert(self):
        if not self.file_path:
            messagebox.showwarning("Aucun fichier", "Veuillez d'abord sélectionner un fichier à convertir.")
            return
        
        if not os.path.exists(self.file_path):
            messagebox.showerror("Erreur", "Le fichier sélectionné n'existe plus.")
            return
        
        self.convert_btn.configure(state="disabled", text="⏳ Conversion en cours...")
        self.progress.set(0)
        
        thread = threading.Thread(target=self.process_file, daemon=True)
        thread.start()
    
    def process_file(self):
        try:
            file_path = self.file_path
            ext = Path(file_path).suffix.lower()
            
            # Créer le chemin de sortie dans le même dossier
            output_dir = Path(file_path).parent
            output_name = f"{Path(file_path).stem}_audio.mp3"
            output_path = str(output_dir / output_name)
            
            # Extraction du texte
            self.log_status("📖 Lecture du document...", "#3498db")
            self.progress.set(0.2)
            
            if ext == '.txt':
                text = self.extract_txt(file_path)
            elif ext == '.pdf':
                text = self.extract_pdf(file_path)
            elif ext == '.docx':
                text = self.extract_docx(file_path)
            else:
                raise Exception(f"Format non supporté : {ext}")
            
            if not text or not text.strip():
                raise Exception("Aucun texte trouvé dans le document")
            
            # Synthèse vocale
            self.log_status("🎵 Génération audio...", "#3498db")
            self.progress.set(0.6)
            
            engine = self.engine_var.get()
            if engine == "pyttsx3":
                self.convert_pyttsx3(text, output_path)
            else:
                self.convert_gtts(text, output_path)
            
            self.progress.set(1.0)
            
            # Vérifier que le fichier a bien été créé
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                size_kb = os.path.getsize(output_path) / 1024
                self.log_status(f"✅ Conversion réussie ! ({size_kb:.1f} Ko)", "#2ecc71")
                self.window.after(0, lambda: self.on_complete(output_path))
            else:
                raise Exception("Le fichier audio n'a pas pu être créé")
            
        except Exception as e:
            error_msg = str(e)
            self.log_status(f"❌ {error_msg}", "#e74c3c")
            self.window.after(0, lambda: self.on_error(error_msg))
    
    def extract_txt(self, path):
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    text = f.read()
                    if text.strip():
                        return text
            except:
                continue
        # Dernier essai
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def extract_pdf(self, path):
        import PyPDF2
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = []
            total_pages = len(reader.pages)
            for i, page in enumerate(reader.pages):
                text_parts.append(page.extract_text())
                self.progress.set(0.2 + (0.3 * (i + 1) / total_pages))
            return "\n".join(text_parts)
    
    def extract_docx(self, path):
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    
    def convert_pyttsx3(self, text, output):
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 140)
        
        # Chercher la meilleure voix française
        voices = engine.getProperty('voices')
        french_voice = None
        
        for voice in voices:
            name = voice.name.lower()
            vid = voice.id.lower()
            if any(x in name or x in vid for x in ['french', 'français', 'fr', 'mb-fr']):
                french_voice = voice
                break
        
        if french_voice:
            engine.setProperty('voice', french_voice.id)
        
        engine.save_to_file(text, output)
        engine.runAndWait()
    
    def convert_gtts(self, text, output):
        from gtts import gTTS
        
        # Pour les longs textes, diviser en morceaux
        if len(text) > 5000:
            chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
            temp_files = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    tmp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    tts = gTTS(text=chunk, lang='fr', slow=False, tld='fr')
                    tts.save(tmp_file.name)
                    temp_files.append(tmp_file.name)
                    self.progress.set(0.6 + (0.3 * (i + 1) / len(chunks)))
            
            # Fusionner avec ffmpeg si disponible
            try:
                concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                for tmp in temp_files:
                    concat_file.write(f"file '{tmp}'\n")
                concat_file.close()
                
                subprocess.run(
                    ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file.name, 
                     '-c', 'copy', output, '-y'],
                    capture_output=True, timeout=60
                )
                
                os.unlink(concat_file.name)
                for tmp in temp_files:
                    os.unlink(tmp)
            except:
                # Si ffmpeg pas dispo, garder le premier chunk
                import shutil
                shutil.copy(temp_files[0], output)
                for tmp in temp_files:
                    os.unlink(tmp)
        else:
            tts = gTTS(text=text, lang='fr', slow=False, tld='fr')
            tts.save(output)
    
    def on_complete(self, output):
        self.convert_btn.configure(state="normal", text="🎯 Convertir en Audio")
        
        reponse = messagebox.askyesno(
            "✅ Conversion réussie !",
            f"Le fichier audio a été créé :\n\n{output}\n\nVoulez-vous l'écouter ?"
        )
        
        if reponse:
            try:
                system = platform.system()
                if system == 'Windows':
                    os.startfile(output)
                elif system == 'Darwin':
                    subprocess.run(['open', output])
                else:
                    subprocess.run(['xdg-open', output])
            except Exception as e:
                messagebox.showwarning("Erreur", f"Impossible de lire le fichier : {e}")
    
    def on_error(self, error):
        self.convert_btn.configure(state="normal", text="🎯 Convertir en Audio")
        self.progress.set(0)
        messagebox.showerror(
            "❌ Erreur de conversion",
            f"Une erreur est survenue :\n\n{error}\n\nVérifiez que le fichier est valide et réessayez."
        )
    
    def run(self):
        self.window.mainloop()

def main():
    try:
        app = AudioConverter()
        app.run()
    except Exception as e:
        # En cas d'erreur critique, afficher dans une boîte de dialogue
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Erreur critique",
            f"L'application n'a pas pu démarrer :\n\n{str(e)}\n\n"
            "Veuillez réinstaller l'application."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
