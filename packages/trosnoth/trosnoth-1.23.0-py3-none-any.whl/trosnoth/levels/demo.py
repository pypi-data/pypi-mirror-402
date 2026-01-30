#!/usr/bin/env python3

if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', '..'))

    # Install the asyncio reactor as early as possible
    from trosnoth.aioreactor import declare_this_module_requires_asyncio_reactor
    declare_this_module_requires_asyncio_reactor()

from trosnoth.const import LEFT_SIDE_ROOM, RIGHT_SIDE_ROOM
from trosnoth.levels.base import play_level
from trosnoth.levels.standard import StandardLevel
from trosnoth.model.map import ZoneLayout, ZoneStep


class DemoLevel(StandardLevel):
    '''
    Example of how to write a custom level.
    '''

    def pre_sync_setup(self):
        super().pre_sync_setup()
        zones = ZoneLayout(symmetryEnforced=True)

        pos = zones.connectZone(zones.firstLocation, ZoneStep.NORTHEAST)
        pos = zones.connectZone(pos, ZoneStep.SOUTHEAST)
        pos = zones.connectZone(pos, ZoneStep.SOUTH)
        pos = zones.connectZone(pos, ZoneStep.SOUTHWEST)
        pos2 = zones.connectZone(pos, ZoneStep.NORTHWEST)
        zones.connectZone(pos2, ZoneStep.NORTH)

        pos = zones.connectZone(pos, ZoneStep.SOUTH)
        pos = zones.connectZone(pos, ZoneStep.SOUTHEAST)
        pos = zones.connectZone(pos, ZoneStep.NORTHEAST)
        pos = zones.connectZone(pos, ZoneStep.NORTH)
        zones.connectZone(pos, ZoneStep.NORTHWEST)

        pos = zones.connectZone(pos, ZoneStep.NORTHEAST)
        pos = zones.connectZone(pos, ZoneStep.NORTH)
        pos = zones.connectZone(pos, ZoneStep.NORTHWEST)
        zones.connectZone(pos, ZoneStep.SOUTHWEST)

        pos = zones.connectZone(pos, ZoneStep.NORTH)
        pos = zones.connectZone(pos, ZoneStep.NORTHWEST)
        pos = zones.connectZone(pos, ZoneStep.SOUTHWEST)
        zones.connectZone(pos, ZoneStep.SOUTH)

        left_team = self.world.teams[0]
        right_team = self.world.teams[1]
        self.world.set_map(
            zones, tag_team_pairs = ((LEFT_SIDE_ROOM, left_team), (RIGHT_SIDE_ROOM, right_team)))


if __name__ == '__main__':
    play_level(DemoLevel(), bot_count=9)
