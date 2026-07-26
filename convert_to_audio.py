#!/usr/bin/env python3
"""
Convertisseur Texte → Audio - Kali Linux Edition
Simple, robuste, avec fallback automatique
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
import tempfile

def extract_text_from_txt(filepath):
    """Extrait le texte d'un fichier TXT"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except:
            continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_text_from_pdf(filepath):
    """Extrait le texte d'un fichier PDF"""
    import PyPDF2
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

def extract_text_from_docx(filepath):
    """Extrait le texte d'un fichier DOCX"""
    from docx import Document
    doc = Document(filepath)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def text_to_speech_gtts(text, output, lang='fr'):
    """Conversion avec Google TTS (qualité supérieure)"""
    from gtts import gTTS
    print("🌐 Synthèse avec Google TTS...")
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output)
    return True

def text_to_speech_pyttsx3(text, output, rate=150):
    """Conversion avec pyttsx3 (hors ligne)"""
    import pyttsx3
    print("🔊 Synthèse avec pyttsx3 (hors ligne)...")
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'fr' in voice.id.lower() or 'french' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            print(f"   Voix: {voice.name}")
            break
    
    engine.save_to_file(text, output)
    engine.runAndWait()
    return True

def text_to_speech_espeak(text, output, lang='fr', speed=150):
    """Conversion avec espeak (toujours disponible)"""
    print("🔊 Synthèse avec espeak (mode secours)...")
    espeak_speed = int(speed * 1.2)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text)
        temp_text = f.name
    
    # Essayer avec mbrola pour meilleure qualité
    cmd_mbrola = ['espeak-ng', '-v', f'mb-{lang}1', '-s', str(espeak_speed), 
                  '-w', output, '-f', temp_text]
    cmd_standard = ['espeak-ng', '-v', f'{lang}', '-s', str(espeak_speed), 
                    '-w', output, '-f', temp_text]
    
    # Essayer d'abord mbrola, puis standard
    for cmd in [cmd_mbrola, cmd_standard]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            os.unlink(temp_text)
            return True
    
    os.unlink(temp_text)
    return False

def convert_to_mp3(wav_file, mp3_file):
    """Convertit WAV en MP3 avec ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-i', wav_file, '-acodec', 'libmp3lame', 
                       '-q:a', '2', mp3_file, '-y'], 
                      capture_output=True, check=True)
        os.unlink(wav_file)
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='🔊 Convertisseur de fichiers texte en audio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s document.pdf                    # Conversion automatique
  %(prog)s document.txt -o audio.mp3       # Sortie personnalisée
  %(prog)s document.docx -m gtts           # Forcer Google TTS
  %(prog)s document.pdf -m pyttsx3 -r 180  # Vitesse personnalisée
  %(prog)s document.txt -m espeak          # Mode secours garanti
        """
    )
    
    parser.add_argument('input', help='Fichier à convertir (.txt, .pdf, .docx)')
    parser.add_argument('-o', '--output', help='Fichier audio de sortie (défaut: .mp3)')
    parser.add_argument('-m', '--method', 
                       choices=['auto', 'gtts', 'pyttsx3', 'espeak'],
                       default='auto', 
                       help='Méthode de synthèse (défaut: auto)')
    parser.add_argument('-l', '--lang', default='fr', help='Langue (défaut: fr)')
    parser.add_argument('-r', '--rate', type=int, default=150, 
                       help='Vitesse de parole, 80-450 (défaut: 150)')
    
    args = parser.parse_args()
    
    # Vérifier le fichier d'entrée
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Erreur: Fichier introuvable: {args.input}")
        sys.exit(1)
    
    # Déterminer le fichier de sortie
    if args.output:
        output_path = args.output
    else:
        output_path = str(input_path.parent / f"{input_path.stem}_audio.mp3")
    
    # Extraire le texte
    print(f"\n📖 Lecture de: {input_path.name}")
    ext = input_path.suffix.lower()
    
    try:
        if ext == '.txt':
            text = extract_text_from_txt(input_path)
        elif ext == '.pdf':
            text = extract_text_from_pdf(input_path)
        elif ext == '.docx':
            text = extract_text_from_docx(input_path)
        else:
            print(f"❌ Format non supporté: {ext}")
            print("   Formats acceptés: .txt, .pdf, .docx")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur d'extraction: {e}")
        sys.exit(1)
    
    if not text or not text.strip():
        print("❌ Aucun texte trouvé dans le fichier")
        sys.exit(1)
    
    print(f"✅ {len(text)} caractères extraits\n")
    
    # Préparer un fichier WAV temporaire pour espeak
    temp_wav = None
    if args.method in ['auto', 'espeak']:
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    
    # Conversion
    print("🎵 Génération audio...")
    success = False
    method_used = ""
    
    if args.method == 'auto':
        # Essayer gTTS (internet), puis pyttsx3, puis espeak
        try:
            import socket
            socket.create_connection(("www.google.com", 80), timeout=3)
            success = text_to_speech_gtts(text, output_path if output_path.endswith('.mp3') else output_path, args.lang)
            method_used = "Google TTS"
        except:
            print("⚠️  Pas de connexion internet, tentative hors ligne...")
        
        if not success:
            try:
                success = text_to_speech_pyttsx3(text, temp_wav if temp_wav else output_path, args.rate)
                if success and temp_wav:
                    if output_path.endswith('.mp3'):
                        convert_to_mp3(temp_wav, output_path)
                    else:
                        os.rename(temp_wav, output_path)
                method_used = "pyttsx3"
            except Exception as e:
                print(f"⚠️  pyttsx3 a échoué: {e}")
        
        if not success:
            success = text_to_speech_espeak(text, temp_wav if temp_wav else output_path, args.lang, args.rate)
            if success and temp_wav:
                if output_path.endswith('.mp3'):
                    convert_to_mp3(temp_wav, output_path)
                else:
                    os.rename(temp_wav, output_path)
            method_used = "espeak-ng"
    
    elif args.method == 'gtts':
        success = text_to_speech_gtts(text, output_path, args.lang)
        method_used = "Google TTS"
    
    elif args.method == 'pyttsx3':
        success = text_to_speech_pyttsx3(text, temp_wav, args.rate)
        if success and output_path.endswith('.mp3'):
            convert_to_mp3(temp_wav, output_path)
        elif success:
            os.rename(temp_wav, output_path)
        method_used = "pyttsx3"
    
    elif args.method == 'espeak':
        success = text_to_speech_espeak(text, temp_wav, args.lang, args.rate)
        if success and output_path.endswith('.mp3'):
            convert_to_mp3(temp_wav, output_path)
        elif success:
            os.rename(temp_wav, output_path)
        method_used = "espeak-ng"
    
    # Nettoyage
    if temp_wav and os.path.exists(temp_wav):
        try:
            os.unlink(temp_wav)
        except:
            pass
    
    # Résultat
    if success:
        print(f"\n{'='*50}")
        print(f"✅ Conversion réussie avec {method_used}!")
        print(f"📁 Fichier: {output_path}")
        print(f"📏 Taille: {os.path.getsize(output_path) / 1024:.1f} Ko")
        print(f"{'='*50}")
        
        # Suggérer la lecture
        print("\n💡 Pour écouter:")
        if subprocess.run(['which', 'mpg123'], capture_output=True).returncode == 0:
            print(f"   mpg123 {output_path}")
        elif subprocess.run(['which', 'ffplay'], capture_output=True).returncode == 0:
            print(f"   ffplay {output_path}")
        else:
            print(f"   sudo apt install mpg123  # Installation du lecteur")
    else:
        print("\n❌ Échec de la conversion")
        print("💡 Vérifiez les logs ou essayez une autre méthode: -m espeak")
        sys.exit(1)

if __name__ == "__main__":
    main()
