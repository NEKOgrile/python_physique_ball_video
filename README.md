# 🎵 Ball Collision MIDI - Animation interactive avec Pygame

Ce projet utilise **Python** et **Pygame** pour simuler deux balles rebondissant à l’intérieur d’une série d’arcs circulaires rotatifs. Lorsqu’une balle entre en collision avec un arc, une **note MIDI** est jouée 🎶. Le projet allie **physique 2D**, **animation graphique** et **synchronisation sonore via MIDI**.

---

## 🎯 Objectif

- Représenter visuellement une simulation avec des **balle(s)** rebondissant contre des **arcs circulaires rotatifs**.
- Lors de collisions précises, une **note MIDI** extraite d’un fichier `.mid` est jouée.
- Afficher en temps réel les scores des balles et des effets visuels dynamiques (arcs qui tournent, rétrécissent...).

---

## 📁 Structure du projet

`dash`
├── arc_circle.py              `# Gestion des arcs circulaires et détection des collisions`
├── balle.py                   `# Classe des balles (mouvement, rebond, collisions entre balles)`
├── main.py                    `# Script principal exécutant la boucle de jeu`
├── midi_manager.py            `# Gestionnaire de lecture de notes MIDI`
├── test4.py                   `# Script de test ou d’expérimentation`
├── musique/
│   └── I'm Blue.mid           `# Fichier MIDI utilisé pour jouer les notes`
└── README.md                  `# Fichier explicatif du projet (celui-ci)`

---

## 🧰 Prérequis

| Outil / Lib                  | Version recommandée | Utilisation                          |
|------------------------------|----------------------|--------------------------------------|
| **Python**                   | 3.13.x               | Langage principal                    |
| **pygame**                   | 2.6.1+               | Affichage graphique & MIDI          |
| **pygame.midi**              | (inclus dans pygame) | Gestion des notes MIDI              |
| **mido**                     | 1.3+                 | Lecture de fichiers `.mid`          |

### ✅ Installation

`dash`
pip install pygame mido python-rtmidi
`dash`

---

## ▶️ Lancement rapide

1. Assurez-vous d’avoir installé Python et les bibliothèques nécessaires (`pygame`, `mido`, `python-rtmidi`).
2. Placez votre fichier MIDI dans le dossier `musique/` (ou utilisez `I'm Blue.mid` fourni).
3. Lancez le programme principal :

`dash`
python main.py
`dash`

---

## ⚙️ Fonctionnement

- Deux balles sont initialisées avec des vitesses différentes.
- Une série d’arcs tournent en permanence autour du centre.
- Lorsqu’une balle entre en collision avec un **arc dans la zone non trouée**, elle rebondit et une **note MIDI est jouée**.
- Si la balle entre dans la "faille" d’un arc, l’arc est marqué comme **cassé** (et ne réagit plus).
- Un score est attribué à chaque balle selon la réussite ou non du passage.

---

## 🧪 Test et Debug

- Le fichier `test4.py` permet de tester certaines fonctionnalités (ex : mouvement de balle ou notes).
- En cas d’erreur `AttributeError` sur `midi_manager`, assurez-vous de passer correctement l'objet à chaque arc :  
`dash`
ArcCircle(..., midi_manager=midi_manager)
`dash`
- Vérifiez également que la méthode appelée est `play_next()` et non `play_next_note()`.

---

## 📈 Roadmap (améliorations prévues)

- [ ] Ajout d'une interface de **sélection de fichier MIDI**
- [ ] Effets visuels lors de la **lecture de notes MIDI** (lumières, flashs)
- [ ] Gestion avancée de **plusieurs canaux MIDI**
- [ ] Intégration avec **contrôleurs MIDI physiques**
- [ ] Optimisation de la gestion des collisions
- [ ] Ajout d'une **musique de fond** synchronisée
- [ ] Menu d’accueil et pause

---

## 🧑‍💻 Auteur

Développé par **Willem Cornil** dans un but personnel, artistique et technique.  
Le projet est librement partageable — toute contribution est la bienvenue !

---

## 📝 .gitignore recommandé

Voici un `.gitignore` minimal :

`dash`
__pycache__/
*.pyc
.venv/
musique/*.mid
`dash`

---
