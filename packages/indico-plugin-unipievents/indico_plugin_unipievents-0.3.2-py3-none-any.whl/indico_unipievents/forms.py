from wtforms import StringField, BooleanField
from wtforms.widgets import PasswordInput
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget

from indico_wp import _

category_description = r"""
This field contains a sequence of mappings of the form N:M, where N is the ID
of an Indico category, and M is the ID of a Wordpress category (taxonomy); when 
an event is exported, any category M found in the list that correspond to the 
immediate parent category N will be added to the event. 
"""

class SettingsForm(IndicoForm):
    enabled = BooleanField(_("Enabled"), widget=SwitchWidget())
    wp_url = StringField(_("Wordpress URL"))
    wp_username = StringField(_("Username"))
    wp_application_password = StringField(_("Application Password"))
    wp_category_maps = StringField(_("Category maps"), 
        description = category_description
    )
    wp_timezone = StringField(_("Wordpress timezone"), description = _("Example: Europe/Rome"))

class EventSettingsForm(IndicoForm):
    enabled = BooleanField(_("Enabled"), widget=SwitchWidget())
