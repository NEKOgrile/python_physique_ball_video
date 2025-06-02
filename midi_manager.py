import pygame.midi
import mido


class MidiManager:
    def __init__(self, filename):
        self.notes = []
        self.index = 0
        self.last_note_time = 0
        self.output = pygame.midi.Output(0)
        self.load_midi(filename)

    def load_midi(self, filename):
        mid = mido.MidiFile(filename)
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.notes.append((msg.note, msg.velocity))

    def play_next_note(self):
        now = pygame.time.get_ticks()
        if self.index < len(self.notes) and now - self.last_note_time >= 100:
            note, velocity = self.notes[self.index]
            self.output.note_on(note, velocity)
            self.index += 1
            self.last_note_time = now
