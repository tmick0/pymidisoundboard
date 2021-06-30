import os.path

import yaml
try:
    from yaml import CLoader as yamlLoader
    from yaml import CDumper as yamlDumper
except:
    from yaml import Loader as yamlLoader
    from yaml import Dumper as yamlDumper

default_config_location = os.path.expanduser("~/.pymidisoundboard.yml")

class config (object):
    def __init__(self, location, dict):
        if 'pads' in dict and not 'banks' in dict:
            dict['banks'] = [{'pads': dict['pads'], 'cc': 0}]
            del dict['pads']
        self.location = location
        self.dict = dict

    def save(self):
        with open(self.location, 'w') as fh:
            yaml.dump(self.dict, fh)

    @classmethod
    def load(cls, filename=default_config_location):
        if os.path.exists(filename):
            with open(filename, 'r') as fh:
                return cls(filename, yaml.load(fh, Loader=yamlLoader))
        return cls(filename, {'ui': []})
