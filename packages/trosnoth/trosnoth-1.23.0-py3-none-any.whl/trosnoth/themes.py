'''
themes.py
This module defines the interface to the various different themes.
'''

import functools
import logging
import os
from math import pi
from pathlib import Path
from typing import Type

import pygame
from pygame.surface import Surface
import pygame.transform

from trosnoth import data
import trosnoth.data.themes     # noqa
from trosnoth.const import (
    BODY_BLOCK_SCREEN_SIZE, INTERFACE_BLOCK_SCREEN_SIZE, MAP_TO_SCREEN_SCALE, ROOM_SCREEN_SIZE,
)
from trosnoth.gui.fonts.font import Font, ScaledFont
from trosnoth.gui.framework.basics import SingleImage, Animation, SpriteSheetAnimation
from trosnoth.trosnothgui.common import setAlpha
from trosnoth.utils.unrepr import unrepr
from trosnoth.model.universe_base import NEUTRAL_TEAM_ID
from trosnoth.model.upgrades import ShopItem

BLOCK_BACKGROUND_COLOURKEY = (224, 192, 224)
x1 = INTERFACE_BLOCK_SCREEN_SIZE[0]
x2 = x1 + BODY_BLOCK_SCREEN_SIZE[0]
y = BODY_BLOCK_SCREEN_SIZE[1]
BLOCK_OFFSETS = {
    'top': (-x1, 0),
    'btm': (-x1, -y),
    'fwd': ((-x2, -y), (0, 0)),
    'bck': ((-x2, 0), (0, -y)),
}
del x1, x2, y

log = logging.getLogger(__name__)


def setToRed(surface):
    '''Inverts the colors of a pygame Screen'''
    surface.lock()

    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            r, g, b, a = surface.get_at((x, y))
            greyscale = r * 0.298 + g * 0.587 + b * 0.114
            surface.set_at((x, y), (greyscale, 0, 0, a))

    surface.unlock()


def colour_split_image(raw_img, result_size, colour):
    '''
    Used to apply team colours to images like room backgrounds.
    '''
    result = pygame.Surface(result_size, pygame.SRCALPHA)
    result.fill((0, 0, 0, 0))
    result.blit(
        raw_img, (0, 0),
        pygame.Rect((0, raw_img.get_height() - 2 * result_size[1]), result_size))

    temp = pygame.Surface(result_size, pygame.SRCALPHA)
    temp.fill(colour + (255,))
    temp.blit(
        raw_img, (0, 0),
        pygame.Rect((0, raw_img.get_height() - result_size[1]), result_size),
        special_flags=pygame.BLEND_RGBA_MULT)
    result.blit(temp, (0, 0))
    return result


class ThemeColours:
    pass


def cachedProperty(fn):
    @functools.wraps(fn)
    def spriteFunction(self):
        try:
            return self._store[fn]
        except KeyError:
            self._store[fn] = fn(self)
            return self._store[fn]
    return property(spriteFunction)


def cached(fn):
    @functools.wraps(fn)
    def spriteFunction(self, *args):
        try:
            return self._store[fn, args]
        except KeyError:
            self._store[fn, args] = fn(self, *args)
            return self._store[fn, args]
    return spriteFunction


def image(path, **kwargs):
    def imageFunction(self):
        return self.theme.loadSprite(path, sprites=self, **kwargs)
    return cachedProperty(imageFunction)


def reversibleImage(filename):
    @cached
    def accessor(self, reversed):
        if reversed:
            regular = accessor(self, False)
            return pygame.transform.flip(regular, True, False)
        return self.theme.loadSprite(filename, sprites=self)
    return accessor


def reversibleTeamColouredImage(filename):
    @cached
    def accessor(self, colour, reversed):
        if reversed:
            regular = accessor(self, colour, False)
            surface = pygame.transform.flip(regular, True, False)
            return surface

        if filename not in self._store:
            self._store[filename] = self.theme.loadSprite(filename, sprites=self)
        surface = self._store[filename].copy()
        solid = pygame.Surface(surface.get_rect().size)
        r, g, b = colour
        solid.fill((127 - r // 2, 127 - g // 2, 127 - b // 2))
        surface.blit(solid, (0, 0), special_flags=pygame.BLEND_SUB)
        surface.blit(surface, (0, 0), special_flags=pygame.BLEND_ADD)
        return surface

    return accessor


def images(paths, **kwargs):
    def imageFunction(self):
        return self.theme.loadSprites(paths, sprites=self, **kwargs)
    return cachedProperty(imageFunction)


def wrappedImage(path, **kwargs):
    def imageFunction(self):
        return SingleImage(self.theme.loadSprite(path, sprites=self, **kwargs))
    return cachedProperty(imageFunction)


def getTeamId(team):
    if team is None:
        return NEUTRAL_TEAM_ID
    return team.id


class TeamColouredImage:
    def __init__(self, prefix):
        self.theme = None
        self.prefix = prefix
        self.baseImg = None
        self.teamImg = None
        self.cached = {}

    def init(self, theme):
        self.theme = theme
        self.baseImg = self.theme.loadSprite(self.prefix + '-base.png')
        self.teamImg = self.theme.loadSprite(self.prefix + '-overlay.png')

    def get(self, colour):
        if colour not in self.cached:
            self.loadImage(colour)
        return self.cached[colour]

    def loadImage(self, colour):
        result = Surface(self.baseImg.get_size(), pygame.SRCALPHA)
        result.fill((0, 0, 0, 0))
        result.blit(self.baseImg, (0, 0))

        temp = Surface(self.baseImg.get_size(), pygame.SRCALPHA)
        temp.fill(colour + (255,))
        temp.blit(self.teamImg, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        result.blit(temp, (0, 0))

        self.cached[colour] = result


class ThemeSprites(object):
    def __init__(self, theme):
        self.theme = theme
        self._store = {}
        self.orbs = TeamColouredImage('orbs')
        self._precache_keys = set()

    def init(self):
        self.orbs.init(self.theme)

    def clearCache(self):
        self._store = {key: self._store[key] for key in self._precache_keys}

    def precache(self):
        existing_keys = set(self._store)

        # Precalculate the following cache keys so they don't take too
        # long during gameplay
        self.grenade_explosion_sprite_sheet()

        self._precache_keys = set(self._store) - existing_keys

    static = image('static.png')
    smallCoin = image('smallstar.png')
    coin = image('star0.png')
    coinImages = images([
        'star0.png', 'star1.png', 'star2.png', 'star3.png',
        'star4.png', 'star3.png', 'star2.png', 'star1.png',
    ])
    bigCoinImages = images([
        'bigCoin0.png', 'bigCoin1.png', 'bigCoin2.png', 'bigCoin3.png',
        'bigCoin4.png', 'bigCoin3.png', 'bigCoin2.png', 'bigCoin1.png',
    ])
    grenade = image('grenade.png')
    scenery = image('scenery.png', colourkey=None)

    gunIcon = wrappedImage('gun.png')

    shieldImages = images([
        'shieldImage1.png', 'shieldImage2.png', 'shieldImage3.png',
        'shieldImage2.png'])

    orb_progress_image = image('orb-progress.png')
    playerSpriteSheet = reversibleImage('player.png')
    playerHeadSheet = reversibleTeamColouredImage('heads.png')
    player_highlight_template = image('playerhighlight.png')
    ghost_sprite_sheet = reversibleTeamColouredImage('ghost.png')
    crosshairs_sprite_sheet = image('crosshairs.png')
    grenade_explosion_sprite_sheet_small = image('explosion-grenade.png')
    shoxwave_explosion_sprite_sheet = image('explosion-shoxwave.png')
    mine_explosion_sprite_sheet = image('explosion-mine.png')
    mine_sprite_sheet = image('mine.png')
    orb_indicator_sheet = image('orb-indicators.png')
    zones = image('zones.png')

    @cached
    def grenade_explosion_sprite_sheet(self):
        small_sheet = self.grenade_explosion_sprite_sheet_small
        w, h = small_sheet.get_size()
        return pygame.transform.smoothscale(small_sheet, (w * 5, h * 5))

    def coinAnimation(self, timer):
        return Animation(0.07, timer, *self.coinImages)

    def bigCoinAnimation(self, timer):
        return Animation(0.07, timer, *self.bigCoinImages)

    def mine(self, angle, team_colour=None):
        sheet = self.coloured_mine_sprite_sheet(team_colour)
        j, i = divmod(round(angle * 32 / pi) % 64, 8)
        return sheet.subsurface(
            get_sprite_sheet_source_rect(i, j, sheet=sheet, cell_map_width=20, cell_map_height=20))

    @cached
    def coloured_mine_sprite_sheet(self, team_colour=None):
        if team_colour is None:
            return self.mine_sprite_sheet
        return colour_split_image(self.mine_sprite_sheet, (200, 200), team_colour)

    def player_highlight_for_team(self, team):
        return self.player_highlight_by_colour((255, 255, 255) if team is None else team.colour)

    @cached
    def player_highlight_by_colour(self, colour):
        return colour_split_image(self.player_highlight_template, (63, 75), colour)

    @cached
    def head_pic(self, head):
        from trosnoth.trosnothgui.ingame.sprites import (
            PlayerDrawer, PlayerSprite)
        w, h = PlayerSprite.canvasSize
        h += 6  # Add some breathing space
        result = pygame.Surface((w, h), pygame.SRCALPHA)
        drawer = PlayerDrawer(self.theme, head=head)
        drawer.render(result)
        return result

    @cached
    def zoneHighlight(self, team, scale):
        if team is None:
            colour = self.theme.colours.borderline_minimap_highlight
        else:
            colour = team.colour
        size = int(300. / scale + 0.5)
        result = pygame.Surface((2 * size, 2 * size))
        result.fill((0, 0, 0))
        result.set_colorkey((0, 0, 0))
        pygame.draw.circle(result, colour, (size, size), size)
        result.set_alpha(64)
        return result

    @cached
    def bigZoneLetter(self, letter):
        font = self.theme.app.screenManager.fonts.bigZoneFont
        result = font.render(
            self.theme.app, letter, True, self.theme.colours.bigZoneLetter)
        setAlpha(result, 128)
        return result

    @cached
    def ghostIcon(self, team):
        return SingleImage(self.theme.loadTeamSprite(
            'ghost1', getTeamId(team), self))

    @cached
    def trosball_image(self):
        return self.theme.loadSprite('trosball.png', sprites=self)

    @cached
    def trosballAnimation(self, timer):
        frame0 = self.trosball_image()
        scale = 25. / max(frame0.get_size())
        frames = []
        for theta in range(0, 360, 15):
            frames.append(pygame.transform.rotozoom(frame0, -theta, scale))
        return Animation(0.05, timer, *frames)

    @cached
    def trosballWarningAnimation(self, timer, always_red=False):
        frame0 = self.theme.loadSprite('trosball.png', sprites=self)
        scale = 25. / max(frame0.get_size())
        frames = []
        for theta in range(0, 360, 15):
            surface = pygame.transform.rotozoom(frame0, -theta, scale)
            # Every 90 degrees, invert the colours
            if always_red or (theta / 45) % 2 < 1:
                setToRed(surface)
            frames.append(surface)
        return Animation(0.05, timer, *frames)

    def grenade_explosion(self, timer):
        return SpriteSheetAnimation(1 / 60, timer, self.grenade_explosion_sprite_sheet(), 6, 6)

    def shoxwave_explosion(self, timer):
        return SpriteSheetAnimation(1 / 60, timer, self.shoxwave_explosion_sprite_sheet, 6, 5)

    def trosballExplosion(self, timer):
        return Animation(0.07, timer, self.explosionFrame(0))

    def mine_explosion(self, timer):
        return SpriteSheetAnimation(1 / 60, timer, self.mine_explosion_sprite_sheet, 10, 6)

    @cached
    def explosionFrame(self, frame):
        return self.theme.loadSprite(
            'explosion%d.png' % (frame + 1,), sprites=self)

    def team_grenade(self, team):
        return self.coloured_grenade((0, 0, 0) if team is None else team.colour)

    @cached
    def coloured_grenade(self, colour):
        return colour_split_image(self.grenade, (45, 38), colour)

    def shop_item_image(self, item_class: Type[ShopItem]):
        return self.path_image(item_class.icon_path)

    def disabled_shop_item(self, item_class: Type[ShopItem]):
        return self.disabled_path_image(item_class.icon_path)

    def category_image(self, path='upgrade-unknown.png'):
        return self.path_image(path)

    def disabled_category_image(self, path='upgrade-unknown.png'):
        return self.disabled_path_image(path)

    @cached
    def path_image(self, path):
        return self.theme.loadSprite(path, sprites=self)

    @cached
    def disabled_path_image(self, path):
        image = self.path_image(path).copy()
        fade = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        fade.fill((128, 128, 128, 128))
        image.blit(fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return image

    @cached
    def blockTopMostPicture(self, block_layout):
        if not block_layout:
            return None
        if block_layout.reversed:
            flipped = self.blockTopMostPicture(block_layout.mirrorLayout)
            if flipped is None:
                return None
            return pygame.transform.flip(flipped, True, False)

        block_path = Path(block_layout.filename)
        path = block_path.with_name(block_path.stem + '-topmost.png')
        if path.is_file():
            return pygame.image.load(path).convert_alpha()
        return None

    def blockBackground(self, block):
        bd = block.defn

        def zone_colour(zone):
            if zone.owner and zone.dark:
                return zone.owner.colour
            else:
                return NEUTRAL_TEAM_ID

        if bd.kind in ('top', 'btm'):
            if bd.zone is None:
                return None
            owners = (zone_colour(block.zone),)
        else:
            if bd.zone1 is None:
                owner1 = None
            else:
                owner1 = zone_colour(block.zone1)
            if bd.zone2 is None:
                owner2 = None
            else:
                owner2 = zone_colour(block.zone2)
            owners = (owner1, owner2)
        result = self._getBlockFromStoreOrBuild(bd.kind, owners)
        return result

    def _getBlockFromStoreOrBuild(self, kind, owners):
        try:
            return self._store['blockBackground', kind, owners]
        except KeyError:
            self._buildBlockBackground(kind, owners)
            return self._store['blockBackground', kind, owners]

    def getFilledBlockBackground(self, block, owner):
        colour = owner.colour if owner is not None else NEUTRAL_TEAM_ID
        if block.defn.kind in ('top', 'btm'):
            if block.defn.zone is None:
                return None
            else:
                owners = (colour,)
        else:
            owner1 = colour if block.zone1 is not None else None
            owner2 = colour if block.zone2 is not None else None
            owners = (owner1, owner2)
        return self._getBlockFromStoreOrBuild(block.defn.kind, owners)

    def _buildBlockBackground(self, kind, owner_colours):
        '''
        Loads and caches zone background.

        Note: None in owner_colours means no zone, NEUTRAL_TEAM_ID means
            neutral.
        '''

        flags = pygame.SRCALPHA

        raw_image = self.zones
        coloured_images = {}
        for colour in owner_colours:
            if colour is NEUTRAL_TEAM_ID:
                coloured_images[colour] = raw_image.subsurface((0, 0), ROOM_SCREEN_SIZE)
            elif colour is not None:
                coloured_images[colour] = colour_split_image(raw_image, ROOM_SCREEN_SIZE, colour)

        def storePic(kind, owners, pic):
            self._store['blockBackground', kind, owners] = pic

        if self.theme.app.settings.display.parallax_backgrounds:
            fill_colour = (0, 0, 0, 0)
        else:
            fill_colour = BLOCK_BACKGROUND_COLOURKEY

        if kind in ('top', 'btm'):
            for colour in owner_colours:
                zone_pic = coloured_images[colour]
                pic = pygame.Surface(BODY_BLOCK_SCREEN_SIZE, flags)
                pic.fill(fill_colour)
                pic.blit(zone_pic, BLOCK_OFFSETS[kind])
                storePic(kind, (colour,), pic)

        elif kind in ('fwd', 'bck'):
            colour1, colour2 = owner_colours
            pic = pygame.Surface(
                INTERFACE_BLOCK_SCREEN_SIZE, flags)
            pic.fill(fill_colour)
            if colour1 is not None:
                pic.blit(
                    coloured_images[colour1], BLOCK_OFFSETS[kind][0])
            if colour2 is not None:
                pic.blit(
                    coloured_images[colour2], BLOCK_OFFSETS[kind][1])
            storePic(kind, (colour1, colour2), pic)

    @cached
    def netOrb(self):
        return self.theme.loadSprite('netOrb.png', sprites=self)

    def orb_indicator(self, kind, team):
        team_colour = team.colour if team else None
        sheet = self.coloured_orb_indicator_sheet(team_colour)
        i = 0 if kind == 'F' else 1 if kind == 'H' else 2
        return sheet.subsurface(
            get_sprite_sheet_source_rect(i, 0, sheet=sheet, cell_map_width=52, cell_map_height=52))

    @cached
    def coloured_orb_indicator_sheet(self, team_colour=None):
        if team_colour is None:
            return self.orb_indicator_sheet
        return colour_split_image(self.orb_indicator_sheet, (3 * 65, 65), team_colour)

    @cached
    def orb_progress(self, colour):
        return colour_split_image(self.orb_progress_image, (6625, 750), colour)


def get_sprite_sheet_source_rect(
        x_index, y_index, *, sheet=None, cell_map_width, cell_map_height, flip=False):
    cell_width = cell_map_width * MAP_TO_SCREEN_SCALE
    cell_height = cell_map_height * MAP_TO_SCREEN_SCALE
    if flip:
        x_index = sheet.get_width() // cell_width - 1 - x_index

    x = x_index * cell_width
    y = y_index * cell_height
    return pygame.Rect(x, y, cell_width, cell_height)


class Theme(object):
    def __init__(self, app):
        self.app = app
        self.paths = []
        self.colours = ThemeColours()
        self.sprites = ThemeSprites(self)
        self.setTheme('default')
#        self.setTheme(app.settings.display.theme)

        app.settings.display.on_detail_level_changed.addListener(
            self.detailChanged)

    def detailChanged(self):
        self.sprites.clearCache()

    def setTheme(self, themeName):
        '''
        Sets the theme to the theme with the given name.
        '''
        self.name = themeName
        self.paths = [data.getPath(data.user), data.getPath(data)]

        def insertPath(p):
            if os.path.exists(p):
                self.paths.insert(0, p)
        insertPath(data.getPath(data.themes, themeName))
        insertPath(data.getPath(data.user, 'themes', themeName))
        self.initFonts()
        self.initColours()
        self.sprites.init()

    def initColours(self):
        colourPath = self.getPath('config', 'colours.cfg')
        colourData = self._getColourData(colourPath)
        defaultColours = self._getColourData(
            data.getPath(data, 'config', 'colours.cfg'))

        for colourName, colour in defaultColours.items():
            if colourName in colourData:
                colour = colourData[colourName]
            setattr(self.colours, colourName, colour)

    def initFonts(self):
        for fontName, defaultDetails in DEFAULT_FONTS.items():
            fontFile, size, bold = defaultDetails.unpack()

            if fontName in UNSCALED_FONTS:
                font = Font(fontFile, size, bold)
            else:
                font = ScaledFont(fontFile, size, bold)
            self.app.fonts.addFont(fontName, font)

    def _getColourData(self, filepath):
        try:
            with open(filepath) as f:
                lines = f.readlines()
        except IOError:
            return {}

        result = {}
        for line in lines:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue
            bits = line.split('=', 1)
            # Perform basic checks
            invalid = False
            if len(bits) != 2:
                invalid = True
            else:
                try:
                    colour = unrepr(bits[1])
                    if type(colour) is str:
                        colour = colour.strip("'")
                except:
                    invalid = True
                else:
                    if colour in list(result.keys()):
                        colour = result[colour]
                    else:
                        if (not isinstance(colour, tuple) or len(colour) < 3 or
                                len(colour) > 4):
                            invalid = True
            if invalid:
                log.warning('Invalid colour config line: %r', line)
            else:
                result[bits[0].strip()] = colour
        return result

    def getPath(self, *pathBits):
        '''
        Returns a path to the given themed file, looking in the following
        locations:
         1. User theme files for the current theme.
         2. Built-in theme files for the current theme.
         3. Default files.
        '''
        for path in self.paths:
            path = os.path.join(path, *pathBits)
            if os.path.isfile(path):
                return path
        raise IOError('file not found: %s' % (os.path.join(*pathBits),))

    def loadSprite(
            self, filename, colourkey=None, sprites=None,
            borders=(127, 127, 127)):
        '''
        Loads the sprite with the given name. A colour key of None may be given
        to disable colourkey transparency.
        '''
        filepath = self.getPath('sprites', filename)
        image = pygame.image.load(filepath)

        alpha = (colourkey is None)
        if alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
            image.set_colorkey(colourkey)

        return image

    def loadSprites(self, filenames, sprites, **kwargs):
        images = []
        for filename in filenames:
            images.append(self.loadSprite(filename, sprites=sprites, **kwargs))
        return images

    def loadTeamSprite(self, filename, teamId, sprites, **kwargs):
        '''
        teamId must be 'A' or 'B'.
        If teamId is 'A', grabs <filename>.png
        If teamId is 'B', grabs <filename>b.png if it exists, or <filename>.png
            otherwise.
        '''
        if teamId == b'B':
            fullFilename = '%sb.png' % (filename,)
            try:
                filepath = self.getPath('sprites', fullFilename)
                if not os.path.isfile(filepath):
                    fullFilename = '%s.png' % (filename,)
            except IOError:
                fullFilename = '%s.png' % (filename,)
        else:
            fullFilename = '%s.png' % (filename,)

        return self.loadSprite(fullFilename, sprites=sprites, **kwargs)

    def loadTeamSprites(self, filenames, teamId, sprites, **kwargs):
        images = []
        for filename in filenames:
            images.append(self.loadTeamSprite(
                filename, teamId, sprites, **kwargs))
        return images


class F(object):

    def __init__(self, fontFile, size, bold=False):
        self.fontFile = fontFile
        self.size = size
        self.bold = bold

    def unpack(self):
        return (self.fontFile, self.size, self.bold)

DEFAULT_FONTS = {
    'default': F('Junction.ttf', 24),
    'defaultTextBoxFont': F('Junction.ttf', 20),
    'unobtrusivePromptFont': F('Junction.ttf', 28),
    'chatFont': F('Junction.ttf', 25),
    'newChatFont': F('Vera.ttf', 14, True),

    'winMessageFont': F('Junction.ttf', 32),

    'nameFont': F('Junction.ttf', 20),
    'countdownFont': F('Junction.ttf', 16),

    'hugeMenuFont': F('Junction.ttf', 54),
    'bigMenuFont': F('Junction.ttf', 36),
    'mainMenuFont': F('Junction.ttf', 36),
    'serverListFont': F('Junction.ttf', 24),
    'timerFont': F('Junction.ttf', 32),
    'consoleFont': F('orbitron-light.ttf', 20),
    'ampleMenuFont': F('Junction.ttf', 40),
    'mediumMenuFont': F('Junction.ttf', 36),
    'menuFont': F('Junction.ttf', 30),
    'smallMenuFont': F('Junction.ttf', 20),
    'ingameMenuFont': F('FreeSans.ttf', 12),
    'gameMenuFont': F('FreeSans.ttf', 24),
    'game_options_font': F('FreeSans.ttf', 16),
    'miniMapLabelFont': F('FreeSans.ttf', 10),
    'gameInfoFont': F('FreeSans.ttf', 14),
    'gameInfoTitleFont': F('FreeSans.ttf', 20),
    'coinsDisplayFont': F('FreeSans.ttf', 20),
    'cost_font': F('FreeSans.ttf', 14),
    'versionFont': F('Junction.ttf', 16),
    'scrollingButtonsFont': F('Junction.ttf', 24),
    'zoneBarFont': F('Junction.ttf', 24),
    'dialogButtonFont': F('KLEPTOCR.TTF', 50),
    'serverSelectionCheckboxesFont': F('Junction.ttf', 28),

    'messageFont': F('Junction.ttf', 16),
    'leaderboardFont': F('FreeSans.ttf', 14),

    'smallNoteFont': F('Junction.ttf', 22),
    'labelFont': F('Junction.ttf', 32),
    'captionFont': F('FreeSans.ttf', 35),
    'keymapFont': F('Junction.ttf', 20),
    'keymapInputFont': F('Junction.ttf', 20),

    'achievementTitleFont': F('orbitron-light.ttf', 21),
    'achievementNameFont': F('Junction.ttf', 18),

    'connectionFailedFont': F('Junction.ttf', 32),

    'creditsFont': F('Junction.ttf', 24),
    'creditsH2': F('KLEPTOCR.TTF', 48),
    'creditsH1': F('KLEPTOCR.TTF', 60),

    'bigZoneFont': F('FreeSansBold.ttf', 64),
}

UNSCALED_FONTS = {
    'nameFont',
    'ingameMenuFont',
    'gameMenuFont',
    'miniMapLabelFont',
    'gameInfoFont',
    'gameInfoTitleFont',
    'leaderboardFont',
    'newChatFont',
    'winMessageFont',
    'bigZoneFont',
}
