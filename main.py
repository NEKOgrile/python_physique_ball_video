import pygame
import math
import mido
import pygame.midi
from balle import Balle
from pygame.math import Vector2
from arc_circle import ArcCircle
from midi_manager import MidiManager

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

# ========== INITIALISATION PYGAME ==========
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deux Balles + Arcs")
clock = pygame.time.Clock()
pygame.mixer.init()
pygame.midi.init()
midi_manager = MidiManager("musique/I'm Blue.mid")

# Initialisation des balles
center = (WIDTH // 2, HEIGHT // 2)
balle1 = Balle(WIDTH // 2 - 100, HEIGHT // 2, BALL_RADIUS, RED)
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 2, BALL_RADIUS, BLUE)
balle1.vel = Vector2(400/1.5, -500/1.5)
balle2.vel = Vector2(-400/1.5, -400/1.5)
balles = [balle1, balle2]

# Création des arcs
arcs = []
for i in range(1000):
    start_deg = i * -5
    radius = RAYON_DEPART + i * ECART_RAYON
    start_rad = math.radians(start_deg)
    end_rad = math.radians(start_deg + OUVERTURE_DEGREES)
    color = [BLUE, RED, WHITE][i % 3]
    arcs.append(ArcCircle(center, radius, start_rad, end_rad, color, midi_manager=midi_manager))

yes_score = 0
no_score = 0
font_title = pygame.font.SysFont(None, 80)
font_score = pygame.font.SysFont(None, 66)

# Police pour le timer
font_timer = pygame.font.SysFont(None, 50)

# Initialiser le timer à 61 secondes (1 min 01 sec)
timer = 61.0

# --- Gestion des états de jeu ---
game_state = "play"
explosion_timer = 0.0

# Pour stocker, lors du début de l'explosion, le radius et width initiaux
orig_radii = []
orig_widths = []

running = True
while running:
    dt = clock.tick(FPS) / 1000.0  # dt en secondes

    # --- Gestion des évènements ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
           event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE
        ):
            running = False

    # ========== LOGIQUE EN FONCTION DE L'ÉTAT ==========
    if game_state == "play":
        # 1) Décrémenter le timer
        timer -= dt
        if timer <= 0:
            timer = 0
            # On passe en phase d'explosion
            game_state = "explode_arcs"
            explosion_timer = 1.0  # durée de l'explosion en secondes

            # On stocke les radius et width actuels de chaque arc
            orig_radii  = [arc.radius for arc in arcs]
            orig_widths = [arc.width  for arc in arcs]

        # 2) Tant que timer > 0, on continue la mise à jour habituelle
        if game_state == "play":
            # Mise à jour des balles
            for b in balles:
                b.update(dt)
                b.check_bounce_edges(WIDTH, HEIGHT)
                # Collision avec chaque arc
                for arc in arcs:
                    collision = arc.check_wall_cercle_collision(b)
                    if collision:
                        if b.color == BLUE:
                            yes_score += 1
                        else:
                            no_score += 1

            # Collision entre les deux balles
            balles[0].check_circle_collision(balles[1])

            # Rotation et rétrécissement des arcs
            for arc in arcs:
                arc.rotate(dt)
            any_at_min = any((not arc.broken and arc.radius <= RAYON_DEPART) for arc in arcs)
            if not any_at_min:
                for arc in arcs:
                    arc.shrink(dt)

    elif game_state == "explode_arcs":
        # 1) Décrémenter le timer d'explosion
        explosion_timer -= dt
        if explosion_timer < 0:
            explosion_timer = 0

        # 2) Calculer le coefficient d'interpolation (0 → 1 en 1s)
        coef = 1.0 - (explosion_timer / 1.0)

        # 3) Pour chaque arc, agrandir radius et width depuis l'état initial
        for idx, arc in enumerate(arcs):
            # new_radius passe de orig_radii[idx] → orig_radii[idx] * 4 (exemple 4×)
            arc.radius = orig_radii[idx] * (1 + 5 * coef)
            # new_width passe de orig_widths[idx] → orig_widths[idx] + 10
            arc.width  = orig_widths[idx] + int(10 * coef)

        # 4) Quand explosion_timer atteint 0, on supprime enfin les arcs
        if explosion_timer <= 0:
            arcs.clear()
            game_state = "after_explosion"

    elif game_state == "after_explosion":
        # Pour l'instant : rien d'autre, on laissera ici la suite (alignement, etc.)
        pass

    # ========== DESSIN (toujours exécuté) ==========
    screen.fill(BG_COLOR)

    # 1) Dessiner les arcs (ou rien si la liste est vide)
    for arc in arcs:
        arc.draw(screen)

    # 2) Dessiner les balles (même si elles sont figées pendant l'explosion)
    for b in balles:
        b.draw(screen)

    # 3) Afficher le titre
    title_text = "Are you dumb? (respectfully)"
    title_surf = font_title.render(title_text, True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 200))
    pygame.draw.rect(screen, (0, 0, 0), title_rect.inflate(20, 10))
    screen.blit(title_surf, title_rect)

    # 4) Afficher les scores
    yes_text_str = f"Yes : {yes_score}"
    yes_surf = font_score.render(yes_text_str, True, (0, 255, 0))
    yes_rect = yes_surf.get_rect(center=(WIDTH // 2 - 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), yes_rect.inflate(20, 10))
    screen.blit(yes_surf, yes_rect)

    no_text_str = f"No : {no_score}"
    no_surf = font_score.render(no_text_str, True, (255, 0, 0))
    no_rect = no_surf.get_rect(center=(WIDTH // 2 + 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), no_rect.inflate(20, 10))
    screen.blit(no_surf, no_rect)

    # 5) Afficher le timer
    minutes = int(timer) // 60
    seconds = int(timer) % 60
    timer_text = f"{minutes:02d}:{seconds:02d}"
    timer_surf = font_timer.render(timer_text, True, WHITE)
    timer_rect = timer_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 300))
    pygame.draw.rect(screen, (0, 0, 0), timer_rect.inflate(20, 10))
    screen.blit(timer_surf, timer_rect)

    pygame.display.flip()

pygame.midi.quit()
pygame.quit()
