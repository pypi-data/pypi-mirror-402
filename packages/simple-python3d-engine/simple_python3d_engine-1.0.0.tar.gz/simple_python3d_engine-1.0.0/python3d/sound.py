import math
import pygame

class SoundEngine:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
    
    def load(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except:
            self.sounds[name] = None
    
    def play(self, name):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()