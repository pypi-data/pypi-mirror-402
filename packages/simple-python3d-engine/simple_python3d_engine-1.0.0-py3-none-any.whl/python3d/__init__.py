"""
Python3D - Простая 3D библиотека для PyGame
"""

__version__ = "1.0.0"

# Импорт модулей
from .physic import PhysicObject, PhysicsWorld
from .particles import Particle, ParticleSystem
from .sound import SoundEngine

__all__ = [
    'PhysicObject',
    'PhysicsWorld', 
    'Particle',
    'ParticleSystem',
    'SoundEngine',
]