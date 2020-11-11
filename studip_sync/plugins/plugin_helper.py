from studip_sync.config import CONFIG
from studip_sync.plugins import PluginError
from studip_sync.plugins.plugin_loader import PluginLoader


class PluginHelper(object):

    def __init__(self, plugin_name):
        self.plugin_name = plugin_name

    def enable(self):
        print("Enabling plugin: " + self.plugin_name)

        if self.plugin_name in CONFIG.plugins:
            print("Plugin is already enabled. To reconfigure call --reconfigure-plugin PLUGIN")
            return 1

        try:
            self._configure()
        except PluginError as e:
            print(e)
            return 1

        new_plugins = CONFIG.plugins
        new_plugins.append(self.plugin_name)
        CONFIG.update_plugins(new_plugins)

    def reconfigure(self):
        print("Reconfiguring plugin: " + self.plugin_name)

        if self.plugin_name not in CONFIG.plugins:
            print("Plugin is not enabled. To enable the plugin call --enable-plugin PLUGIN")
            return 1

        try:
            self._configure()
        except PluginError as e:
            print(e)
            return 1

    def _configure(self):
        plugin = PluginLoader.load_plugin(self.plugin_name, CONFIG.config_dir)

        plugin.hook_configure()

    def disable(self):
        print("Disabling plugin: " + self.plugin_name)

        if self.plugin_name not in CONFIG.plugins:
            print("Plugin is already disabled.")
            return 1

        new_plugins = CONFIG.plugins
        new_plugins.remove(self.plugin_name)
        CONFIG.update_plugins(new_plugins)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

