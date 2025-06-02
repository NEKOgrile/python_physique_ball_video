import pygame
import math
from pygame.math import Vector2
from midi_manager import MidiManager

# Couleurs
BLUE  = (100, 150, 255)
RED   = (255,  80,  80)

# Arcs
RAYON_DEPART      = 100
ECART_RAYON       = 12
OUVERTURE_DEGREES = 300


class ArcCircle:
    def __init__(self, center, radius, start_angle, end_angle, color, width=4, midi_manager=None):
        self.center = Vector2(center)
        self.radius = radius
        self.start_angle = start_angle % (2 * math.pi)
        self.end_angle   = end_angle   % (2 * math.pi)
        self.color = color
        self.width = width
        self.broken = False
        self.midi_manager = midi_manager  # ✅ Ajout obligatoire



    def rotate(self, dt):
        rotation_speed = math.radians(25)
        self.start_angle = (self.start_angle - rotation_speed * dt) % (2 * math.pi)
        self.end_angle   = (self.end_angle   - rotation_speed * dt) % (2 * math.pi)

    def shrink(self, dt):
        if not self.broken and self.radius > RAYON_DEPART:
            self.radius -= 200 * dt
            if self.radius < RAYON_DEPART:
                self.radius = RAYON_DEPART

    def draw(self, surface):
        if self.broken or self.radius > 800:
            return
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = (int(self.center.x), int(self.center.y))
        pygame.draw.arc(surface, self.color, rect,
                        self.start_angle, self.end_angle, self.width)

    def is_in_hole(self, pos):
        dx = pos.x - self.center.x
        dy = self.center.y - pos.y
        angle = math.atan2(dy, dx) % (2 * math.pi)
        start = self.start_angle
        end = self.end_angle
        if start < end:
            in_drawn = (start <= angle <= end)
        else:
            in_drawn = (angle >= start or angle <= end)
        return not in_drawn
    

    def check_wall_cercle_collision(self, balle):
        if self.broken:
            return False

        offset = balle.pos - self.center
        distance = offset.length()

        if distance + balle.radius > self.radius:
            if self.is_in_hole(balle.pos):
                self.broken = True
                return True
            else:
                normal = offset.normalize()
                balle.vel = balle.vel.reflect(normal) * balle.restitution
                overlap = (distance + balle.radius) - self.radius
                balle.pos -= normal * overlap

                if self.midi_manager:
                    self.midi_manager.play_next_note()

        return False

