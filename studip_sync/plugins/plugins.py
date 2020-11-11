
from studip_sync.config import CONFIG
from studip_sync.plugins import PluginList

try:
    PLUGINS = PluginList(CONFIG.plugins, CONFIG.config_dir)
except Exception as e:
    print(str(e))
    print("Aborting...")
    exit(1)
