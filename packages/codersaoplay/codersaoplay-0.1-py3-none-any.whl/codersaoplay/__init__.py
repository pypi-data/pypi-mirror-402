import sys
from .core import play

class _CodersaoPlay:
    def __call__(self, mp3_file):
        play(mp3_file)

# Replace module with callable object
sys.modules[__name__] = _CodersaoPlay()
