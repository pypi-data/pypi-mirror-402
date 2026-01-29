from indico.core.plugins import WPJinjaMixinPlugin
from indico.modules.events.management.views import WPEventManagement

class WPSync(WPJinjaMixinPlugin, WPEventManagement):
    sidemenu_option = 'wp'
