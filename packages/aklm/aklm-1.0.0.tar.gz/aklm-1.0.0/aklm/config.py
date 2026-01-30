"""Configuration class"""
import os
import logging
import configparser


class Configuration():
    """Main configuration class reader"""
    _log = logging.getLogger(__file__)
    LOGGINGLEVEL = {
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    def __init__(self):
        # Look for configuration in $XDG_CONFIG_HOME/aklm/aklm.ini
        # (if XDG_CONFIG_HOME is not set, fallback to $HOME/.config)
        local_config_file = os.path.join(
            os.environ.get(
                'XDG_CONFIG_HOME',
                os.path.join(
                    os.environ.get('HOME', '/root'),
                    '.config'
                )
            ),
            'aklm',
            'aklm.ini'
        )

        # Look for configuration in all XDG conf folder in aklm.ini file
        # (if XDG_CONFIG_DIRS is not set, fallback to /etc/xdg)
        # NOTE: folder list is reversed since XDG_CONFIG_DIRS is
        # preference-ordered, the most preferred should be parsed at the end
        # to allow proper configuration inheriteance.
        config_dirs = os.environ.get(
            'XDG_CONFIG_DIRS',
            '/etc/xdg'
        ).split(':')[::-1]
        generic_config_files = [
            os.path.join(folder, 'aklm.ini')
            for folder in config_dirs
        ]
        self.config_files = generic_config_files + [local_config_file]
        self._log.debug("Will use configuration in %r", self.config_files)

        self.config = configparser.ConfigParser()
        self.__set_default()

        for file in self.config_files:
            self.__read_single_file(file)

    def __read_single_file(self, file):
        self.config.read(file)

    def __set_default(self):
        self.config.add_section('general')
        # TODO: here, default_layout is set to fr by default BUT it could be
        # wise to auto-detect default layout based on system configuration
        self.config['general']['default_layout'] = 'fr'
        self.config['general']['setxkbmap'] = '/usr/bin/setxkbmap'
        self.config.add_section('log')
        self.config['log']['level'] = 'info'
        self.config.add_section('layout')

    def get_layout(self, window_class):
        """Retrieve layout associated to given window_class"""
        return self.config['layout'].get(
            window_class,
            self.config['general']['default_layout']
        )

    def configure_log(self, logger=None):
        """Reconfigure logger"""
        if logger is None:
            log = logging.getLogger()
        else:
            log = logging.getLogger(logger)
        log.handlers = []
        log.setLevel(
            self.LOGGINGLEVEL.get(self.config['log']['level'], 'info')
        )
        consoleformatter = logging.Formatter('%(levelname)s: %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(consoleformatter)
        log.addHandler(stream_handler)

    @property
    def default_layout(self):
        """Configured default layout"""
        return self.config['general']['default_layout']

    @property
    def setxkbmap(self):
        """Get complete path of setxkbmap"""
        return self.config['general']['setxkbmap']
