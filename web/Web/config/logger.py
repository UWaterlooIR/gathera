import json
import logging

from braces import views
from django.views.generic.base import View

from web.core.models import LogEvent

logger = logging.getLogger('web')


class LoggerView(views.CsrfExemptMixin,
                 views.JsonRequestResponseMixin,
                 View):
    require_json = False

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        timestamp = body['timestamp']
        event = body['event']
        data = body['data']
        current_session = self.request.user.current_session
        log = {
            'user': self.request.user.username,
            'timestamp': timestamp,
            'event': event,
            'data': data
        }
        if data.get('track_backend'):
            data.pop('track_backend', None)
            LogEvent.objects.create(user=self.request.user, session=current_session, action=event, data=data)

        # Log
        logger.info('{}'.format(json.dumps(log)))

        return self.render_json_response({u'message': 'done'})
