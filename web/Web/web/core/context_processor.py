import datetime
import logging

from web.core.forms import SessionForm
from web.core.forms import SessionPredefinedTopicForm
from web.core.forms import ShareSessionForm
from web.core.models import SharedSession
from web.judgment.models import Judgment

logger = logging.getLogger(__name__)


def shared_session_processor(request):
    if not request.user.is_authenticated:
        return {}
    context = {"current_session_owner": False}
    current_session_obj = request.user.current_session
    if current_session_obj:
        if current_session_obj.username != request.user:
            try:
                shared_session_obj = SharedSession.objects.get(
                    refers_to=current_session_obj,
                    shared_with=request.user
                )
                context["activated_shared_session"] = shared_session_obj
                return context
            except SharedSession.DoesNotExist:
                logger.error("Could not find a shared session obj of activated session")
                return context

        context["current_session_owner"] = True
        context["share_session_form"] = ShareSessionForm(user=request.user)

    return context


def create_form_processor(request):
    if not request.user.is_authenticated:
        return {}
    # FORMS
    context = {'form_custom': SessionForm(),
               'form_predefined': SessionPredefinedTopicForm()}
    return context


def get_current_year_to_context(request):
    current_datetime = datetime.datetime.now()
    return {'current_year': current_datetime.year}
