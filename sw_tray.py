# System tray script for SoocerWorld Leipzig
# Developed by Stan Rode
import os
import threading
import tkinter as tk
from tkinter import simpledialog
import PIL.Image
import pystray
import asyncio
import edge_tts
import sys
import traceback
import pygame
import zeitansage
from deep_translator import MyMemoryTranslator
from zeitansage import ansage_ausfuehren

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SKRIPT_ORDNER, "sw_logo.png")
ANSAGE_FILE = os.path.join(SKRIPT_ORDNER, "ansage_tray.mp3")
LOG_FILE = os.path.join(SKRIPT_ORDNER, "error_tray.log")
GONG_FILE = os.path.join(SKRIPT_ORDNER, "gong_sw_tray.mp3")

image = (
    PIL.Image.open(IMAGE_PATH)
    .convert("RGBA")
    .resize((64, 64), PIL.Image.Resampling.LANCZOS)
)

def speak(text):
    """Spielt den angegebenen Text mit einem Gong davor ab"""
    voice = "de-DE-KatjaNeural"
    async def generate_speech(text):
        translator = MyMemoryTranslator(source="de-DE", target="en-US")
        text = text + " " + translator.translate(text)
        communicate = edge_tts.Communicate(
            text=text, voice=voice, pitch="+5Hz", rate="-6%", volume="-60%"
        )
        await communicate.save(ANSAGE_FILE)

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )
        asyncio.run(generate_speech(text))
    except Exception:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Fehler bei TTS: \n{traceback.format_exc()}\n")
        return

    try:
        pygame.mixer.init()

        if os.path.exists(GONG_FILE):
            zeitansage.play_audio(GONG_FILE)

        if os.path.exists(ANSAGE_FILE):
            zeitansage.play_audio(ANSAGE_FILE)

        pygame.mixer.quit()
    except Exception:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Fehler bei Audiowiedergabe: \n{traceback.format_exc()}\n")
    finally:
        # Temporäre Datei immer löschen
        if os.path.exists(ANSAGE_FILE):
            try:
                os.remove(ANSAGE_FILE)
            except OSError:
                pass

def say_time(icon, item):
    """Ansage der aktuellen Zeit"""
    threading.Thread(
       target=ansage_ausfuehren, kwargs={"force": True}, daemon=True
   ).start()

def leave_court(icon, item):
    """Ansage zum Verlassen des Feldes. Mittels item wird die Feld Nummer übergeben"""
    if str(item) == "Pepsi":
        threading.Thread(
            target=speak, args={"Bitte das kleine Feld verlassen!"}, daemon=True
        ).start()
    else:
        threading.Thread(
            target=speak, args={f"Bitte Feld {item} verlassen!"}, daemon=True
        ).start()

def beenden(icon, item):
    icon.stop()

def custom_text(icon, item):
    """Ansage einen individuellen Textes, welcher vorher abgefragt wird"""
    def open_dialog():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        user_input = simpledialog.askstring(
            title="SoccerWorld Durchsage",
            prompt="Welche Durchsage soll gesprochen werden?",
            parent=root,
        )

        root.destroy()

        if user_input:
            speak(user_input)

    threading.Thread(target=open_dialog, daemon=True).start()

def ballplaying(icon, item):
    """Ansage zum Ballspielverbot außerhalb der Felder"""
    speak("Achtung! Das Ballspielen ist nur auf unseren Spielfeldern erlaubt!")


icon = pystray.Icon(
    "SoccerWorld",
    image,
    title="SoccerWorld Zeitsage",
    menu=pystray.Menu(
        pystray.MenuItem("Zeitansage abspielen", say_time),
        pystray.MenuItem("Feld verlassen", pystray.Menu(
            pystray.MenuItem("1", leave_court),
            pystray.MenuItem("2", leave_court),
            pystray.MenuItem("3", leave_court),
            pystray.MenuItem("4", leave_court),
            pystray.MenuItem("5", leave_court),
            pystray.MenuItem("6", leave_court),
            pystray.MenuItem("7", leave_court),
            pystray.MenuItem("8", leave_court),
            pystray.MenuItem("9", leave_court),
            pystray.MenuItem("Pepsi", leave_court),
        )),
        pystray.MenuItem("Ballspielen", ballplaying),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Manuelle Ansage", custom_text),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", beenden),
    ),
)

icon.run()