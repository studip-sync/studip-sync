import importlib

from studip_sync.plugins import PluginError

PACKAGE = "studip_sync.plugins"

class PluginLoader(object):
    @staticmethod
    def load_plugin(plugin_name, config_path):
        print("Loading plugin: " + plugin_name)
        relative_plugin_name = "." + plugin_name
        if importlib.util.find_spec(relative_plugin_name, package=PACKAGE) is None:
            raise PluginError("Plugin doesn't exist!")

        plugin = importlib.import_module(relative_plugin_name, PACKAGE)
        return plugin.Plugin(config_path)
