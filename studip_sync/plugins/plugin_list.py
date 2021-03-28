from studip_sync.plugins.plugin_loader import PluginLoader


class PluginList(list):

    def __init__(self, plugins=None, config_path=""):
        super(PluginList, self).__init__()

        if plugins is None:
            plugins = []

        for plugin_name in plugins:
            plugin = PluginLoader.load_plugin(plugin_name, config_path)

            self.append(plugin)

    def hook(self, hook_name, *args, **kwargs):
        for plugin in self:
            getattr(plugin, hook_name)(*args, **kwargs)
