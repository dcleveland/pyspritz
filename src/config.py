"""Configuration module."""
from configparser import Configparser
import inject

class SpritzConfig:
    """Configuration class for Spritzpy GUI."""
    section = "NOTSET"

    def __init__(self, config=None):
        assert isinstance(config, ConfigParser)
        section = self.section
        
        if not config.has_section(section):
            raise Exception('section %s not found in config'%section)
            
        self.is_sandbox = config.getboolean('general','is_sandbox') \
            if config.has_option('general','is_sandbox') else  False
        
        self.api_key = config.get(section,'key') \
            if config.has_option(section,'key') else None
        self.secret = config.get(section,'secret') \
            if config.has_option(section,'secret') else None
        self.min_equity_to_position_ratio = config.get(section,'min_equity_to_position_ratio') \
            if config.has_option(section,'min_equity_to_position_ratio') else  Decimal('0.3333')
        self.default_leverage = config.getint(section,'default_leverage') \
            if config.has_option(section,'default_leverage') else self.default_leverage
        self.currency_pairs = config.get(section,'currency_pairs') \
            if config.has_option(section,'currency_pairs') else  None
        self.password = config.get(section, 'password') \
            if config.has_option(section, 'password') else None
        self.base_id = config.get(section, 'base_id') \
            if config.has_option(section, 'base_id') else None
        
        
    def reload(self):
        self.__init__(self.exchange)
