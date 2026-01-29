from flask import jsonify, request, Response, render_template
import os, warnings

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.events import Event
from indico.core.plugins import WPJinjaMixinPlugin

from flask_pluginengine import current_plugin

from .wordpress import update_event
from .views import WPSync

with open(os.path.join(
        os.path.dirname(__file__),
        'static', 'main.js')) as h:
    js_data = h.read()

class RHWpUpdate(RHManageEventBase):

    def _process(self):
        event_id = request.view_args['event_id']
        event = Event.get(event_id)

        success = True
        message = "Event updated successfully"

        try:
            update_event(event)
        except Exception as e:
            success = False
            message = "Failure to update the event with ID = %d" % event_id
            warnings.warn(message)
            warnings.warn(e)
                            
        return jsonify({
            "success": success,
            "message": message
        })

class RHWpSync(RHManageEventBase):

    def _process(self):
        event = Event.get(request.view_args['event_id'])
        return WPSync.render_template('sync.html', event, wp_url = current_plugin.settings.get('wp_url'))

class RHWpStatic(RHManageEventBase):
    
    def _process(self):
        return Response(js_data, mimetype = 'text/javascript')
