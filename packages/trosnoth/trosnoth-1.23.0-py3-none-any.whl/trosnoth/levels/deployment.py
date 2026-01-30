#!/usr/bin/env python3

if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', '..'))

    # Install the asyncio reactor as early as possible
    from trosnoth.aioreactor import declare_this_module_requires_asyncio_reactor
    declare_this_module_requires_asyncio_reactor()

from trosnoth.levels.base import play_level
from trosnoth.levels.standard import StandardLevel
from trosnoth.model.map import ZoneStep, ZoneLayout


class DeploymentLevel(StandardLevel):
    def pre_sync_setup(self):
        super().pre_sync_setup()

        block_ratio = 0.8

        zones = ZoneLayout(symmetryEnforced=True)

        location = zones.firstLocation
        zones.add_standard_column(location, block_ratio, 5)
        location += ZoneStep.SOUTHEAST
        zones.add_standard_column(location, block_ratio, 4, 5)
        location += ZoneStep.NORTHEAST
        zones.add_standard_column(location, block_ratio, 5, 4)
        location += ZoneStep.SOUTHEAST
        zones.add_standard_column(location, block_ratio, 4, 5)
        location += ZoneStep.SOUTHEAST
        zones.add_standard_column(location, block_ratio, 3, 4)
        location += ZoneStep.SOUTHEAST
        zones.add_standard_column(location, block_ratio, 2, 3)
        location += ZoneStep.SOUTHEAST
        zones.add_standard_column(location, block_ratio, 1, 2)

        zones.makeEverywhereReachable()
        left_team, right_team = self.world.teams[:2]
        self.world.set_map(
            zones, tag_team_pairs=(('leftmost', left_team), ('rightmost', right_team)))

        leftmost = min(self.world.zones, key=lambda z: z.defn.pos[0])
        rightmost = max(self.world.zones, key=lambda z: z.defn.pos[0])
        for zone in self.world.zones:
            if zone not in (leftmost, rightmost):
                if zone.owner:
                    zone.owner.zoneLost()
                zone.owner = None
                zone.dark = False


if __name__ == '__main__':
    play_level(DeploymentLevel(), bot_count=9)
