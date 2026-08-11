#Script for Time Saying in Soocerworld Leipzig
#Developed by Stan Rode
import asyncio
import datetime
import os
import sys
import traceback

import edge_tts
import pygame

now = datetime.datetime.now()
weekday = now.weekday()
hour = now.hour

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
GONG_FILE = os.path.join(SKRIPT_ORDNER, "gong_sw.mp3")
ANSAGE_FILE = os.path.join(SKRIPT_ORDNER, "ansage.mp3")
LOG_FILE = os.path.join(SKRIPT_ORDNER, "error.log")

isTime = True
if 0<=weekday<=4:
    if 1<= hour <=9:
        isTime = False
else:
    if 0<=hour <=9 or 22<= hour <=23:
        isTime = False

if not isTime:
    sys.exit()

if now.minute == 00 and now.hour != 0:
    TEXT = now.strftime("Es ist %H Uhr.")
elif now.hour == 0 and now.minute == 00:
    TEXT = "Es ist jetzt 24 Uhr."
else:
    TEXT = now.strftime("Es ist %H Uhr %M.")
VOICE = "de-DE-KatjaNeural"

async def generate_speech():
    communicate = edge_tts.Communicate(text=TEXT, voice=VOICE, pitch="+5Hz", rate="-6%", volume="-60%")
    await communicate.save(ANSAGE_FILE)

try:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(generate_speech())
except Exception as e:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"Fehler aufgetreten: \n {traceback.format_exc()}\n")
    sys.exit(1)

asyncio.run(generate_speech())

pygame.mixer.init()

def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

if os.path.exists(GONG_FILE):
    play_audio(GONG_FILE)

play_audio(ANSAGE_FILE)
pygame.mixer.quit()

if os.path.exists(ANSAGE_FILE):
    os.remove(ANSAGE_FILE)
