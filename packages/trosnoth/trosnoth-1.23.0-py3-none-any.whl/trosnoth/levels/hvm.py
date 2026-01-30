# Trosnoth (UberTweak Platform Game)
# Copyright (C) Joshua D Bartlett
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import random
import logging

from twisted.internet import defer

from trosnoth.const import DEFAULT_BOT_DIFFICULTY
from trosnoth.levels.maps import SmallMap
from trosnoth.messages import SetPlayerTeamMsg

log = logging.getLogger(__name__)


BOTS_PER_HUMAN = 1  # Option exists for debugging with many bots


class HumansVsMachinesBotManager(object):
    '''
    Injects bots into the game as needed for a humans vs. machines game.
    '''
    def __init__(self, universe, reverse):
        self.universe = universe

        self.enabled = False
        self.botSurplus = 0
        self.detachingAgents = set()

        if reverse:
            self.bot_team = universe.teams[0]
            self.human_team = universe.teams[1]
        else:
            self.bot_team = universe.teams[1]
            self.human_team = universe.teams[0]

        self.agents = set()

    @defer.inlineCallbacks
    def starting_soon(self):
        self.enabled = True
        self.universe.uiOptions.set(
            team_ids_humans_can_join=[self.human_team.id],
        )
        self.move_players_to_correct_team()

        bots = len([p for p in self.universe.players if p.bot])
        humans = len(self.universe.players) - bots

        self.botSurplus = bots - humans * BOTS_PER_HUMAN
        yield self._addBots()

    def move_players_to_correct_team(self):
        for player in self.universe.players:
            correct_team = self.bot_team if player.bot else self.human_team
            if player.team != correct_team:
                self.universe.sendServerCommand(
                    SetPlayerTeamMsg(player.id, correct_team.id))
                pos = self.universe.select_good_respawn_zone_for_team(player.team).centre
                self.universe.magically_move_player_now(player, pos, alive=False)

    @defer.inlineCallbacks
    def playerAdded(self, player):
        if not self.enabled:
            return
        if player.bot:
            if player.agent not in self.agents:
                # Someone's directly added a different bot
                self.botSurplus += 1
                self._removeBots()
        else:
            self.botSurplus -= BOTS_PER_HUMAN
            yield self._addBots()

    @defer.inlineCallbacks
    def removingPlayer(self, player):
        if not self.enabled:
            return

        if player.bot:
            if player.agent in self.agents:
                # Bot was booted, not by us
                self.agents.discard(player.agent)
                player.agent.stop()
                self.universe.game.detachAgent(player.agent)

            if player.agent in self.detachingAgents:
                self.detachingAgents.discard(player.agent)
            else:
                self.botSurplus -= 1
                yield self._addBots()
        else:
            self.botSurplus += BOTS_PER_HUMAN
            self._removeBots()

    @defer.inlineCallbacks
    def _addBots(self):
        game = self.universe.game
        bot_name = ''
        if game.serverInterface:
            difficulty = game.serverInterface.get_machines_difficulty()
            bot_name = game.serverInterface.get_machines_bot_name()
            extra_bot_count = game.serverInterface.get_extra_bot_count()
        else:
            difficulty = DEFAULT_BOT_DIFFICULTY
            extra_bot_count = 0

        if not bot_name:
            bot_name = self._get_default_bot_name()

        while self.botSurplus < extra_bot_count:
            agent = yield game.addBot(bot_name, team=self.bot_team, difficulty=difficulty)
            self.agents.add(agent)
            self.botSurplus += 1

    def _get_default_bot_name(self):
        from trosnoth.levels.standard import StandardLevel
        level = self.universe.scenarioManager.level
        if isinstance(level, StandardLevel):
            map_object = level.level_options.get_map(level)
            if isinstance(map_object, SmallMap):
                # If we're on a 1v1 map, use SilverBot instead of RangerBot
                return 'silver'
        return 'ranger'

    def _removeBots(self):
        game = self.universe.game
        extra_bot_count = game.serverInterface.get_extra_bot_count() if game.serverInterface else 0

        while self.botSurplus > extra_bot_count:
            if not self.agents:
                return
            agent = random.choice(list(self.agents))
            self.agents.discard(agent)
            self.detachingAgents.add(agent)
            self.botSurplus -= 1
            agent.stop()
            game.detachAgent(agent)

    def getTeamToJoin(self, preferred_team, bot):
        if bot:
            return self.bot_team
        return self.human_team

    def stop(self):
        self.enabled = False
        while self.agents:
            agent = self.agents.pop()
            agent.stop()
            self.universe.game.detachAgent(agent)
