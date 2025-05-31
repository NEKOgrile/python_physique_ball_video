import pygame
from pygame.math import Vector2
import math
import random
import pygame.gfxdraw

pygame.init()
pygame.font.init()  # Initialisation du module font

# =============================
# CONFIGURATION DE LA FENÊTRE
# =============================
WIDTH, HEIGHT = 1080, 1920
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Simulation de balle physique")
clock = pygame.time.Clock()

# =============================
# POLICES & COULEURS
# =============================
font_question = pygame.font.Font(None, 60)  # Police pour la question
font_score    = pygame.font.Font(None, 72)  # Police pour le score

COLOR_WHITE   = (255, 255, 255)
COLOR_BLACK   = (  0,   0,   0)
COLOR_RED     = (255,   0,   0)
COLOR_BLUE    = (  0,   0, 255)
COLOR_BG      = ( 30,  30,  30)  # fond général

# =============================
# TEXTE DE LA QUESTION
# =============================
question_text = "Are you dumb? (respectfully)"  # Remplacez par votre question

# =============================
# CLASSES (inchangées)
# =============================
class Particle:
    def __init__(self, pos, vel, color, lifetime, radius):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.color = color
        self.lifetime = lifetime
        self.radius = radius

    def update(self, dt):
        self.pos += self.vel * dt
        self.lifetime -= dt
        self.radius = max(0, self.radius - dt * 10)

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = max(0, int(255 * (self.lifetime / 1.0)))
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s,
                (*self.color, alpha),
                (int(self.radius), int(self.radius)),
                int(self.radius)
            )
            surface.blit(s, (self.pos.x - self.radius, self.pos.y - self.radius))


class WallCercle:
    def __init__(self, x, y, radius, color, width,
                 base_angle, rotation_speed, hole_opening_angle_rad):
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
        hole_end   = (hole_start + self.hole_opening_angle) % (2 * math.pi)

        if hole_start > hole_end:
            return angle >= hole_start or angle <= hole_end
        else:
            return hole_start <= angle <= hole_end

    def update(self, dt):
        self.time += dt
        if self.broken:
            return
        if not cercle_min_atteint:
            if self.radius > 110:
                self.radius -= 200 * dt
            if self.radius < 110:
                self.radius = 110

    def draw(self, surface):
        if self.broken:
            return
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.pos.x), int(self.pos.y)),
            int(self.radius),
            self.width
        )
        hole_start = (self.base_angle + self.time * self.rotation_speed) % (2 * math.pi)
        hole_end   = (hole_start + self.hole_opening_angle) % (2 * math.pi)

        start_deg = math.degrees(hole_start)
        end_deg   = math.degrees(hole_end)
        if end_deg < start_deg:
            end_deg += 360

        pts = [self.pos]
        for angle_deg in range(int(start_deg), int(end_deg) + 1):
            angle_rad = math.radians(angle_deg % 360)
            x = self.pos.x + self.radius * math.cos(angle_rad)
            y = self.pos.y + self.radius * math.sin(angle_rad)
            pts.append(Vector2(x, y))

        if len(pts) >= 3:
            pygame.draw.polygon(surface, (30, 30, 30), pts)


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
        self.particles = []
        self.positions = []
        self.max_trail = 20
        self.score = 0

    def draw(self, surface):
        for i, pos in enumerate(self.positions):
            alpha = int(255 * (1 - i / len(self.positions)))
            radius = int(self.radius * (1 - i / len(self.positions)) * 1.2)
            if radius < 1:
                continue
            trail_color = (*self.color, alpha)
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(s, radius, radius, radius, trail_color)
            surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

        pygame.draw.circle(
            surface,
            (255, 255, 255),
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
                    boost_factor = self.boost_speed_increase - (
                        self.boost_speed_increase - 1
                    ) * (time_after / 0.5)
                else:
                    self.boost_timer = 0
                    self.boost_elapsed = 0
            self.boost_timer -= dt

        self.pos += self.vel * boost_factor * dt

        self.positions.insert(0, Vector2(self.pos))
        if len(self.positions) > self.max_trail:
            self.positions.pop()

        particle = Particle(
            pos=self.pos,
            vel=-self.vel * 0.1 + Vector2(random.uniform(-10, 10), random.uniform(-10, 10)),
            color=self.color,
            lifetime=0.5,
            radius=self.radius / 2
        )
        self.particles.append(particle)
        for p in self.particles[:]:
            p.update(dt)
            if p.lifetime <= 0:
                self.particles.remove(p)

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
            return False
        offset = self.pos - cercle.pos
        distance = offset.length()
        if distance + self.radius > cercle.radius:
            if cercle.is_in_hole(self.pos):
                cercle.broken = True
                return True
            else:
                normal = offset.normalize()
                self.vel = self.vel.reflect(normal) * self.restitution
                overlap = distance + self.radius - cercle.radius
                self.pos -= normal * overlap
        return False


# =============================
# INITIALISATION DES OBJETS
# =============================
nombre_cercles = 1000
rayon_depart = 300
ecart_rayon = 12
hole_opening = math.radians(60)
rotation_speed = math.radians(20)
angle_offset = hole_opening * 0.1
cercle_min_atteint = False
voile_actif = False
voile_couleur = (255, 0, 0)
voile_timer = 0.0
voile_duree = 0.2

Cercles = []
i_cercle = 0
temps_depuis_dernier_cercle = 0
intervalle_generation = 0.0001

balle1 = Balle(WIDTH // 2 - 100, HEIGHT // 4, 20, (200, 50, 50))
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 4, 20, (50, 50, 200))
balles = [balle1, balle2]

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
            running = False

    # Génération progressive des cercles
    temps_depuis_dernier_cercle += dt
    while temps_depuis_dernier_cercle >= intervalle_generation and i_cercle < nombre_cercles:
        rayon = rayon_depart + i_cercle * ecart_rayon
        if rayon >= 200:
            base_angle = i_cercle * angle_offset
            cercle = WallCercle(
                WIDTH // 2,
                HEIGHT // 2,
                rayon,
                (255, 255, 255),
                4,
                base_angle,
                rotation_speed,
                hole_opening
            )
            Cercles.append(cercle)
        i_cercle += 1
        temps_depuis_dernier_cercle -= intervalle_generation

    # 1) On remplit le fond
    screen.fill(COLOR_BG)

    # 2) Mise à jour & dessin des cercles
    cercle_min_atteint = any(not c.broken and c.radius <= 110 for c in Cercles)
    for Cercle in reversed(Cercles):
        Cercle.update(dt)
        if not Cercle.broken and Cercle.radius <= 1000:
            Cercle.draw(screen)

    # 3) Mise à jour & dessin des balles (avec collisions)
    for i, b in enumerate(balles):
        b.update(dt)
        b.check_bounce_edges(WIDTH, HEIGHT)
        for cercle in Cercles:
            if b.check_wall_cercle_collision(cercle):
                b.score += 1
                voile_actif = True
                voile_timer = voile_duree
                voile_couleur = b.color
        for autre in balles[i + 1:]:
            b.check_circle_collision(autre)
        b.draw(screen)
        if voile_actif:
            voile_timer -= dt
            if voile_timer > 0:
                s = pygame.Surface((WIDTH, HEIGHT))
                s.set_alpha(100)
                s.fill(voile_couleur)
                screen.blit(s, (0, 0))
            else:
                voile_actif = False

    # =============================
    # 4) AFFICHAGE DE LA QUESTION AU-DESSUS
    # =============================
    question_surf = font_question.render(question_text, True, COLOR_BLACK)
    # Calcul de la position : centré horizontalement, un peu au-dessus du centre vertical
    q_x = WIDTH // 2 - question_surf.get_width() // 2
    # On place la question au-dessus de la boîte de score. On calculera la boîte de score ci-dessous.
    # Placeholder vertical : nous laissons 200 px au-dessus du centre.
    q_y = HEIGHT // 2 -500  
    # Fond blanc semi-transparent derrière la question (avec coins arrondis)
    box_q = pygame.Rect(
        q_x - 20, q_y - 10,
        question_surf.get_width() + 40,
        question_surf.get_height() + 20
    )
    pygame.draw.rect(screen, COLOR_WHITE, box_q, border_radius=12)
    screen.blit(question_surf, (q_x, q_y))

    # =============================
    # 5) AFFICHAGE DU SCORE AU CENTRE
    # =============================
    # Rendu des textes “Yes” et “No”
    oui_text = font_score.render(f"Yes : {balle2.score}", True, COLOR_BLUE)
    non_text = font_score.render(f"No : {balle1.score}", True, COLOR_RED)

    # Marges intérieures
    padding_h = 40
    padding_v = 20
    separator_width = 8

    total_width = (
        oui_text.get_width() +
        non_text.get_width() +
        separator_width +
        (padding_h * 3)
    )
    total_height = max(oui_text.get_height(), non_text.get_height()) + (padding_v * 2)

    rect_x = WIDTH // 2 - total_width // 2
    rect_y = HEIGHT // 2 - total_height -350

    # Fond blanc arrondi
    rect = pygame.Rect(rect_x, rect_y, total_width, total_height)
    pygame.draw.rect(screen, COLOR_WHITE, rect, border_radius=12)

    # Barre séparatrice noire
    sep_x = rect_x + padding_h + oui_text.get_width() + padding_h // 2
    pygame.draw.line(
        screen,
        COLOR_BLACK,
        (sep_x, rect_y + padding_v // 2),
        (sep_x, rect_y + total_height - padding_v // 2),
        separator_width
    )

    # Texte “Yes”
    oui_x = rect_x + padding_h
    oui_y = rect_y + (total_height // 2 - oui_text.get_height() // 2)
    screen.blit(oui_text, (oui_x, oui_y))

    # Texte “No”
    non_x = sep_x + (separator_width // 2) + padding_h // 2
    non_y = rect_y + (total_height // 2 - non_text.get_height() // 2)
    screen.blit(non_text, (non_x, non_y))

    # =============================
    # 6) MISE À JOUR DE L’ÉCRAN
    # =============================
    pygame.display.flip()

pygame.quit()
