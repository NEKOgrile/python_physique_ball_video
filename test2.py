import pygame
import pygame.midi
import mido
import time

# Fichier MIDI
MIDI_FILE = "I'm Blue.mid"  # Remplace par ton fichier

# Initialisation
pygame.init()
pygame.midi.init()

# Sortie MIDI (peut être muet si aucun synthé logiciel dispo)
output_id = pygame.midi.get_default_output_id()
midi_out = pygame.midi.Output(output_id)

# Fonction pour convertir les numéros de note en noms
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def get_note_name(midi_number):
    octave = (midi_number // 12) - 1
    note = NOTE_NAMES[midi_number % 12]
    return f"{note}{octave}"

# Charge le fichier MIDI
mid = mido.MidiFile(MIDI_FILE)

# Récupère tous les messages (de toutes les pistes)
all_messages = []
for track in mid.tracks:
    for msg in track:
        if not msg.is_meta:
            all_messages.append(msg)

# Lecture à intervalle fixe de 10 ms
for msg in all_messages:
    if msg.type == 'note_on' and msg.velocity > 0:
        print(f"Note ON  - {get_note_name(msg.note)} ({msg.note}), Vel: {msg.velocity}")
        midi_out.note_on(msg.note, msg.velocity)
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        print(f"Note OFF - {get_note_name(msg.note)} ({msg.note})")
        midi_out.note_off(msg.note, 0)

    time.sleep(0.1)  # 10 ms

# Nettoyage
midi_out.close()
pygame.midi.quit()
pygame.quit()
