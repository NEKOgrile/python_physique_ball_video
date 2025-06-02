import pygame
import math
from pygame.math import Vector2
import mido
import pygame.midi
import time

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
OUVERTURE_DEGREES = 300

# Balle
GRAVITY        = 500      # gravité (en px/s²)
BALL_RADIUS    = 15
RESTITUTION    = 1.0      # rebond parfaitement élastique
MAX_SPEED      = 800      # vitesse maximale (en px/s)
BOOST_FACTOR   = 1.5      # multiplicateur temporaire de vitesse
BOOST_DURATION = 0.2      # durée du boost (en secondes)
# Limitation de vitesse


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

                # 🎵 Jouer une note MIDI si délai respecté
                global note_index, last_note_time
                now = pygame.time.get_ticks()
                if now - last_note_time >= 100:
                    if note_index < len(notes):
                        note, velocity = notes[note_index]
                        midi_out.note_on(note, velocity)
                        note_index += 1
                        last_note_time = now
                    else:
                        note_index = 0

        return False

class Balle:
    def __init__(self, x, y, radius, color):
        self.pos    = Vector2(x, y)
        self.vel    = Vector2(0, 0)     # vitesse “de base”, sans boost
        self.radius = radius
        self.color  = color

        # Masse proportionnelle au rayon (pour la collision élastique)
        self.mass       = radius
        self.restitution = RESTITUTION  # = 1.0 → pas de perte d’énergie

        # Pour gérer le boost :
        self.is_boosting  = False       # à True pendant les 0,2 s du boost
        self.boost_timer  = 0.0         # compte à rebours du boost (s)
        self.can_boost    = True        # autorise un nouveau boost si True

    def clamp_velocity(self):
        """
        Si la norme de self.vel dépasse MAX_SPEED, on la ramène à MAX_SPEED
        (en conservant la direction).
        """
        speed = self.vel.length()
        if speed > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

    def draw(self, surface):
        # Cercle blanc en arrière-plan, puis cercle coloré par-dessus
        pygame.draw.circle(surface, (255, 255, 255),
                           (int(self.pos.x), int(self.pos.y)),
                           self.radius + 6)
        pygame.draw.circle(surface, self.color,
                           (int(self.pos.x), int(self.pos.y)),
                           self.radius)

    def update(self, dt):
        # 1) Appliquer la gravité sur la vitesse “de base” (self.vel)
        self.vel.y += GRAVITY * dt

        # 2) Clamper self.vel pour ne jamais dépasser MAX_SPEED
        self.clamp_velocity()

        # 3) Déplacer la balle : on applique le “boost” en multipliant
        #    seulement au moment du déplacement, PAS sur self.vel elle-même.
        facteur = BOOST_FACTOR if self.is_boosting else 1.0
        self.pos += self.vel * facteur * dt

        # 4) Gestion du timer de boost :
        if not self.can_boost:
            self.boost_timer -= dt
            if self.boost_timer <= 0:
                # À la fin des 0,2 s, on repasse en mode “pas de boost”
                self.boost_timer = 0.0
                self.is_boosting = False
                self.can_boost   = True

    def check_bounce_edges(self, width, height):
        # Rebond sur le bord gauche/droite
        if self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.vel.x *= -self.restitution
            self.clamp_velocity()
        elif self.pos.x + self.radius > width:
            self.pos.x = width - self.radius
            self.vel.x *= -self.restitution
            self.clamp_velocity()

        # Rebond sur le bord haut/bas
        if self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.vel.y *= -self.restitution
            self.clamp_velocity()
        elif self.pos.y + self.radius > height:
            self.pos.y = height - self.radius
            self.vel.y *= -self.restitution
            self.clamp_velocity()

    def check_circle_collision(self, autre):
        """
        Détection + résolution d’une collision parfaitement élastique avec une autre balle.
        Si la collision est détectée et que self.can_boost est True, on active le boost
        (i.e. self.is_boosting = True pendant 0,2 s), puis on bloque can_boost = False
        jusqu’à la fin du timer.
        """
        offset  = self.pos - autre.pos
        dist_sq = offset.length_squared()
        rayon_min = self.radius + autre.radius

        if dist_sq < rayon_min ** 2:
            dist     = max(offset.length(), 1e-8)
            overlap  = rayon_min - dist
            normal   = offset.normalize()

            # 1) On repousse les deux balles pour qu’elles ne se chevauchent pas
            correction = normal * (overlap / 2)
            self.pos  += correction
            autre.pos -= correction

            # 2) Calcul de l’impulsion élastique
            rel_vel = self.vel - autre.vel
            vel_norm = rel_vel.dot(normal)

            if vel_norm < 0:
                # Impulsion standard choc élastique 1D sur la normale
                impulse = (2 * vel_norm) / (self.mass + autre.mass)
                self.vel   -= impulse * autre.mass * normal
                autre.vel  += impulse * self.mass     * normal

                # On clamp les deux vitesses juste après l’impulsion
                self.clamp_velocity()
                autre.clamp_velocity()

                # 3) Si self peut encore être boosté → on démarre le boost
                if self.can_boost:
                    self.is_boosting  = True
                    self.can_boost    = False
                    self.boost_timer  = BOOST_DURATION
                    # Note : on n’applique PAS self.vel *= BOOST_FACTOR ici,
                    #       car le multipliant ne sert qu’au moment du déplacement.

                # 4) Même chose pour l’autre balle
                if autre.can_boost:
                    autre.is_boosting  = True
                    autre.can_boost    = False
                    autre.boost_timer  = BOOST_DURATION

    def check_wall_cercle_collision(self, cercle):
        """
        Votre code existant pour gérer le rebond sur un arc de cercle
        (ou la “cassure” si la balle tombe dans le trou).
        """
        return cercle.check_wall_cercle_collision(self)

# ========== INITIALISATION PYGAME ==========
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deux Balles + Arcs")
clock = pygame.time.Clock()
pygame.mixer.init()
pygame.midi.init()
midi_out = pygame.midi.Output(0)

# Charger les notes du fichier MIDI
mid = mido.MidiFile("I'm Blue.mid")
notes = []
for track in mid.tracks:
    for msg in track:
        if msg.type == 'note_on' and msg.velocity > 0:
            notes.append((msg.note, msg.velocity))

note_index = 0
last_note_time = 0  # en millisecondes

# Initialisation des balles
center = (WIDTH // 2, HEIGHT // 2)
balle1 = Balle(WIDTH // 2 - 100, HEIGHT // 2, BALL_RADIUS, RED)
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 2, BALL_RADIUS, BLUE)
balle1.vel = Vector2(400/1.5, -500/1.5)   # norme ≈ 640 px/s
balle2.vel = Vector2(-400/1.5, -400/1.5)  # norme ≈ 565 px/s
#balle1.vel = Vector2(150, -200)
#balle2.vel = Vector2(-150, -150)
balles = [balle1, balle2]

# Création des arcs
arcs = []
for i in range(1000):
    start_deg = i * -5
    radius = RAYON_DEPART + i * ECART_RAYON
    start_rad = math.radians(start_deg)
    end_rad = math.radians(start_deg + OUVERTURE_DEGREES)
    color = [BLUE, RED, WHITE][i % 3]
    arcs.append(ArcCircle(center, radius, start_rad, end_rad, color))

yes_score = 0
no_score = 0
font_title = pygame.font.SysFont(None, 40)
font_score = pygame.font.SysFont(None, 36)

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
           event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE
        ):
            running = False

    # —————— Mise à jour des balles ——————
    for b in balles:
        b.update(dt)
        b.check_bounce_edges(WIDTH, HEIGHT)
        # Collision avec chaque arc
        for arc in arcs:
            if b.check_wall_cercle_collision(arc):
                if b.color == BLUE:
                    yes_score += 1
                else:
                    no_score += 1

    # Collision entre les deux balles
    balles[0].check_circle_collision(balles[1])

    # —————— Rotation et rétrécissement des arcs ——————
    for arc in arcs:
        arc.rotate(dt)

    any_at_min = any((not arc.broken and arc.radius <= RAYON_DEPART) for arc in arcs)
    if not any_at_min:
        for arc in arcs:
            arc.shrink(dt)

    # —————— Dessin ——————
    screen.fill(BG_COLOR)
    for arc in arcs:
        arc.draw(screen)
    for b in balles:
        b.draw(screen)

    # Titre (centré plus bas)
    title_text = "Are you dumb? (respectfully)"
    title_surf = font_title.render(title_text, True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 200))
    pygame.draw.rect(screen, (0, 0, 0), title_rect.inflate(20, 10))
    screen.blit(title_surf, title_rect)

    # Score Yes (dessous à gauche)
    yes_text_str = f"Yes : {yes_score}"
    yes_surf = font_score.render(yes_text_str, True, (0, 255, 0))
    yes_rect = yes_surf.get_rect(center=(screen.get_width() // 2 - 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), yes_rect.inflate(20, 10))
    screen.blit(yes_surf, yes_rect)

    # Score No (dessous à droite)
    no_text_str = f"No : {no_score}"
    no_surf = font_score.render(no_text_str, True, (255, 0, 0))
    no_rect = no_surf.get_rect(center=(screen.get_width() // 2 + 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), no_rect.inflate(20, 10))
    screen.blit(no_surf, no_rect)


    pygame.display.flip()

pygame.midi.quit()
pygame.quit()
