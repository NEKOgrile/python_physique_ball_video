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
GREEN  = (0, 255, 0)  # Vert, même que le score YES


# Arcs
RAYON_DEPART      = 100
ECART_RAYON       = 12
OUVERTURE_DEGREES = 300

# Balle
GRAVITY        = 500
BALL_RADIUS    = 15
RESTITUTION    = 1.0
MAX_SPEED      = 800
BOOST_FACTOR   = 1.5
BOOST_DURATION = 0.2

# Croissance maximale d'une balle (en pixels de rayon)
MAX_GROWTH_RADIUS = 100

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
balle2 = Balle(WIDTH // 2 + 100, HEIGHT // 2, BALL_RADIUS, GREEN)
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
font_timer = pygame.font.SysFont(None, 50)


timer = 61.0


winner_font_timer = 0.0
winner_font_duration = 2.0
winner_font_max_size = 120

game_state = "play"
explosion_timer = 0.0
orig_radii = []
orig_widths = []
separation = 300
align_duration = 1.0
align_timer = 0.0
y_init1 = y_init2 = target_y = None
x_init1 = x_init2 = target_x1 = target_x2 = None
radius_init1 = radius_init2 = target_radius = None
score_timer = 0.0
score_duration = 1.0
yes_init = no_init = 0
grow_timer = 0.0
grow_duration = 1.0
grow_init1 = grow_init2 = None
grow_target1 = grow_target2 = None
winner = None
loser = None
center_move_timer = 1.0
center_move_duration = 1.0

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
            running = False

    if game_state == "play":
        timer -= dt
        if timer <= 0:
            timer = 0
            game_state = "explode_arcs"
            explosion_timer = 1.0
            orig_radii = [arc.radius for arc in arcs]
            orig_widths = [arc.width for arc in arcs]

        if game_state == "play":
            for b in balles:
                b.update(dt)
                b.check_bounce_edges(WIDTH, HEIGHT)
                for arc in arcs:
                    if arc.check_wall_cercle_collision(b):
                        if b.color == GREEN:
                            yes_score += 1
                        else:
                            no_score += 1
            balles[0].check_circle_collision(balles[1])
            for arc in arcs:
                arc.rotate(dt)
            if not any((not arc.broken and arc.radius <= RAYON_DEPART) for arc in arcs):
                for arc in arcs:
                    arc.shrink(dt)

    elif game_state == "explode_arcs":
        explosion_timer -= dt
        if explosion_timer < 0:
            explosion_timer = 0

        coef = 1.0 - (explosion_timer / 1.0)

        for idx, arc in enumerate(arcs):
            arc.radius = orig_radii[idx] * (1 + 7 * coef)
            arc.width = orig_widths[idx] + int(20 * coef)

        if explosion_timer <= 0:
            game_state = "align_balls"
            align_timer = align_duration
            y_init1 = balle1.pos.y
            y_init2 = balle2.pos.y
            target_y = min(y_init1, y_init2)
            x_init1 = balle1.pos.x
            x_init2 = balle2.pos.x
            target_x1 = (WIDTH // 2) + separation / 2
            target_x2 = (WIDTH // 2) - separation / 2
            radius_init1 = balle1.radius
            radius_init2 = balle2.radius
            target_radius = 50

    elif game_state == "align_balls":
        align_timer -= dt
        if align_timer < 0:
            align_timer = 0

        t = 1.0 - (align_timer / align_duration)

        balle1.pos.y = y_init1 + (target_y - y_init1) * t
        balle2.pos.y = y_init2 + (target_y - y_init2) * t

        balle1.pos.x = x_init1 + (target_x1 - x_init1) * t
        balle2.pos.x = x_init2 + (target_x2 - x_init2) * t

        balle1.radius = radius_init1 + (target_radius - radius_init1) * t
        balle2.radius = radius_init2 + (target_radius - radius_init2) * t

        balle1.vel = Vector2(0, 0)
        balle2.vel = Vector2(0, 0)

        if align_timer <= 0:
            game_state = "decrease_score"
            score_timer = score_duration
            yes_init = yes_score
            no_init = no_score
            grow_init1 = balle1.radius
            grow_init2 = balle2.radius
            max_score = max(yes_init, no_init)
            yes_ratio = yes_init / max_score if max_score > 0 else 0
            no_ratio = no_init / max_score if max_score > 0 else 0
            grow_target1 = grow_init1 + MAX_GROWTH_RADIUS * no_ratio
            grow_target2 = grow_init2 + MAX_GROWTH_RADIUS * yes_ratio

    elif game_state == "decrease_score":
        score_timer -= dt
        if score_timer < 0:
            score_timer = 0

        t = 1.0 - (score_timer / score_duration)

        yes_score = int(yes_init * (1.0 - t))
        no_score = int(no_init * (1.0 - t))

        balle1.radius = grow_init1 + (grow_target1 - grow_init1) * t
        balle2.radius = grow_init2 + (grow_target2 - grow_init2) * t

        if score_timer <= 0:
            yes_score = 0
            no_score = 0
            winner = balle1 if grow_target1 > grow_target2 else balle2
            loser = balle2 if winner is balle1 else balle1
            game_state = "center_winner"
            center_move_timer = center_move_duration
        
    elif game_state == "center_winner":
        center_move_timer -= dt
        if center_move_timer < 0:
            center_move_timer = 0

        t = 1.0 - (center_move_timer / center_move_duration)

        loser.radius = loser.radius * (1 - t)  # shrink loser
        winner.pos.x += (WIDTH // 2 - winner.pos.x) * t
        winner.pos.y += (HEIGHT // 2 - winner.pos.y) * t

        if center_move_timer <= 0:
            winner_font_timer = winner_font_duration
            game_state = "done"


    elif game_state == "grow_finished":
        pass

    elif game_state == "done":
        if winner_font_timer > 0:
            winner_font_timer -= dt


    screen.fill(BG_COLOR)

    for arc in arcs:
        arc.draw(screen)

    for b in balles:
        if b.radius > 1:
            b.draw(screen)

            # Choix du label
            label = "YES" if b.color == GREEN else "NO"
            
            # Taille du texte proportionnelle à la taille de la balle
            font_size = int(b.radius * 0.9)  # Ajuste le facteur si besoin
            font_label = pygame.font.SysFont(None, font_size)
            
            # Création de la surface texte
            label_surf = font_label.render(label, True, (255, 255, 255))
            label_rect = label_surf.get_rect(center=(int(b.pos.x), int(b.pos.y)))
            
            # Dessin du texte centré sur la balle
            screen.blit(label_surf, label_rect)



    title_surf = font_title.render("Are you dumb? (respectfully)", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 200))
    pygame.draw.rect(screen, (0, 0, 0), title_rect.inflate(20, 10))
    screen.blit(title_surf, title_rect)

    yes_surf = font_score.render(f"Yes : {yes_score}", True, (0, 255, 0))
    yes_rect = yes_surf.get_rect(center=(WIDTH // 2 - 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), yes_rect.inflate(20, 10))
    screen.blit(yes_surf, yes_rect)

    no_surf = font_score.render(f"No : {no_score}", True, (255, 0, 0))
    no_rect = no_surf.get_rect(center=(WIDTH // 2 + 120, 260))
    pygame.draw.rect(screen, (0, 0, 0), no_rect.inflate(20, 10))
    screen.blit(no_surf, no_rect)

    minutes = int(timer) // 60
    seconds = int(timer) % 60
    timer_surf = font_timer.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    timer_rect = timer_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 300))
    pygame.draw.rect(screen, (0, 0, 0), timer_rect.inflate(20, 10))
    screen.blit(timer_surf, timer_rect)

     # Affichage "Winner!" animé
    if game_state == "done" and winner_font_timer > 0:
        t = 1.0 - (winner_font_timer / winner_font_duration)
        font_size = int(20 + t * (winner_font_max_size - 20))
        winner_font = pygame.font.SysFont(None, font_size)
        winner_surf = winner_font.render("Winner!", True, (255, 255, 0))
        winner_rect = winner_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        screen.blit(winner_surf, winner_rect)



    pygame.display.flip()

pygame.midi.quit()
pygame.quit()