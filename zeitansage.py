# Script for Time Saying in Soccerworld Leipzig
# Developed by Stan Rode
import asyncio
import datetime
import os
import sys
import traceback
import edge_tts
import pygame

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
GONG_FILE = os.path.join(SKRIPT_ORDNER, "gong_sw.mp3")
ANSAGE_FILE = os.path.join(SKRIPT_ORDNER, "ansage.mp3")
LOG_FILE = os.path.join(SKRIPT_ORDNER, "error.log")


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

    # Zeitfenster prüfen (wird bei force=True übersprungen)
    if not force and not ist_im_zeitfenster(now):
        return

    # Text formatieren
    if now.minute == 0 and now.hour != 0:
        text = now.strftime("Es ist %H Uhr.")
    elif now.hour == 0 and now.minute == 0:
        text = "Es ist jetzt 24 Uhr."
    else:
        text = now.strftime("Es ist %H Uhr %M.")

    voice = "de-DE-KatjaNeural"

    async def generate_speech():
        communicate = edge_tts.Communicate(
            text=text, voice=voice, pitch="+5Hz", rate="-6%", volume="-60%"
        )
        await communicate.save(ANSAGE_FILE)

    # Audio erzeugen
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )
        asyncio.run(generate_speech())
    except Exception:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Fehler bei TTS: \n{traceback.format_exc()}\n")
        return

    # Audio abspielen
    try:
        pygame.mixer.init()

        if os.path.exists(GONG_FILE):
            play_audio(GONG_FILE)

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


if __name__ == "__main__":
    ansage_ausfuehren(force=False)