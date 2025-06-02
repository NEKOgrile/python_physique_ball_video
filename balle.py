import pygame
from pygame.math import Vector2

# ========== CONFIGURATION ==========
# Couleurs
BLUE  = (100, 150, 255)
RED   = (255,  80,  80)


# Balle
GRAVITY        = 500      # gravité (en px/s²)
BALL_RADIUS    = 15
RESTITUTION    = 1.0      # rebond parfaitement élastique
MAX_SPEED      = 800      # vitesse maximale (en px/s)
BOOST_FACTOR   = 1.5      # multiplicateur temporaire de vitesse
BOOST_DURATION = 0.2      # durée du boost (en secondes)
# Limitation de vitesse

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