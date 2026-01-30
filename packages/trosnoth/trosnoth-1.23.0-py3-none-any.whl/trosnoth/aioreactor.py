# Trosnoth (Ubertweak Platform Game)
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
# 02110-1301, USA
import asyncio
import os
import sys
import traceback

from twisted.internet import asyncioreactor


def install_asyncio_reactor():
    '''
    Installs the asyncio/Twisted main loop. This will not work if a
    different Twisted reactor has already been installed.
    '''
    if sys.platform == 'win32':
        # This is required because the deafult event loop doesn't support
        # add_reader() / add_writer() on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncioreactor.install()

    if sys.platform == 'win32':
        # This is needed for Qt on Windows
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()


_twisted_reactor_intentionally_chosen = False


def declare_twisted_reactor_was_intentionally_chosen():
    '''
    Use this if you need to import a module that calls
    declare_this_module_requires_asyncio_reactor, but you don't want to
    install the asyncio/Twisted main loop.
    '''
    global _twisted_reactor_intentionally_chosen
    _twisted_reactor_intentionally_chosen = True


def declare_this_module_requires_asyncio_reactor():
    '''
    This should be called before any direct or indirect Twisted imports
    in any module that requires the asyncio/Twisted main loop to be
    installed.

    If declare_twisted_reactor_was_intentionally_chosen() has been
    previously called, this call will do nothing.
    Otherwise, this function will install the asyncio/Twisted main
    loop if possible, and raise RuntimeError otherwise (e.g., if a
    different Twisted reactor has already been installed.)
    '''
    if _twisted_reactor_intentionally_chosen:
        return

    reactor = sys.modules.get('twisted.internet.reactor')
    if not reactor:
        install_asyncio_reactor()
        return

    if not isinstance(reactor, asyncioreactor.AsyncioSelectorReactor):
        raise RuntimeError(
            'Could not install the asyncio/Twisted main loop because a Twisted reactor has '
            'already been installed. You can fix this by:\n'
            ' * calling declare_this_module_requires_asyncio_reactor() before any Twisted imports '
            f'(probably early in {traceback.extract_stack()[0].filename})\n'
            ' * if you really do not want the asyncio/Twisted main loop to be installed, '
            'call declare_twisted_reactor_was_intentionally_chosen() before this import'
        )

