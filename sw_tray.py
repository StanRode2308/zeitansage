# System tray script for SoocerWorld Leipzig
# Developed by Stan Rode
import os
import threading
import tkinter as tk
from tkinter import simpledialog
import PIL.Image
import pystray
import asyncio

from Xlib.protocol.rq import Bool

import edge_tts
import datetime
import time
import sys
import traceback
import pygame
from deep_translator import MyMemoryTranslator
from enum import Enum

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SKRIPT_ORDNER, "sw_logo.png")
ANSAGE_FILE = os.path.join(SKRIPT_ORDNER, "ansage_tray.mp3")
LOG_FILE = os.path.join(SKRIPT_ORDNER, "error_tray.log")
letzte_ansage_minute = -1

class Gong(Enum):
    NORMAL = os.path.join(SKRIPT_ORDNER, "gong_sw_tray.mp3")
    TIME = os.path.join(SKRIPT_ORDNER, "gong_sw.mp3")

image = (
    PIL.Image.open(IMAGE_PATH)
    .convert("RGBA")
    .resize((64, 64), PIL.Image.Resampling.LANCZOS)
)

def speak(text, volume, gong: Gong, translation: bool = True):
    """Spielt den angegebenen Text mit einem Gong davor ab"""
    voice = "de-DE-KatjaNeural"
    async def generate_speech(text):
        if translation:
            translator = MyMemoryTranslator(source="de-DE", target="en-US")
            text = text + " " + translator.translate(text)
        communicate = edge_tts.Communicate(
            text=text, voice=voice, pitch="+5Hz", rate="-6%", volume=volume
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

        if os.path.exists(gong.value):
            play_audio(gong.value)

        if os.path.exists(ANSAGE_FILE):
            play_audio(ANSAGE_FILE)

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
        speak("Bitte das kleine Feld verlassen!", "-40%", Gong.NORMAL)
    else:
        speak(f"Bitte Feld {item} verlassen!", "-40%", Gong.NORMAL)

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
            speak(user_input, "-40%", Gong.NORMAL)

    threading.Thread(target=open_dialog, daemon=True).start()

def ballplaying(icon, item):
    """Ansage zum Ballspielverbot außerhalb der Felder"""
    speak("Achtung! Das Ballspielen ist nur auf unseren Spielfeldern erlaubt!", "-40%", Gong.NORMAL)

def automatic_time():
    """Startet die Schleife zum automatischen Ausführen aller halben Stunde"""
    while True:
        global letzte_ansage_minute
        while True:
            jetzt = datetime.datetime.now()

            if jetzt.minute in (0, 30) and jetzt.minute != letzte_ansage_minute:
                ansage_ausfuehren(force=False)
                letzte_ansage_minute = jetzt.minute

            if jetzt.minute not in (0, 30):
                letzte_ansage_minute = -1

            time.sleep(5)


def ist_im_zeitfenster(jetzt: datetime.datetime) -> bool:
    """Prüft, ob der Zeitpunkt im erlaubten Zeitfenster liegt."""
    weekday = jetzt.weekday()
    hour = jetzt.hour

    if 0 <= weekday <= 4:
        # Mo - Fr: 10:00 bis 00:00 Uhr
        if 1 <= hour <= 9:
            return False
    else:
        # Sa - So: 10:00 bis 21:00 Uhr
        if 0 <= hour <= 9 or 22 <= hour <= 23:
            return False
    return True


def play_audio(file_path: str):
    """Spielt eine einzelne Audiodatei über Pygame ab."""
    if not os.path.exists(file_path):
        return
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def ansage_ausfuehren(force: bool = False):
    """Erzeugt und spielt die Zeitansage ab."""
    now = datetime.datetime.now()

    if not force and not ist_im_zeitfenster(now):
        return

    if now.minute == 0 and now.hour != 0:
        text = now.strftime("Es ist %H Uhr.")
    elif now.hour == 0 and now.minute == 0:
        text = "Es ist jetzt 24 Uhr."
    else:
        text = now.strftime("Es ist %H Uhr %M.")
    speak(text, "-60%", Gong.TIME, False)

#--------------------------------------------------------------------------------------------------------#
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

threading.Thread(target=automatic_time, daemon=True).start()
icon.run()