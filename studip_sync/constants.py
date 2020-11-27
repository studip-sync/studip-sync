from studip_sync.logins import LoginPreset
from studip_sync.logins.general import GeneralLogin
from studip_sync.logins.shibboleth import ShibbolethLogin

URL_BASEURL_DEFAULT = "https://studip.uni-goettingen.de"
CONFIG_FILENAME = "config.json"
LOGIN_PRESETS = [
    LoginPreset(name="University of Göttingen", base_url="https://studip.uni-goettingen.de",
                auth_type="general", auth_data={}),
    LoginPreset(name="University of Passau", base_url="https://studip.uni-passau.de/studip/",
                auth_type="shibboleth", auth_data={
                    "sso_url": "https://studip.uni-passau.de/studip/index.php?again=yes&sso=shib"
                })
]
AUTHENTICATION_TYPES = {"general": GeneralLogin,
                        "shibboleth": ShibbolethLogin}
AUTHENTICATION_TYPE_DEFAULT = "general"
AUTHENTICATION_TYPE_DATA_DEFAULT = {}

