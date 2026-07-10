#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de packaging pour VisionLab.exe avec gestion des grosses dépendances.
Placez ce script à la racine du projet, activez votre venv et exécutez-le.
"""

import os
import sys
import shutil
from pathlib import Path
import PyInstaller.__main__

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
APP_NAME = "VisionLab"
MAIN_SCRIPT = "main.py"
ICON_PNG = Path("assets/logos/icon.png")
ICON_ICO = Path("assets/logos/icon.ico")
ASSETS_DIR = Path("assets")
MODELS_DIR = Path("models")          # Dossier des modèles ONNX/PKL
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")

# ----------------------------------------------------------------------
# Stratégie de packaging
# ----------------------------------------------------------------------
# On utilise --onedir (pas --onefile) pour les gros frameworks, car --onefile
# peut échouer à cause de la taille et des fichiers extraits en mémoire.
USE_ONEFILE = False   # Mettre à True si vous voulez tenter un seul exe (risqué)

# ----------------------------------------------------------------------
# Modules à exclure (uniquement ceux vraiment inutiles)
# On retire tensorflow, torch, matplotlib, pandas des exclusions car ils sont
# nécessaires à l'application.
# ----------------------------------------------------------------------
EXCLUDE_MODULES = [
    "tkinter", "jupyter", "IPython", "notebook",
    "PyQt5", "wx", "gtk", "PySide2", "PyQt6",
    "tensorboard", "sympy", "numba",
    "distutils", "setuptools", "pip",  # inutiles en runtime
]

# ----------------------------------------------------------------------
# Collecter entièrement ces paquets (pour éviter les imports manquants)
# ----------------------------------------------------------------------
COLLECT_ALL = [
    "onnxruntime", "supervision", "sklearn", "imagehash",
    "PIL", "scipy", "matplotlib", "tensorflow", "keras",
    "torch", "torchvision", "ultralytics", "transformers",
    "tokenizers", "safetensors", "huggingface_hub",
    "pandas",  # parfois utilisé par supervision ou d'autres
    "cv2", "numpy", "PySide6",
    "aiohttp", "qrcode", "pyngrok", "joblib",
    "onnx", "onnxruntime", "tf2onnx",
    "scikit_learn", "threadpoolctl", "filelock",
]

# ----------------------------------------------------------------------
# Imports cachés (pour les modules chargés dynamiquement)
# ----------------------------------------------------------------------
HIDDEN_IMPORTS = [
    # PySide6
    "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
    "PySide6.QtSvg", "PySide6.QtNetwork",
    # Ultralytics / YOLO
    "ultralytics.utils", "ultralytics.models", "ultralytics.data",
    "ultralytics.engine", "ultralytics.trackers",
    # Supervision
    "supervision.annotators", "supervision.detection", "supervision.utils",
    # Transformers / HuggingFace
    "transformers.models", "transformers.tokenization_utils",
    "huggingface_hub.file_download", "huggingface_hub.snapshot_download",
    # TensorFlow / Keras
    "tensorflow.python", "keras.saving", "keras.models",
    # PyTorch
    "torch._C", "torch.nn", "torch.optim",
    # ONNX
    "onnxruntime.capi", "onnxruntime.training",
    # Scikit-learn
    "sklearn.utils", "sklearn.ensemble", "sklearn.tree",
    # Autres
    "pandas._libs", "matplotlib.backends", "matplotlib.pyplot",
]

# ----------------------------------------------------------------------
def clean():
    for folder in [BUILD_DIR, DIST_DIR]:
        if folder.exists():
            try:
                shutil.rmtree(folder)
                print(f"🧹 Nettoyé : {folder}/")
            except PermissionError:
                print(f"⚠️ Impossible de supprimer {folder}/ (fichier verrouillé).")
            except Exception as e:
                print(f"⚠️ Erreur lors du nettoyage : {e}")

def check_env():
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ L'environnement virtuel ne semble pas activé.")

def prepare_icon():
    if ICON_ICO.exists():
        return str(ICON_ICO)
    if ICON_PNG.exists():
        try:
            from PIL import Image
            img = Image.open(ICON_PNG).convert('RGBA')
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            ICON_ICO.parent.mkdir(parents=True, exist_ok=True)
            img.save(ICON_ICO, format='ICO')
            print(f"✅ Icône créée : {ICON_ICO}")
            return str(ICON_ICO)
        except Exception as e:
            print(f"❌ Impossible de convertir l'icône : {e}")
    print("⚠️ Aucune icône trouvée.")
    return None

def collect_assets_data():
    datas = []
    if ASSETS_DIR.exists():
        for path in ASSETS_DIR.rglob("*"):
            if path.is_file():
                rel = path.relative_to(ASSETS_DIR)
                datas.append((str(path), str(Path("assets") / rel)))
        print(f"📁 Assets inclus : {len(datas)} fichiers")
    return datas

def build():
    # Nettoyer les builds précédents
    clean()

    icon = prepare_icon()
    assets_data = collect_assets_data()

    args = [
        MAIN_SCRIPT,
        f"--name={APP_NAME}",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--log-level=WARN",
    ]

    if USE_ONEFILE:
        args.append("--onefile")
    else:
        args.append("--onedir")  # recommandé pour les gros projets

    if icon:
        args.append(f"--icon={icon}")

    # Ajouter les assets
    for src, dst in assets_data:
        args.append(f"--add-data={src}{os.pathsep}{dst}")

    # Ajouter les modèles externes (copiés dans le dossier de l'exe)
    if MODELS_DIR.exists():
        for model_file in MODELS_DIR.rglob("*"):
            if model_file.is_file():
                rel = model_file.relative_to(MODELS_DIR.parent)  # on garde la structure models/
                args.append(f"--add-data={str(model_file)}{os.pathsep}{str(rel.parent)}")
        print(f"📦 Modèles inclus depuis {MODELS_DIR}")

    # Exclusions
    for mod in EXCLUDE_MODULES:
        args.append(f"--exclude-module={mod}")

    # Imports cachés
    for imp in HIDDEN_IMPORTS:
        args.append(f"--hidden-import={imp}")

    # Collecte complète
    for pkg in COLLECT_ALL:
        args.append(f"--collect-all={pkg}")

    # Options supplémentaires pour les gros paquets
    args.append("--collect-submodules=torch")
    args.append("--collect-submodules=tensorflow")
    args.append("--collect-submodules=transformers")
    args.append("--collect-submodules=ultralytics")

    # Éviter de copier les fichiers .pyc inutiles
    args.append("--no-pyc")

    print("🔨 Lancement de PyInstaller avec les options :")
    print(" ".join(args))
    print("-" * 80)

    PyInstaller.__main__.run(args)

    # Vérification
    exe_dir = DIST_DIR / APP_NAME
    if exe_dir.exists():
        print(f"✅ Dossier de l'application créé : {exe_dir}")
        # Optionnel : afficher la taille totale
        total_size = sum(f.stat().st_size for f in exe_dir.rglob('*') if f.is_file())
        print(f"📦 Taille totale : {total_size / (1024**2):.1f} MB")
    else:
        print("❌ Le dossier de sortie n'a pas été créé.")

if __name__ == "__main__":
    print("=" * 60)
    print(f"🐟 BUILD {APP_NAME} (grosses dépendances intégrées)")
    print("=" * 60)
    check_env()
    build()
    print("\n📌 Prochaine étape : créez un installeur Inno Setup avec VisionLab_Setup.iss")