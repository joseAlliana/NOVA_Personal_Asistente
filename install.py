#!/usr/bin/env python3
"""
install.py — Instalador inteligente de Nova Personal Assistant
Detecta el sistema operativo e instala las dependencias correctas.

Uso:
  python install.py          # instalación completa
  python install.py --check  # solo verificar dependencias
"""

import sys
import os
import subprocess
import shutil
import argparse

# ─── Colores ANSI ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"{GREEN}  ✓{RESET} {msg}")
def warn(msg): print(f"{YELLOW}  ⚠{RESET} {msg}")
def err(msg):  print(f"{RED}  ✗{RESET} {msg}")
def info(msg): print(f"{CYAN}  →{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{CYAN}{msg}{RESET}")

# ─── Detectar plataforma ─────────────────────────────────────────────────────

def detect_platform() -> str:
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    else:
        return "linux"

PLATFORM = detect_platform()

# ─── Requisitos base (todas las plataformas) ─────────────────────────────────

BASE_REQUIREMENTS = [
    "openai>=1.0.0",
    "edge-tts>=6.1.9",
    "SpeechRecognition",
    "python-dotenv",
    "duckduckgo-search",
    "pyautogui",
    "Pillow",
    "requests",
    "numpy",
    "mem0ai",
    "qdrant-client",
    "groq",
    "anthropic",
]

# PyAudio y playsound son opcionales - requieren compilación en Windows
OPTIONAL_REQUIREMENTS = {
    "macos": ["PyAudio"],
    "windows": ["PyAudio"],
    "linux": ["PyAudio"],
}

# ─── Requisitos por plataforma ───────────────────────────────────────────────

PLATFORM_REQUIREMENTS = {
    "macos": [
        "rumps",           # menu bar macOS
        "PyQtWebEngine",   # HUD Qt
        "PyQt5",
        "gtts",
    ],
    "windows": [
        "PyQt5",
        "pywin32",         # winreg, COM
        "pycaw",           # control de volumen Windows
        "comtypes",        # pycaw dep
        "pyperclip",       # portapapeles cross-platform
        "sounddevice",     # grabación de audio (alternativa a PyAudio, sin compilación)
        "numpy",           # requerido por sounddevice para audio
    ],
    "linux": [
        "PyQt5",
        "pyperclip",       # portapapeles (requiere xclip/xsel instalado)
        "pygame",          # audio fallback
    ],
}

# ─── Deps de sistema (no-pip) ────────────────────────────────────────────────

SYSTEM_DEPS = {
    "macos":   [],         # macOS ya tiene say, afplay, screencapture, osascript
    "windows": [],         # PowerShell tiene todo lo necesario (SAPI, etc.)
    "linux":   [
        ("espeak-ng", "sudo apt install espeak-ng  # TTS voz"),
        ("mpg123",    "sudo apt install mpg123       # reproducción MP3"),
        ("xclip",     "sudo apt install xclip         # portapapeles"),
        ("scrot",     "sudo apt install scrot          # capturas de pantalla (alternativa: gnome-screenshot)"),
    ],
}

# ─── Checks de versión ───────────────────────────────────────────────────────

def check_python_version() -> bool:
    v = sys.version_info
    if v >= (3, 10):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    err(f"Python {v.major}.{v.minor} — se requiere Python 3.10+")
    return False


def check_pip() -> bool:
    if shutil.which("pip") or shutil.which("pip3"):
        ok("pip disponible")
        return True
    err("pip no encontrado — instalar manualmente")
    return False


def check_ollama() -> bool:
    if shutil.which("ollama"):
        ok("Ollama detectado")
        return True
    warn("Ollama no instalado — Nova funcionará con Groq/OpenRouter (requiere internet)")
    info("Instalar Ollama (para modo local): https://ollama.ai")
    return False


def check_system_deps() -> None:
    deps = SYSTEM_DEPS.get(PLATFORM, [])
    if not deps:
        return
    header("Dependencias de sistema")
    for binary, install_cmd in deps:
        if shutil.which(binary):
            ok(f"{binary} disponible")
        else:
            warn(f"{binary} no encontrado — instalar con: {install_cmd}")


def check_env_file() -> bool:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    example_path = os.path.join(os.path.dirname(__file__), ".env.example")
    if os.path.exists(env_path):
        ok(".env encontrado")
        return True
    if os.path.exists(example_path):
        warn(".env no encontrado — copiando .env.example")
        import shutil as _sh
        _sh.copy(example_path, env_path)
        warn("Editá .env y agrega tus API keys (GROQ_API_KEY, OPENROUTER_API_KEY)")
        return True
    warn(".env no encontrado y no hay .env.example — creá uno manualmente")
    return False

# ─── Instalación ─────────────────────────────────────────────────────────────

def pip_install(packages: list[str], optional: bool = False) -> bool:
    if not packages:
        return True
    
    # Si es Windows e intentamos instalar PyAudio, intentar con versión precompilada
    if PLATFORM == "windows" and "PyAudio" in packages:
        warn("PyAudio requiere compilación en Windows. Intentando versión precompilada...")
        packages = [p for p in packages if p != "PyAudio"]
        
        # Intentar descargar wheel precompilado
        try:
            import struct
            bits = 64 if struct.calcsize("P") * 8 == 64 else 32
            py_version = f"{sys.version_info.major}{sys.version_info.minor}"
            wheel_name = f"PyAudio-0.2.13-cp{py_version}-cp{py_version}-win_amd64.whl"
            
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--only-binary", ":all:", "PyAudio"]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                warn("No se pudo instalar PyAudio precompilado. Será opcional.")
        except:
            warn("No se pudo instalar PyAudio. Será opcional.")
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *packages]
    result = subprocess.run(cmd)
    
    if result.returncode != 0 and optional:
        warn("Algunas dependencias opcionales fallaron (pueden usarse alternativas)")
        return True  # No fallar para dependencias opcionales
    
    return result.returncode == 0


def install_all() -> None:
    header(f"Instalando Nova — plataforma detectada: {PLATFORM.upper()}")

    # 1. Requisitos base
    header("Dependencias base (todas las plataformas)")
    info(f"Instalando {len(BASE_REQUIREMENTS)} paquetes...")
    if pip_install(BASE_REQUIREMENTS):
        ok("Dependencias base instaladas")
    else:
        err("Algunas dependencias base fallaron — revisá el output")

    # 2. Requisitos de plataforma
    plat_deps = PLATFORM_REQUIREMENTS.get(PLATFORM, [])
    if plat_deps:
        header(f"Dependencias {PLATFORM.upper()}")
        info(f"Instalando {len(plat_deps)} paquetes específicos...")
        if pip_install(plat_deps, optional=True):
            ok(f"Dependencias {PLATFORM} instaladas")
        else:
            warn(f"Algunas dependencias {PLATFORM} fallaron (pueden ser opcionales)")

    # 2b. Requisitos opcionales (con mejor manejo de errores)
    opt_deps = OPTIONAL_REQUIREMENTS.get(PLATFORM, [])
    if opt_deps:
        header("Dependencias opcionales (pueden fallar - es OK)")
        info(f"Intentando instalar {len(opt_deps)} paquetes opcionales...")
        pip_install(opt_deps, optional=True)

    # 3. Deps de sistema
    check_system_deps()

    # 4. .env
    header("Configuración")
    check_env_file()

    # 5. Ollama (opcional)
    header("Dependencias opcionales")
    check_ollama()
    
    # 6. Post-install de pywin32 en Windows (requerido para winreg)
    if PLATFORM == "windows":
        try:
            info("Ejecutando post-install de pywin32...")
            subprocess.run([sys.executable, "-m", "pip", "show", "pywin32"], 
                          capture_output=True, check=True)
            # Si pywin32 está instalado, ejecutar post-install
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pywin32"],
                          capture_output=False)
        except:
            pass

    # ── Crear lanzador en el escritorio ─────────────────────────────────────
    create_desktop_launcher()

    # ── Resumen final ───────────────────────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"{BOLD}Nova listo para usar.{RESET}")
    print()
    print("Siguientes pasos:")
    if PLATFORM == "macos":
        print("  1. Editá .env y configurá tus API keys")
        print("  2. chmod +x launch_nova.sh")
        print("  3. ./launch_nova.sh   (o hacer doble clic en el lanzador de Nova en el escritorio)")
    elif PLATFORM == "windows":
        print("  1. Editá .env y configurá tus API keys")
        print("  2. python main.py      (o hacer doble clic en el lanzador de Nova en el escritorio)")
        print("  3. Usa 'nova' en PowerShell/CMD (requiere reiniciar la terminal)")
    else:
        print("  1. Editá .env y configurá tus API keys")
        print("  2. python main.py      (o hacer doble clic en el lanzador de Nova en el escritorio)")
    print()


def create_desktop_launcher() -> None:
    """Crear lanzador en el escritorio para ejecutar Nova."""
    if PLATFORM == "windows":
        try:
            header("Launcher de escritorio")
            # Rutas del sistema Windows
            import winreg
            
            desktop_path = None
            try:
                # Obtener ruta del Escritorio del usuario
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
                    desktop_path = winreg.QueryValueEx(key, 'Desktop')[0]
            except:
                # Fallback: usar variables de entorno
                desktop_path = os.path.expanduser("~\\Desktop")
            
            if not os.path.exists(desktop_path):
                warn(f"No se encontró Escritorio en {desktop_path}")
                return
            
            # Crear archivo .bat para lanzar Nova
            nova_root = os.path.dirname(os.path.abspath(__file__))
            bat_path = os.path.join(desktop_path, "Nova.bat")
            
            bat_content = f"""@echo off
REM Launcher de Nova Personal Assistant
cd /d "{nova_root}"
python main.py
pause
"""
            
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat_content)
            
            ok(f"Launcher creado en Escritorio: Nova.bat")
            
            # Agregar al PATH para que se pueda ejecutar `nova` desde terminal
            python_dir = os.path.dirname(sys.executable)
            
            # Crear script nova.py en Scripts de Python
            scripts_dir = os.path.join(python_dir, "Scripts")
            nova_script = os.path.join(scripts_dir, "nova.py")
            nova_cmd = os.path.join(scripts_dir, "nova.cmd")
            
            nova_script_content = f"""#!/usr/bin/env python
import sys
import os

# Agregar directorio del proyecto al path
project_root = r"{nova_root}"
sys.path.insert(0, os.path.join(project_root, 'src'))

from nova.cli.repl import main

if __name__ == '__main__':
    main()
"""
            
            # Contenido del archivo .cmd para que PowerShell lo ejecute
            nova_cmd_content = f"""@echo off
REM Wrapper para ejecutar nova desde terminal
"{sys.executable}" "{nova_script}" %*
"""
            
            try:
                os.makedirs(scripts_dir, exist_ok=True)
                with open(nova_script, 'w', encoding='utf-8') as f:
                    f.write(nova_script_content)
                
                # Crear archivo .cmd para Windows CMD/PowerShell
                with open(nova_cmd, 'w', encoding='utf-8') as f:
                    f.write(nova_cmd_content)
                
                ok(f"Comando 'nova' disponible desde terminal")
                info("  (reinicia PowerShell/CMD para que surta efecto)")
            except Exception as e:
                warn(f"No se pudo crear comando 'nova' en Scripts: {e}")
                
        except Exception as e:
            warn(f"Error creando launcher de escritorio: {e}")
    
    elif PLATFORM == "macos":
        try:
            header("Launcher de escritorio")
            desktop = os.path.expanduser("~/Desktop")
            app_name = "Nova Personal Assistant"
            
            # Crear app alias en macOS
            nova_root = os.path.dirname(os.path.abspath(__file__))
            launcher_script = os.path.join(desktop, f"{app_name}.command")
            
            script_content = f"""#!/bin/bash
cd "{nova_root}"
python main.py
"""
            
            with open(launcher_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            os.chmod(launcher_script, 0o755)
            ok(f"Launcher creado en Escritorio: {app_name}.command")
            
        except Exception as e:
            warn(f"Error creando launcher de escritorio: {e}")


def check_only() -> None:
    header(f"Verificando instalación — {PLATFORM.upper()}")
    ok_py = check_python_version()
    ok_pip = check_pip()
    check_ollama()
    check_system_deps()
    check_env_file()

    # Verificar imports críticos
    header("Módulos Python")
    critical = ["openai", "speech_recognition", "dotenv", "edge_tts"]
    for mod in critical:
        try:
            __import__(mod)
            ok(mod)
        except ImportError:
            err(f"{mod} — ejecutá: python install.py")

    print()


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instalador de Nova Personal Assistant")
    parser.add_argument("--check", action="store_true", help="Solo verificar dependencias")
    args = parser.parse_args()

    if args.check:
        check_only()
    else:
        install_all()
