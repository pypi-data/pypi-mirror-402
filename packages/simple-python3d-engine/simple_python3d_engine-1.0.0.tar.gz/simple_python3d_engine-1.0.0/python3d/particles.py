import random
import pygame

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, 0)
        self.life = 1.0
        self.color = (
            random.randint(200, 255),
            random.randint(100, 200),
            random.randint(50, 100)
        )
        self.size = random.randint(2, 6)
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= 0.02 * dt
        return self.life > 0

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, count=30):
        for _ in range(count):
            self.particles.append(Particle(x, y))
    
    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, surface):
        for p in self.particles:
            alpha = int(p.life * 255)
            color = (*p.color[:3], alpha)
            s = pygame.Surface((p.size*2, p.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p.size, p.size), p.size)
            surface.blit(s, (p.x - p.size, p.y - p.size))