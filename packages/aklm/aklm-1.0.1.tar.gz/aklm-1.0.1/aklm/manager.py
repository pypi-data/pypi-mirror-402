"""Entry point for AKLM utility"""
import asyncio
import subprocess
import logging
from i3ipc import aio
import i3ipc

from aklm import config


CONFIG = config.Configuration()
CONFIG.configure_log('aklm')
_log = logging.getLogger('aklm')


def switch_layout(layout: str):
    """Actually modify keyboard layout"""
    command = [CONFIG.setxkbmap] + layout.split(' ')
    _log.info('Switch to %s with command `%s`', layout, ' '.join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        _log.error('Fail to change layout: %s', err)


async def main():
    """Main async method"""
    current_mapping = CONFIG.default_layout

    CONFIG.banner(_log)

    def on_focus(
            _connection: aio.Connection,
            event: i3ipc.events.IpcBaseEvent
    ):
        """Method to trigger when focus reach a new window"""
        nonlocal current_mapping
        ipc_data = getattr(event, 'ipc_data', None)
        if ipc_data is None:
            _log.warning('Event has no ipc_data: %s', event)
            return
        properties = ipc_data['container']['window_properties']
        _log.debug('Focus now on %s', properties['class'])

        new_mapping = CONFIG.get_layout(properties['class'])
        if current_mapping != new_mapping:
            switch_layout(new_mapping)
            current_mapping = new_mapping
        else:
            _log.debug(
                'Layout for %s is still %s, no change needed',
                properties['class'],
                current_mapping
            )

    connection = await aio.Connection(auto_reconnect=True).connect()
    connection.on(i3ipc.Event.WINDOW_FOCUS, on_focus)

    await connection.main()


def _start():
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        _log.info('Exiting on user request')
