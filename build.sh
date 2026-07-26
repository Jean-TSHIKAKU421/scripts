#!/bin/bash
# Script de compilation automatique

echo "🔨 Compilation du Convertisseur Audio"
echo "===================================="

# Nettoyage
echo "🧹 Nettoyage des builds précédents..."
rm -rf build/ dist/ *.spec

# Installation de PyInstaller si nécessaire
pip install pyinstaller --quiet

# Options communes
COMMON_OPTS="--onefile --windowed --clean --noconfirm"

# Options spécifiques à l'OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Compilation pour Linux..."
    pyinstaller $COMMON_OPTS \
        --name "Convertisseur_Audio" \
        --hidden-import customtkinter \
        --hidden-import tkinter \
        --hidden-import PyPDF2 \
        --hidden-import docx \
        --hidden-import pyttsx3 \
        --hidden-import gtts \
        convertisseur.py
        
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Compilation pour macOS..."
    pyinstaller $COMMON_OPTS \
        --name "Convertisseur_Audio" \
        --hidden-import customtkinter \
        --hidden-import tkinter \
        --hidden-import PyPDF2 \
        --hidden-import docx \
        --hidden-import pyttsx3 \
        --hidden-import gtts \
        convertisseur.py
        
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "🪟 Compilation pour Windows..."
    pyinstaller $COMMON_OPTS \
        --name "Convertisseur_Audio" \
        --hidden-import customtkinter \
        --hidden-import tkinter \
        --hidden-import PyPDF2 \
        --hidden-import docx \
        --hidden-import pyttsx3 \
        --hidden-import gtts \
        convertisseur.py
fi

# Vérification
if [ -f "dist/Convertisseur_Audio" ] || [ -f "dist/Convertisseur_Audio.exe" ]; then
    echo ""
    echo "✅ Compilation réussie !"
    echo "📁 L'exécutable se trouve dans le dossier 'dist/'"
    
    # Afficher la taille
    if [ -f "dist/Convertisseur_Audio" ]; then
        SIZE=$(du -h "dist/Convertisseur_Audio" | cut -f1)
        echo "📏 Taille : $SIZE"
    fi
    
    # Créer un raccourci sur le bureau (Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        DESKTOP_FILE="$HOME/Desktop/Convertisseur_Audio.desktop"
        EXEC_PATH="$(pwd)/dist/Convertisseur_Audio"
        
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Convertisseur Audio
Comment=Convertissez vos documents en audio
Exec=$EXEC_PATH
Icon=audio-card
Terminal=false
Type=Application
Categories=Utility;Audio;
EOF
        chmod +x "$DESKTOP_FILE"
        echo "🔗 Raccourci bureau créé !"
    fi
else
    echo ""
    echo "❌ La compilation a échoué"
    exit 1
fi
