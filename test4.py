import pygame
import math
from pygame.math import Vector2

# ========== CONFIGURATION ==========
WIDTH, HEIGHT = 1080, 1080
FPS = 60
BG_COLOR = (20, 20, 30)
WHITE = (255, 255, 255)

# Couleurs
BLUE  = (100, 150, 255)
RED   = (255,  80,  80)

# Arcs
RAYON_DEPART      = 100
ECART_RAYON       = 12
OUVERTURE_DEGREES = 300  # 300° dessinés ⇒ 60° de trou

# Balle
GRAVITY             = 500
BALL_RADIUS         = 15
RESTITUTION         = 1.0

# ========== CLASSES ==========

class ArcCircle:
    def __init__(self, center, radius, start_angle, end_angle, color, width=4):
        self.center = Vector2(center)
        self.radius = radius
        self.start_angle = start_angle % (2 * math.pi)
        self.end_angle   = end_angle   % (2 * math.pi)
        self.color = color
        self.width = width
        self.broken = False

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
        if self.broken:
            return
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = (int(self.center.x), int(self.center.y))
        pygame.draw.arc(
            surface,
            self.color,
            rect,
            self.start_angle,
            self.end_angle,
            self.width
        )

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

                # 👇 AJOUTE ICI
                collision_sound.play()

        return False


class Balle:
    def __init__(self, x, y, radius, color):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.mass = radius
        self.restitution = RESTITUTION
        self.boost_timer = 0
        self.boost_duration = 0.2
        self.boost_elapsed = 0.0
        self.boost_speed_increase = 1.5

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            WHITE,
            (int(self.pos.x), int(self.pos.y)),
            self.radius + 6
        )
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.pos.x), int(self.pos.y)),
            self.radius
        )

    def update(self, dt):
        self.vel.y += GRAVITY * dt

        boost_factor = 1.0
        if self.boost_timer > 0:
            self.boost_elapsed += dt
            if self.boost_elapsed <= self.boost_duration:
                boost_factor = self.boost_speed_increase
            else:
                time_after = self.boost_elapsed - self.boost_duration
                if time_after <= 0.5:
                    boost_factor = self.boost_speed_increase - (
                        (self.boost_speed_increase - 1) * (time_after / 0.5)
                    )
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
        return cercle.check_wall_cercle_collision(self)

# ========== INITIALISATION PYGAME ==========
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deux Balles + Arcs")
clock = pygame.time.Clock()
pygame.mixer.init()



collision_sound = pygame.mixer.Sound("collision.wav")






center = (WIDTH // 2, HEIGHT // 2)

balle1 = Balle(WIDTH // 2 - 100, HEIGHT // 2, BALL_RADIUS, RED)
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 2, BALL_RADIUS, BLUE)
balle1.vel = Vector2(150, -200)
balle2.vel = Vector2(-150, -150)
balles = [balle1, balle2]

arcs = []
for i in range(100):
    start_deg = i * -5
    radius = RAYON_DEPART + i * ECART_RAYON
    start_rad = math.radians(start_deg)
    end_rad = math.radians(start_deg + OUVERTURE_DEGREES)
    color = [BLUE, RED, WHITE][i % 3]
    arcs.append(ArcCircle(center, radius, start_rad, end_rad, color))

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
           event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE
        ):
            running = False

    for b in balles:
        b.update(dt)
        b.check_bounce_edges(WIDTH, HEIGHT)

    balles[0].check_circle_collision(balles[1])

    for arc in arcs:
        arc.rotate(dt)

    any_at_min = any((not arc.broken and arc.radius <= RAYON_DEPART) for arc in arcs)
    if not any_at_min:
        for arc in arcs:
            arc.shrink(dt)

    for b in balles:
        for arc in arcs:
            arc.check_wall_cercle_collision(b)

    screen.fill(BG_COLOR)
    for arc in arcs:
        arc.draw(screen)
    for b in balles:
        b.draw(screen)
    pygame.display.flip()

pygame.quit()