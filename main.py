import pygame
from pygame.math import Vector2

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Simulation de balle physique")
clock = pygame.time.Clock()

class WallCercle: 
    def __init__(self , x , y , radius , color , width ):
        self.pos = Vector2(x, y)
        self.radius = radius
        self.color = color
        self.width = width

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius, self.width)

class Balle:
    def __init__(self, x, y, radius, color):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.radius = radius
        self.color = color
        self.mass = radius
        self.restitution = 1

    def draw(self, surface):
        # Dessine un contour blanc
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius + 6)
        # Dessine la balle colorée
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def update(self, dt):
        g = 500.0
        self.vel.y += g * dt
        # SUPPRIMER l'amortissement pour garder la vitesse constante
        # self.vel *= 0.99  # supprimé
        self.pos += self.vel * dt

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
            # On force une vitesse minimale vers le haut pour éviter que ça colle
            if abs(self.vel.y) < 50:
                self.vel.y = -50

    def check_circle_collision(self, autre):
        offset = self.pos - autre.pos
        dist_sq = offset.length_squared()
        rayon_min = self.radius + autre.radius
        if dist_sq < rayon_min**2:
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

    def check_wall_cercle_collision(self, cercle):
        offset = self.pos - cercle.pos
        distance = offset.length()
        if distance + self.radius > cercle.radius:
            normal = offset.normalize()
            self.vel = self.vel.reflect(normal) * self.restitution
            overlap = distance + self.radius - cercle.radius
            self.pos -= normal * overlap

# création du cercle
Cercle = WallCercle(WIDTH // 2, HEIGHT // 2, 300, "white", 4)

# création des balles
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
    Cercle.draw(screen)

    for i, b in enumerate(balles):
        b.update(dt)
        b.check_bounce_edges(WIDTH, HEIGHT)
        b.check_wall_cercle_collision(Cercle)
        for autre in balles[i + 1:]:
            b.check_circle_collision(autre)
        b.draw(screen)

    pygame.display.flip()

pygame.quit()
