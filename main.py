import pygame
from pygame.math import Vector2
import random
import math

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Simulation de balle physique")
clock = pygame.time.Clock()


class Spark:
    def __init__(self, pos):
        self.pos = Vector2(pos)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)
        self.vel = Vector2(speed * math.cos(angle), speed * math.sin(angle))
        self.life = 0.5
        self.radius = random.randint(2, 4)

    def update(self, dt):
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= 0.8

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / 0.5))
            color = (255, random.randint(100, 150), 0, alpha)
            spark_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(spark_surface, color, (self.radius, self.radius), self.radius)
            surface.blit(spark_surface, (self.pos.x - self.radius, self.pos.y - self.radius))


class WallCercle:
    def __init__(self, x, y, radius, color, width):
        self.pos = Vector2(x, y)
        self.radius = radius
        self.color = color
        self.width = width
        self.broken = False  # cercle intact au départ
        self.rotation_speed = 0.01  # radians par frame

        # définir le trou en angles radians
        self.hole_start_angle = math.radians(270)  # exemple trou entre 270° et 300°
        self.hole_end_angle = math.radians(300)

    def draw(self, surface):
        if self.broken:
            return

        # Dessine le cercle entier
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius, self.width)

        # Dessine le "trou" avec un polygone noir pour masquer la portion
        points = [self.pos]
        start_deg = math.degrees(self.hole_start_angle)
        end_deg = math.degrees(self.hole_end_angle)

        # Gère le cas où le trou dépasse 360° (boucle)
        if end_deg < start_deg:
            end_deg += 360

        step = 1  # degré
        for angle_deg in range(int(start_deg), int(end_deg)+1, step):
            angle_rad = math.radians(angle_deg % 360)
            x = self.pos.x + self.radius * math.cos(angle_rad)
            y = self.pos.y + self.radius * math.sin(angle_rad)
            points.append(Vector2(x, y))

        if len(points) >= 3:
            pygame.draw.polygon(surface, (30, 30, 30), points)  # couleur du fond

    def is_in_hole(self, pos):
        vect = Vector2(pos) - self.pos
        angle = math.atan2(vect.y, vect.x)
        if angle < 0:
            angle += 2 * math.pi

        # Cas spécial : le trou traverse 0 radians
        if self.hole_start_angle > self.hole_end_angle:
            return angle >= self.hole_start_angle or angle <= self.hole_end_angle
        else:
            return self.hole_start_angle <= angle <= self.hole_end_angle

    def update(self):
        self.hole_start_angle = (self.hole_start_angle + self.rotation_speed) % (2 * math.pi)
        self.hole_end_angle = (self.hole_end_angle + self.rotation_speed) % (2 * math.pi)


class Balle:
    def __init__(self, x, y, radius, color):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.mass = radius
        self.restitution = 1
        self.sparks = []
        self.boost_timer = 0
        self.boost_duration = 0.2
        self.boost_elapsed = 0.0
        self.boost_speed_increase = 1.5
        self.base_vel = Vector2(0, 0)  # vitesse sans boost

    def draw(self, surface):
        for spark in self.sparks:
            spark.draw(surface)

        if self.boost_timer > 0:
            alpha = int(128 + 127 * ((self.boost_timer % 0.5) * 2))
            halo_surface = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
            pygame.draw.circle(
                halo_surface,
                (self.color[0], self.color[1], self.color[2], alpha),
                (self.radius * 3, self.radius * 3),
                self.radius * 2
            )
            surface.blit(halo_surface, (self.pos.x - self.radius * 3, self.pos.y - self.radius * 3))

        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius + 6)
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def update(self, dt):
        g = 500.0
        self.vel.y += g * dt

        # Détermine facteur de boost (1 si pas de boost)
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

            # Mise à jour des étincelles
            for spark in self.sparks[:]:
                spark.update(dt)
                if spark.life <= 0:
                    self.sparks.remove(spark)

        # Mise à jour position avec facteur boost appliqué uniquement au déplacement
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

                # Active le boost si ce n'est pas déjà en cours
                if self.boost_timer <= 0:
                    self.boost_timer = 0.5
                    self.boost_elapsed = 0

                if autre.boost_timer <= 0:
                    autre.boost_timer = 0.5
                    autre.boost_elapsed = 0

                for _ in range(5):
                    self.sparks.append(Spark(self.pos))


    def check_wall_cercle_collision(self, cercle):
        if cercle.broken:
            return  # ne fait rien si le cercle est déjà cassé

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



# Valeurs initiales
nombre_cercles = 100
rayon_depart = 300
ecart_rayon = 20  # car 320 - 300 = 20 dans ton exemple


# Création des cercles avec écart constant
Cercles = []
for i in range(nombre_cercles):
    rayon = rayon_depart + i * ecart_rayon
    cercle = WallCercle(WIDTH // 2, HEIGHT // 2, rayon, "white", 4)
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


    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
                running = False

        screen.fill((30, 30, 30))

        for Cercle in Cercles:
            Cercle.update()
            if not Cercle.broken:
                Cercle.draw(screen)

        for i, b in enumerate(balles):
            b.update(dt)
            b.check_bounce_edges(WIDTH, HEIGHT)
            for cercle in Cercles:  # <- ici
                b.check_wall_cercle_collision(cercle)
            for autre in balles[i + 1:]:
                b.check_circle_collision(autre)
            b.draw(screen)

        pygame.display.flip()


pygame.quit()