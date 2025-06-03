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
timer = 10.0

# --- États de jeu ---
# "play" → jusqu'à ce que timer = 0
# "explode_arcs" → 1 s d'agrandissement progressif des arcs
# "align_balls" → 0,5 s pour :
#    • aligner verticalement, 
#    • repositionner horizontalement à une certaine distance,
#    • faire grossir les balles en même temps
# "balls_aligned" → état final (pour la suite)
game_state = "play"
explosion_timer = 0.0

# Pour stocker les radius et width initiaux des arcs au moment de l'explosion
orig_radii  = []
orig_widths = []

# Variables pour l'animation d'alignement (align_balls)
align_duration = 1.0      # durée en secondes pour aligner/grossir/répartir les balles
align_timer    = 0.0

# Yeux pour mémoriser les positions/tailles de départ, et cibles
y_init1 = y_init2 = target_y = None
x_init1 = x_init2 = target_x1 = target_x2 = None
radius_init1 = radius_init2 = target_radius = None

# Séparation horizontale souhaitée (en px) entre les deux balles, une fois alignées :
separation = 300

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
            # Passer à l'explosion des arcs
            game_state = "explode_arcs"
            explosion_timer = 1.0  # 1 s pour exploser

            # Stocker radius et width initiaux de chaque arc
            orig_radii  = [arc.radius for arc in arcs]
            orig_widths = [arc.width  for arc in arcs]

        # 2) Tant que timer > 0, mise à jour “normale”
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

            # Collision entre les balles
            balles[0].check_circle_collision(balles[1])

            # Rotation + rétrécissement des arcs
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

        # 2) Calculer coef d'interpolation (0→1 en 1 s)
        coef = 1.0 - (explosion_timer / 1.0)

        # 3) Agrandir peu à peu chaque arc depuis orig_radii vers 6× (exemple)
        for idx, arc in enumerate(arcs):
            arc.radius = orig_radii[idx] * (1 + 5 * coef)   # 1→6×
            arc.width  = orig_widths[idx] + int(20 * coef)  # on passe à +20 px d'épaisseur

        # 4) Quand explosion terminée, préparer l'alignement des balles
        if explosion_timer <= 0:
            game_state = "align_balls"
            align_timer = align_duration   # 0,5 s

            # Y départ et Y cible
            y_init1 = balle1.pos.y
            y_init2 = balle2.pos.y
            target_y = min(y_init1, y_init2)

            # X départ et X cible :
            x_init1 = balle1.pos.x
            x_init2 = balle2.pos.x
            # On veut les deux balles centrées autour de WIDTH//2, espacées de `separation`
            target_x1 = (WIDTH // 2) + separation / 2
            target_x2 = (WIDTH // 2) - separation / 2

            # Rayon départ et rayon cible (ex. on veut qu'elles passent de 15→50 px)
            radius_init1 = balle1.radius
            radius_init2 = balle2.radius
            target_radius = 50

    elif game_state == "align_balls":
        # 1) Décrémenter align_timer
        align_timer -= dt
        if align_timer < 0:
            align_timer = 0

        # 2) Calculer t entre 0 et 1 : 0 au départ, 1 à la fin
        t = 1.0 - (align_timer / align_duration)  # passe de 0→1

        # 3) Interpoler la position Y de chaque balle
        balle1.pos.y = y_init1 + (target_y - y_init1) * t
        balle2.pos.y = y_init2 + (target_y - y_init2) * t

        # 4) Interpoler la position X de chaque balle
        balle1.pos.x = x_init1 + (target_x1 - x_init1) * t
        balle2.pos.x = x_init2 + (target_x2 - x_init2) * t

        # 5) Faire croître les rayons
        balle1.radius = radius_init1 + (target_radius - radius_init1) * t
        balle2.radius = radius_init2 + (target_radius - radius_init2) * t

        # 6) Mettre la vélocité à zéro pour que les balles restent figées
        balle1.vel = Vector2(0, 0)
        balle2.vel = Vector2(0, 0)

        # 7) Quand tout est terminé, passer à l'état “balls_aligned”
        if align_timer <= 0:
            game_state = "balls_aligned"

    elif game_state == "balls_aligned":
        # Ici, les balles sont à la même hauteur, espacées de `separation` et ont grandi.
        # On peut lancer la phase suivante (décompte du score, etc.).
        pass

    # ========== DESSIN (toujours exécuté) ==========
    screen.fill(BG_COLOR)

    # 1) Dessiner les arcs (s'ils sont encore dans la liste)
    for arc in arcs:
        arc.draw(screen)

    # 2) Dessiner les balles (en mouvement ou alignées)
    for b in balles:
        b.draw(screen)

    # 3) Titre
    title_text = "Are you dumb? (respectfully)"
    title_surf = font_title.render(title_text, True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 200))
    pygame.draw.rect(screen, (0, 0, 0), title_rect.inflate(20, 10))
    screen.blit(title_surf, title_rect)

    # 4) Scores Yes / No
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
