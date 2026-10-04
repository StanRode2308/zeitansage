# System tray script for SoocerWorld Leipzig
# Developed by Stan Rode
import os
import threading
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
from tkinter import messagebox
import PIL.Image
from PIL import ImageTk
import pystray
import asyncio
import re

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


class ToolTip:
    """Small hover tooltip. tkinter has no built-in one."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip = None
        self._job = None
        # add="+" so this never replaces bindings the widget already has.
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._job = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._job is not None:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self):
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        # No title bar or border — it should look like a tooltip, not a window.
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=3,
        ).pack()

    def _hide(self, _event=None):
        self._cancel()
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


class Application:
    def __init__(self, root):
        self.root = root
        root.title("Kennzeichen ausrufen")
        root.geometry("800x500")
        root.update_idletasks()
        root.geometry(
            f"+{(root.winfo_screenwidth() - 800) // 2}"
            f"+{(root.winfo_screenheight() - 500) // 2}"
        )

        self.optionmenu_color_var = tk.StringVar()
        self.optionmenu_color_var.set("Weiß")
        self.switch2_var = tk.IntVar()
        self.switch3_var = tk.IntVar()

        self.label1 = tk.Label(root, text="Bitte Informationen über das Fahrzeug angeben!", font=("Helvetica", 15, "bold"))
        self.label1.place(x=260, y=10, width=300, height=70)

        self.Brand = tk.Entry(root)
        self.Brand.place(x=210, y=134, width=130, height=20)
        ToolTip(self.Brand, "Automarke")

        self.w_Brand = tk.Label(root, text="Marke")
        self.w_Brand.place(x=210, y=114, width=40, height=20)

        self.w_Color = tk.Label(root, text="Farbe")
        self.w_Color.place(x=480, y=110, width=40, height=20)

        self.optionmenu_color = tk.OptionMenu(root, self.optionmenu_color_var, "Weiß", "Gelb", "Orange", "Rot", "Lila / Violett", "Blau", "Grün", "Grau", "Braun", "Schwarz")
        self.optionmenu_color.place(x=480, y=130, width=150, height=28)
        ToolTip(self.optionmenu_color, "Farbe angeben")

        self.switch2 = tk.Checkbutton(root, text="Enabled", variable=self.switch2_var, command=self.brand_switch)
        self.switch2.place(x=220, y=154, width=120, height=28)

        self.switch3 = tk.Checkbutton(root, text="Enabled", variable=self.switch3_var, command=self.color_switch)
        self.switch3.place(x=480, y=160, width=150, height=30)

        self.separator2 = ttk.Separator(root, orient="horizontal")
        self.separator2.place(x=0, y=190, width=800, height=20)

        self.label5 = tk.Label(root, text="Kennzeichen", font=("Helvetica", 11, "bold"))
        self.label5.place(x=345, y=210, width=130, height=30)

        # Kept on self, or Python garbage-collects it and the image goes blank.
        self.image2_image = ImageTk.PhotoImage(PIL.Image.open("kennzeichen.png").resize((250, 55)))
        self.image2 = tk.Label(root, image=self.image2_image)
        self.image2.place(x=290, y=263, width=250, height=55)

        self.entry4 = tk.Entry(root)
        self.entry4.place(x=315, y=271, width=50, height=40)

        self.entry7 = tk.Entry(root)
        self.entry7.place(x=410, y=270, width=120, height=40)

    def brand_switch(self):
        pass

    def color_switch(self):
        pass


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
    speak("Achtung! Das Ballspielen ist nur auf unseren Spielfeldern erlaubt!", "", Gong.NORMAL)

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

def custom_license_plate(icon, item):
    """Öffnet ein GUI-Eingabefenster für Kennzeichen und schließt es nach Absenden direkt wieder."""

    root = tk.Tk()
    app = Application(root)
    root.mainloop()
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
        pystray.MenuItem("Kennzeichen ausrufen", custom_license_plate),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", beenden),
    ),
)

threading.Thread(target=automatic_time, daemon=True).start()
icon.run()