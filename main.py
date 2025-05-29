import pygame
from pygame.math import Vector2
import math
import random

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Simulation de balle physique")
clock = pygame.time.Clock()

class WallCercle:
    def __init__(self, x, y, radius, color, width, base_angle, rotation_speed, hole_opening_angle_rad):
        self.pos = Vector2(x, y)
        self.radius = radius
        self.color = color
        self.width = width
        self.broken = False
        self.base_angle = base_angle
        self.rotation_speed = rotation_speed
        self.hole_opening_angle = hole_opening_angle_rad
        self.time = 0

    def is_in_hole(self, pos):
        vect = Vector2(pos) - self.pos
        angle = math.atan2(vect.y, vect.x)
        if angle < 0:
            angle += 2 * math.pi

        hole_start = (self.base_angle + self.time * self.rotation_speed) % (2 * math.pi)
        hole_end = (hole_start + self.hole_opening_angle) % (2 * math.pi)

        if hole_start > hole_end:
            return angle >= hole_start or angle <= hole_end
        else:
            return hole_start <= angle <= hole_end

    def update(self, dt):
        self.time += dt
        if self.broken:
            return

        if not cercle_min_atteint:
            if self.radius > 100:
                self.radius -= 100 * dt
            if self.radius < 100:
                self.radius = 100

    def draw(self, surface):
        if self.broken:
            return

        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius), self.width)

        hole_start = (self.base_angle + self.time * self.rotation_speed) % (2 * math.pi)
        hole_end = (hole_start + self.hole_opening_angle) % (2 * math.pi)

        start_deg = math.degrees(hole_start)
        end_deg = math.degrees(hole_end)
        if end_deg < start_deg:
            end_deg += 360

        points = [self.pos]
        for angle_deg in range(int(start_deg), int(end_deg) + 1):
            angle_rad = math.radians(angle_deg % 360)
            x = self.pos.x + self.radius * math.cos(angle_rad)
            y = self.pos.y + self.radius * math.sin(angle_rad)
            points.append(Vector2(x, y))

        if len(points) >= 3:
            pygame.draw.polygon(surface, (30, 30, 30), points)

class Balle:
    def __init__(self, x, y, radius, color):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.mass = radius
        self.restitution = 1
        self.boost_timer = 0
        self.boost_duration = 0.2
        self.boost_elapsed = 0.0
        self.boost_speed_increase = 1.5

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius + 6)
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def update(self, dt):
        g = 500.0
        self.vel.y += g * dt

        boost_factor = 1.0
        if self.boost_timer > 0:
            self.boost_elapsed += dt
            if self.boost_elapsed <= self.boost_duration:
                boost_factor = self.boost_speed_increase
            else:
                time_after = self.boost_elapsed - self.boost_duration
                if time_after <= 0.5:
                    boost_factor = self.boost_speed_increase - (self.boost_speed_increase - 1) * (time_after / 0.5)
                else:
                    self.boost_timer = 0
                    self.boost_elapsed = 0
            self.boost_timer -= dt

        self.pos += self.vel * boost_factor * dt

    def check_bounce_edges(self, width, height):
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -self.restitution
        elif self.pos.x + self.radius > width:
            self.pos.x = width - self.radius
            self.vel.x *= -self.restitution
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -self.restitution
        elif self.pos.y + self.radius > height:
            self.pos.y = height - self.radius
            self.vel.y *= -self.restitution
            if abs(self.vel.y) < 50:
                self.vel.y = -50

    def check_circle_collision(self, autre):
        offset = self.pos - autre.pos
        dist_sq = offset.length_squared()
        rayon_min = self.radius + autre.radius
        if dist_sq < rayon_min ** 2:
            dist = max(offset.length(), 1e-8)
            overlap = rayon_min - dist
            correction = offset.normalize() * (overlap / 2)
            self.pos += correction
            autre.pos -= correction
            normal = offset.normalize()
            rel_vel = self.vel - autre.vel
            vel_norm = rel_vel.dot(normal)
            if vel_norm < 0:
                impulse = (2 * vel_norm) / (self.mass + autre.mass)
                self.vel -= impulse * autre.mass * normal
                autre.vel += impulse * self.mass * normal

                if self.boost_timer <= 0:
                    self.boost_timer = 0.5
                    self.boost_elapsed = 0

                if autre.boost_timer <= 0:
                    autre.boost_timer = 0.5
                    autre.boost_elapsed = 0

    def check_wall_cercle_collision(self, cercle):
        if cercle.broken:
            return

        offset = self.pos - cercle.pos
        distance = offset.length()

        if distance + self.radius > cercle.radius:
            if cercle.is_in_hole(self.pos):
                cercle.broken = True
            else:
                normal = offset.normalize()
                self.vel = self.vel.reflect(normal) * self.restitution
                overlap = distance + self.radius - cercle.radius
                self.pos -= normal * overlap

nombre_cercles = 100
rayon_depart = 300
ecart_rayon = 12
hole_opening = math.radians(60)
rotation_speed = math.radians(20)
angle_offset = hole_opening * 0.1
cercle_min_atteint = False

Cercles = []
for i in range(nombre_cercles):
    rayon = rayon_depart + i * ecart_rayon
    base_angle = i * angle_offset
    cercle = WallCercle(WIDTH // 2, HEIGHT // 2, rayon, (255, 255, 255), 4, base_angle, rotation_speed, hole_opening)
    Cercles.append(cercle)

balle1 = Balle(WIDTH // 2 - 100, HEIGHT // 4, 30, (200, 50, 50))
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 4, 30, (50, 50, 200))
balles = [balle1, balle2]

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
            running = False

    screen.fill((30, 30, 30))
    cercle_min_atteint = any(not c.broken and c.radius <= 225 for c in Cercles)

    for Cercle in reversed(Cercles):
        Cercle.update(dt)
        if not Cercle.broken:
            Cercle.draw(screen)

    for i, b in enumerate(balles):
        b.update(dt)
        b.check_bounce_edges(WIDTH, HEIGHT)
        for cercle in Cercles:
            b.check_wall_cercle_collision(cercle)
        for autre in balles[i + 1:]:
            b.check_circle_collision(autre)
        b.draw(screen)

    pygame.display.flip()

pygame.quit()
