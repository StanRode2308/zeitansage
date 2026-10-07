# System tray script for SoocerWorld Leipzig
# Developed by Stan Rode
import os
import threading
import tkinter as tk
from tkinter import simpledialog
import customtkinter as ctk
from tkinter import messagebox
import PIL.Image
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
THEME_BG = "#fff4ec"
THEME_FG = "#4a2c2a"
THEME_ACCENT = "#e07a5f"
THEME_ACCENT_FG = "#ffffff"
THEME_FIELD_BG = "#ffffff"
THEME_FONT_FAMILY = "Georgia"
THEME_FONT_SIZE = 10
audio_lock = threading.Lock()

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

def apply_theme(root):
    """Apply the project theme to a window. CustomTkinter styles per widget,
    so the widgets themselves carry the rest of the colours."""
    root.configure(fg_color=THEME_BG)

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
        root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.optionmenu_color_var = tk.StringVar()
        self.optionmenu_color_var.set("Keine")

        self.label1 = ctk.CTkLabel(root, text="Bitte Informationen über das Fahrzeug angeben!", font=ctk.CTkFont(family="Helvetica", size=15, weight="bold"), text_color=THEME_FG, width=300, height=70)
        self.label1.place(x=260, y=10)

        self.Brand = ctk.CTkEntry(root, fg_color=THEME_FIELD_BG, text_color=THEME_FG, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=THEME_FONT_SIZE), width=130, height=30)
        self.Brand.place(x=210, y=134)
        ToolTip(self.Brand, "Automarke")

        self.w_Brand = ctk.CTkLabel(root, text="Marke", text_color=THEME_FG, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=THEME_FONT_SIZE), width=40, height=20)
        self.w_Brand.place(x=210, y=114)

        self.w_Color = ctk.CTkLabel(root, text="Farbe", text_color=THEME_FG, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=THEME_FONT_SIZE), width=40, height=20)
        self.w_Color.place(x=480, y=110)

        self.optionmenu_color = ctk.CTkOptionMenu(root, values=["Keine", "Weiß", "Gelb", "Orange", "Rot", "Lila / Violett", "Blau", "Grün", "Grau", "Braun", "Schwarz"], variable=self.optionmenu_color_var, fg_color=THEME_ACCENT, text_color=THEME_ACCENT_FG, width=150, height=28)
        self.optionmenu_color.place(x=480, y=130)
        ToolTip(self.optionmenu_color, "Farbe angeben")

        self.separator2 = ctk.CTkFrame(root, corner_radius=0, fg_color="gray70", width=800, height=20)
        self.separator2.place(x=0, y=190)

        self.label5 = ctk.CTkLabel(root, text="Kennzeichen", font=ctk.CTkFont(family="Helvetica", size=11, weight="bold"), text_color=THEME_FG, width=130, height=30)
        self.label5.place(x=345, y=210)

        # Kept on self, or Python garbage-collects it and the image goes blank.
        self.image2_image = ctk.CTkImage(PIL.Image.open("kennzeichen.png"), size=(250, 55))
        self.image2 = ctk.CTkLabel(root, text="", image=self.image2_image)
        self.image2.place(x=290, y=263)

        self.entry4 = ctk.CTkEntry(root, placeholder_text="L", fg_color=THEME_FIELD_BG, text_color=THEME_FG, font=ctk.CTkFont(family="Helvetica", size=21), width=50, height=40)
        self.entry4.place(x=330, y=271)

        self.entry7 = ctk.CTkEntry(root, placeholder_text="KC 946", font=ctk.CTkFont(family="Helvetica", size=21), fg_color=THEME_FIELD_BG, text_color=THEME_FG, width=120, height=40)
        self.entry7.place(x=410, y=271)

        self.submit = ctk.CTkButton(root, text="Ausrufen", command=self.on_submit, fg_color=THEME_ACCENT, text_color=THEME_ACCENT_FG, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=THEME_FONT_SIZE), width=96, height=32)
        self.submit.place(x=360, y=390)

    def hide_window(self):
        """Versteckt das Fenster unsichtbar im Hintergrund."""
        self.root.withdraw()

    def reset_fields(self):
        """Leert alle Eingabefelder, damit das Fenster beim nächsten Öffnen frisch ist."""
        self.Brand.delete(0, tk.END)
        self.optionmenu_color_var.set("Keine")
        self.entry4.delete(0, tk.END)
        self.entry7.delete(0, tk.END)

    def on_submit(self):
        brand = self.Brand._entry.get()
        color = self.optionmenu_color.get()
        front_part = self.entry4._entry.get()
        last_part = self.entry7._entry.get()
        pattern = r"^([A-ZÄÖÜ]{1,3})([A-Z]{1,2})([1-9][0-9]{0,3})([EH]?)$"
        match_check = (front_part + last_part).upper().replace(" ", "").replace("-", "")

        def throw_error_no_license():
            messagebox.showerror("Fehler!",
                                 "Es wurde kein Kennzeichen angegeben!",
                                 parent=self.root)
            return

        if front_part == self.entry4._placeholder_text:
            throw_error_no_license()
            return

        if last_part == self.entry7._placeholder_text:
            throw_error_no_license()
            return

        match = re.match(pattern, match_check)
        if not match:
            throw_error_no_license()
            return



        def cleanup_entry(front_part, last_part):
            brand.replace(" ", "")
            front_part.strip()
            last_part.strip()
            front_part = front_part.upper().replace(" ", "")
            last_part = last_part.upper().replace(" ", "").replace("-", " ")

            front_part = " ,".join(list(front_part))
            last_part = " ,".join(list(last_part))

            if brand == "" and color== "Keine":
                speech_text = (
                    f"Achtung! Der Fahrer des Wagens mit dem amtlichen Kennzeichen: "
                    f"{front_part},  Trennung, {last_part}, "
                    "bitte schnell an der Rezeption melden!"
                )

            elif brand == "":
                speech_text = (
                    f"Achtung! Der Fahrer des Wagens mit der Farbe: {color} und dem amtlichen Kennzeichen: "
                    f"{front_part},  Trennung, {last_part}, "
                    "bitte schnell an der Rezeption melden!"
                )

            elif color == "Keine":
                speech_text = (
                    f"Achtung! Der Fahrer des {brand}s mit dem amtlichen Kennzeichen: "
                    f"{front_part},  Trennung, {last_part}, "
                    "bitte schnell an der Rezeption melden!"
                )
            else:
                speech_text = (
                    f"Achtung! Der Fahrer des {brand}s mit der Farbe: {color} und dem amtlichen Kennzeichen: "
                    f"{front_part},  Trennung, {last_part}, "
                    "bitte schnell an der Rezeption melden!"
                )

            speak(speech_text, "-40%", Gong.NORMAL, translation=False)

            self.hide_window()
        cleanup_entry(front_part, last_part)

def speak(text, volume, gong: Gong, translation: bool = True):
    """Spielt den angegebenen Text mit einem Gong davor ab"""
    with audio_lock:
        voice = "de-DE-KatjaNeural"
        async def generate_speech(text):
            if translation:
                translator = MyMemoryTranslator(source="de-DE", target="en-US")
                text = text + ". " + translator.translate(text)
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
    """Ansage zum Verlassen des Feldes. Mittels item wird die Feldnummer übergeben"""
    if str(item) == "Pepsi":
        text = "Bitte das kleine Feld verlassen!"
    else:
        text= f"Bitte Feld {item} verlassen!"

    threading.Thread(
        target=speak,
        args=(text, "-40%", Gong.NORMAL),
        daemon=True
    ).start()

def beenden(icon, item):
    icon.stop()
    main_root.quit()
    sys.exit(0)

def custom_text(icon, item):
    """Ansage eines individuellen Textes, welcher vorher abgefragt wird"""

    def open_dialog():
        dialog_parent = tk.Toplevel(main_root)
        dialog_parent.withdraw()
        dialog_parent.attributes("-topmost", True)

        user_input = simpledialog.askstring(
            title="SoccerWorld Durchsage",
            prompt="Welche Durchsage soll gesprochen werden?",
            parent=dialog_parent,
        )
        dialog_parent.destroy()

        if user_input == "67" or " 6 7 " or "six seven" or "sixseven":
            messagebox.showwarning(title="Nope", message="Nice Try ;)")
            return

        if user_input:
            threading.Thread(
                target=speak,
                args=(user_input, "-40%", Gong.NORMAL),
                daemon=True
            ).start()
    main_root.after(0, open_dialog)

def ballplaying(icon, item):
    """Ansage zum Ballspielverbot außerhalb der Felder"""
    text = "Achtung! Das Ballspielen ist nur auf unseren Spielfeldern erlaubt!"
    threading.Thread(
        target=speak,
        args=(text, "-40%", Gong.NORMAL),
        daemon=True
    ).start()

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

ctk.set_appearance_mode("light")
main_root = ctk.CTk()
main_root.withdraw()

app_window = ctk.CTkToplevel(main_root)
app = Application(app_window)
app_window.withdraw()

def open_license_window():
    """Wird vom Main-Thread ausgeführt: Felder leeren und Fenster zeigen."""
    app.reset_fields()
    app_window.deiconify()
    app_window.focus()

def custom_license_plate(icon, item):
    """Sagt der GUI aus dem Tray-Thread sicher Bescheid, dass sie sich zeigen soll."""
    main_root.after(0, open_license_window)
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

threading.Thread(target=icon.run, daemon=True).start()
threading.Thread(target=automatic_time, daemon=True).start()

main_root.mainloop()