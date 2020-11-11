import json
import logging

from braces import views
from django.views.generic.base import View

logger = logging.getLogger("web")


class LoggerView(views.CsrfExemptMixin,
                 views.JsonRequestResponseMixin,
                 View):
    require_json = False

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)["lg"][0]
        message = json.loads(body["m"])
        client_timestamp = body["t"]
        # This is the base log message.
        # Client message will contain different type of logs
        log = {
            "timestamp": client_timestamp,
            "user": self.request.user.username,
            # Add more below

            # client log message
            "client_message": message
        }

        # Log
        logger.info("{}".format(json.dumps(log)))

        return self.render_json_response({u"message": u"Your log has been received!"})
