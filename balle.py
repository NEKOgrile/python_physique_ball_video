import pygame
from pygame.math import Vector2

# ========== CONFIGURATION ==========
# Couleurs
BLUE  = (100, 150, 255)
RED   = (255,  80,  80)

# Balle
GRAVITY        = 500
BALL_RADIUS    = 15
RESTITUTION    = 1.0
MAX_SPEED      = 800
BOOST_FACTOR   = 1.5
BOOST_DURATION = 0.2

class Balle:
    def __init__(self, x, y, radius, color):
        self.pos    = Vector2(x, y)
        self.vel    = Vector2(0, 0)
        self.radius = radius
        self.color  = color

        self.mass        = radius
        self.restitution = RESTITUTION

        self.is_boosting = False
        self.boost_timer = 0.0
        self.can_boost   = True

        # Squash and stretch
        self.scale          = Vector2(1, 1)
        self.target_scale   = Vector2(1, 1)
        self.scale_timer    = 0.0
        self.scale_duration = 0.2

    def clamp_velocity(self):
        speed = self.vel.length()
        if speed > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

    def draw(self, surface):
        scaled_radius_x = int(self.radius * self.scale.x)
        scaled_radius_y = int(self.radius * self.scale.y)

        # Fond blanc (halo)
        pygame.draw.ellipse(surface, (255, 255, 255),
            pygame.Rect(0, 0, scaled_radius_x * 2 + 8, scaled_radius_y * 2 + 8).move(
                self.pos.x - scaled_radius_x - 4, self.pos.y - scaled_radius_y - 4)
        )

        # Balle colorée
        pygame.draw.ellipse(surface, self.color,
            pygame.Rect(0, 0, scaled_radius_x * 2, scaled_radius_y * 2).move(
                self.pos.x - scaled_radius_x, self.pos.y - scaled_radius_y)
        )

    def update(self, dt):
        self.vel.y += GRAVITY * dt
        self.clamp_velocity()

        facteur = BOOST_FACTOR if self.is_boosting else 1.0
        self.pos += self.vel * facteur * dt

        if not self.can_boost:
            self.boost_timer -= dt
            if self.boost_timer <= 0:
                self.boost_timer = 0.0
                self.is_boosting = False
                self.can_boost   = True

        # Animation squash/stretch
        if self.scale_timer > 0:
            self.scale_timer -= dt
            t = max(0.0, 1.0 - (self.scale_timer / self.scale_duration))
            self.scale = Vector2(
                1 + (self.target_scale.x - 1) * (1 - t),
                1 + (self.target_scale.y - 1) * (1 - t)
            )
        else:
            self.scale = Vector2(1, 1)

    def check_bounce_edges(self, width, height):
        rebondi = False

        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -self.restitution
            rebondi = True
        elif self.pos.x + self.radius > width:
            self.pos.x = width - self.radius
            self.vel.x *= -self.restitution
            rebondi = True

        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -self.restitution
            rebondi = True
        elif self.pos.y + self.radius > height:
            self.pos.y = height - self.radius
            self.vel.y *= -self.restitution
            rebondi = True

        if rebondi:
            self.clamp_velocity()
            self.scale_timer  = self.scale_duration
            if abs(self.vel.y) > abs(self.vel.x):  # Rebond vertical
                self.target_scale = Vector2(1.4, 0.6)
            else:  # Rebond horizontal
                self.target_scale = Vector2(0.6, 1.4)

    def check_circle_collision(self, autre):
        offset  = self.pos - autre.pos
        dist_sq = offset.length_squared()
        rayon_min = self.radius + autre.radius

        if dist_sq < rayon_min ** 2:
            dist     = max(offset.length(), 1e-8)
            overlap  = rayon_min - dist
            normal   = offset.normalize()

            correction = normal * (overlap / 2)
            self.pos  += correction
            autre.pos -= correction

            rel_vel = self.vel - autre.vel
            vel_norm = rel_vel.dot(normal)

            if vel_norm < 0:
                impulse = (2 * vel_norm) / (self.mass + autre.mass)
                self.vel  -= impulse * autre.mass * normal
                autre.vel += impulse * self.mass     * normal

                self.clamp_velocity()
                autre.clamp_velocity()

                if self.can_boost:
                    self.is_boosting  = True
                    self.can_boost    = False
                    self.boost_timer  = BOOST_DURATION

                if autre.can_boost:
                    autre.is_boosting  = True
                    autre.can_boost    = False
                    autre.boost_timer  = BOOST_DURATION

                # Squash/stretch sur collision entre balles
                self.scale_timer  = self.scale_duration
                self.target_scale = Vector2(1.4, 0.6)

                autre.scale_timer  = autre.scale_duration
                autre.target_scale = Vector2(1.4, 0.6)

    def check_wall_cercle_collision(self, cercle):
        return cercle.check_wall_cercle_collision(self)
