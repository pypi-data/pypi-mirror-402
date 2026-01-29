from wtforms.validators import DataRequired

from indico.core import signals
from indico.core.plugins import IndicoPlugin, IndicoPluginBlueprint, url_for_plugin
from indico.modules.events.management.views import WPEventManagement
from indico.web.menu import SideMenuItem
from indico.modules.events.layout.util import MenuEntryData

from .controllers import RHWpUpdate, RHWpStatic, RHWpSync
from .forms import SettingsForm
from .wordpress import delete_event

import os, requests, re, warnings
from flask import request

class IndicoUnipiEvents(IndicoPlugin):
    """UnipiEvents

    This plugin synchronizes the changes in Indico events to an
    external Wordpress instance with the UnipiEvents plugin, creating
    posts with a custom post type 'unipievent'. """

    configurable = True
    settings_form = SettingsForm

    # event_settings_form = EventSettingsForm

    default_settings = {
        'enabled': False,
        'wp_url': '',
        'wp_username': '',
        'wp_application_password': '',
        'wp_category_maps': '',
        'wp_timezone': 'Europe/Rome'
    }

    def init(self):
        super().init()
        
        # Connect to the event modification signals
        self.connect(signals.event.created, self._on_event_created)
        self.connect(signals.event.deleted, self._on_event_deleted)
        self.connect(signals.event.updated, self._on_event_updated)

        # self.template_hook('html-head', self.inject_js)
        self.connect(signals.menu.items, self._extend_menu, sender = 'event-management-sidemenu')

    def _extend_menu(self, sender, **kwargs):
        if self.settings.get('enabled'):
            return SideMenuItem('unipievents', 'Pubblica evento',
                                url_for_plugin('unipievents.sync', event_id = request.view_args['event_id']),
                                icon = 'transmission')

    def inject_js(self, **kwargs):
        pass
        #if self.settings.get('enabled') and re.match('^/event/\d+/manage/$', request.path):
        #    return "<script src='./wp/js/main.js'></script>"

    def _on_event_created(self, event, **kwargs):
        if self.settings.get('enabled'):
            pass
        
    def _on_event_deleted(self, event, **kwargs):
        if self.settings.get('enabled'):
            try:
                delete_event(event.id)
            except:
                warnings.warn("Failure to propagate the deletion of event with ID = %d to Wordpress" % event.id)

    def _on_event_updated(self, event, **kwargs):
        if self.settings.get('enabled'):
            pass
        
    def get_blueprints(self):
        return blueprint        
    

blueprint = IndicoPluginBlueprint('unipievents', __name__, url_prefix='/event/<int:event_id>/manage/unipievents')

blueprint.add_url_rule('/update', 'update', view_func = RHWpUpdate)
blueprint.add_url_rule('/sync', 'sync', view_func = RHWpSync)
blueprint.add_url_rule('/js/main.js', 'js', view_func = RHWpStatic)
