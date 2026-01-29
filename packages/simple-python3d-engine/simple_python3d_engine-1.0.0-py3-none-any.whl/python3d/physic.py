import math

class PhysicObject:
    def __init__(self, x, y, mass=1.0):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.mass = mass
        self.gravity = 0.5
    
    def add_force(self, fx, fy):
        self.vx += fx / self.mass
        self.vy += fy / self.mass
    
    def update(self, dt):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.98
        self.vy *= 0.98

class PhysicsWorld:
    def __init__(self):
        self.objects = []
        self.gravity = 0.5
    
    def add(self, obj):
        self.objects.append(obj)
    
    def update_all(self, dt):
        for obj in self.objects:
            obj.update(dt)
            if obj.y > 10:
                obj.y = 10
                obj.vy = -obj.vy * 0.3