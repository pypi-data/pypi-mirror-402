import logging

import pygame

import trosnoth.data.sound
from trosnoth.data import getPath
from trosnoth.utils.math import distance


log = logging.getLogger(__name__)


CROWD_CHANNEL = 0
LOOPING_SOUND_CHANNELS = (1, 2, 3)


def get_sound_volume(dist, loud_radius=500):
    return max(0, 1 / max(1, dist / loud_radius) ** 2 - 0.01)


def get_distance(origin, pos, x_offset=0):
    x, y = origin
    x += x_offset
    return distance((x, y), pos)


class SoundAction:
    def __init__(self, filename):
        if not pygame.mixer.get_init():
            return

        try:
            self.sound = pygame.mixer.Sound(getPath(trosnoth.data.sound, filename))
        except Exception:
            self.sound = None
            log.exception('Error loading sound file')

    def play(self, origin=None, pos=None, *, master_volume):
        if self.sound is None or not pygame.mixer.get_init():
            return
        if origin is None or pos is None:
            l_volume = r_volume = 1
        else:
            l_volume = get_sound_volume(get_distance(origin, pos, x_offset=-250))
            r_volume = get_sound_volume(get_distance(origin, pos, x_offset=250))

        l_volume *= master_volume
        r_volume *= master_volume
        if l_volume < 0.01 and r_volume < 0.01:
            return

        channel = self.sound.play()

        if channel:
            channel.set_volume(l_volume, r_volume)


class LoopingSound:
    def __init__(self, filename, origin, position, channel, master_volume):
        if not pygame.mixer.get_init():
            return
        self.channel_number = channel
        self.channel = pygame.mixer.Channel(channel)

        try:
            self.sound = pygame.mixer.Sound(getPath(trosnoth.data.sound, filename))
        except Exception:
            self.sound = None
            log.exception('Error loading sound file')

        self.update(origin, position, master_volume)

    def update(self, origin, pos, master_volume):
        if not pygame.mixer.get_init():
            return

        l_volume = get_sound_volume(get_distance(origin, pos, x_offset=-250), loud_radius=300)
        r_volume = get_sound_volume(get_distance(origin, pos, x_offset=250), loud_radius=300)
        l_volume *= master_volume
        r_volume *= master_volume
        if l_volume <= 0 >= r_volume:
            self.channel.stop()
        else:
            self.channel.set_volume(l_volume, r_volume)
            if not self.channel.get_busy():
                self.channel.play(self.sound, loops=-1)

    def stop(self):
        self.channel.fadeout(200)


class CrowdSound:
    def __init__(self, channel=CROWD_CHANNEL, filename='crowd.ogg', master_volume=1.):
        if not pygame.mixer.get_init():
            return
        self.channel = pygame.mixer.Channel(channel)
        self.master_volume = master_volume
        self.stopped = True

        try:
            self.sound = pygame.mixer.Sound(getPath(trosnoth.data.sound, filename))
        except Exception:
            self.sound = None
            log.exception('Error loading sound file')

    def set_master_volume(self, master_volume):
        self.master_volume = master_volume

    def stop(self, fade_time):
        self.channel.fadeout(round(fade_time * 1000))
        self.stopped = True

    def set_volume(self, volume):
        if not pygame.mixer.get_init():
            return
        self.channel.set_volume(self.master_volume * volume)
        if self.stopped or not self.channel.get_busy():
            self.channel.play(self.sound, loops=-1)
            self.stopped = False


class SoundPlayer:
    instance = None

    def __init__(self):
        self.sounds_by_filename = {}
        self.looping_sounds: dict[object, LoopingSound] = {}
        self.sfx_volume = 1
        self.crowd_sound = CrowdSound()
        self._reservedChannels = max(CROWD_CHANNEL, *LOOPING_SOUND_CHANNELS) + 1
        if pygame.mixer.get_init():
            pygame.mixer.set_num_channels(32)
            pygame.mixer.set_reserved(self._reservedChannels)

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = SoundPlayer()
        return cls.instance

    def set_looping_sound_positions(self, origin, looping_sound_positions):
        pygame.mixer.set_reserved(self._reservedChannels)
        sounds = sorted(
            looping_sound_positions,
            key=lambda item: distance(origin, item[-1])
        )[:len(LOOPING_SOUND_CHANNELS)]

        free_channels = set(LOOPING_SOUND_CHANNELS)
        unapplied = []
        for id_, filename, position in sounds:
            if id_ in self.looping_sounds:
                sound = self.looping_sounds[id_]
                sound.update(origin, position, master_volume=self.sfx_volume)
                free_channels.discard(sound.channel_number)
            else:
                unapplied.append((id_, filename, position))

        for id_, filename, position in unapplied:
            self.looping_sounds[id_] = LoopingSound(
                filename,
                origin,
                position,
                channel=free_channels.pop(),
                master_volume=self.sfx_volume,
            )

        for channel in free_channels:
            pygame.mixer.Channel(channel).fadeout(200)

    def stop_looping_sounds(self):
        for looping_sound in self.looping_sounds.values():
            looping_sound.stop()

    def play_by_filename(self, filename, *, origin=None, pos=None):
        if not pygame.mixer.get_init():
            return

        try:
            sound = self.sounds_by_filename[filename]
        except KeyError:
            self.sounds_by_filename[filename] = sound = SoundAction(filename)
        sound.play(origin, pos, master_volume=self.sfx_volume)

    def set_sfx_volume(self, val):
        self.sfx_volume = val

    def set_crowd_master_volume(self, val):
        self.crowd_sound.set_master_volume(val)

    def set_crowd_current_volume(self, val):
        self.crowd_sound.set_volume(val)

    def stop_crowd_noise(self, fade_time=0.5):
        self.crowd_sound.stop(fade_time)
