import importlib


class PluginLoader(object):
    @staticmethod
    def load_plugin(plugin_name, config_path):
        print("Loading plugin: " + plugin_name)
        plugin = importlib.import_module("." + plugin_name, "studip_sync.plugins")
        return plugin.Plugin(config_path)
