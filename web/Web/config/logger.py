import json
import logging

from braces import views
from django.views.generic.base import View

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
        message = body['message']

        log = {
            'user': self.request.user.username,
            'timestamp': timestamp,
            'event': event,
            'data': data,
            'message': message
        }

        # Log
        logger.info('{}'.format(json.dumps(log)))

        return self.render_json_response({u'message': message})
