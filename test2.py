import pygame
import math

def draw_smooth_arc(surface, color, center, radius, start_angle, end_angle, width, step_deg=1):
    """
    Dessine un arc antialiasé en plaçant de petites billes le long de la circonférence.
      - surface      : surface pygame
      - color        : couleur de l'arc
      - center       : (x,y) du centre
      - radius       : rayon de l'arc
      - start_angle  : angle de début en radians
      - end_angle    : angle de fin en radians
      - width        : épaisseur de l'arc en pixels
      - step_deg     : résolution en degrés (plus petit => plus fluide, plus lent)
    """
    x0, y0 = center
    r = radius
    half = width / 2
    step = math.radians(step_deg)

    a = start_angle
    # on boucle de start→end
    while a <= end_angle:
        x = x0 + math.cos(a) * r
        y = y0 + math.sin(a) * r
        # dessine un petit cercle de rayon half
        pygame.draw.circle(surface, color, (int(x), int(y)), int(half))
        a += step

# ---- exemple minimal ----
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# paramètres
center = (400, 300)
radius = 200
start_a = math.radians(30)
end_a   = math.radians(150)
thick   = 8

running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill((30,30,30))
    # on trace notre arc lissé
    draw_smooth_arc(screen, (255,255,255), center, radius, start_a, end_a, thick, step_deg=0.5)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
