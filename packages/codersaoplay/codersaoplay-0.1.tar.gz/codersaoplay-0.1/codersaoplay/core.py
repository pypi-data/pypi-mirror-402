import pygame
import os
import time

pygame.mixer.init()

def play(mp3_file):
    if not os.path.exists(mp3_file):
        raise FileNotFoundError("MP3 file not found")

    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play()

    print("Playing:", mp3_file)
    print("Press Ctrl+C to stop")

    try:
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\nMusic stopped")
