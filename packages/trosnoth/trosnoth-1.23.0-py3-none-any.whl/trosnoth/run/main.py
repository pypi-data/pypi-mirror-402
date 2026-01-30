import functools

from trosnoth.utils.utils import run_async_main_function
from trosnoth.welcome.welcome import async_main


def launch_trosnoth(show_replay=None):
    run_async_main_function(functools.partial(async_main, show_replay=show_replay))
