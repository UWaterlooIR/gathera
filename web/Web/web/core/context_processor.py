import datetime
import logging

from web.core.forms import SessionForm, PreTaskQuestionnaireForm, PostTaskQuestionnaireForm, \
    PostExperimentQuestionnaireForm
from web.core.forms import SessionPredefinedTopicForm
from web.core.forms import ShareSessionForm
from web.core.models import SharedSession, ExperimentForm
from web.judgment.models import Judgment

logger = logging.getLogger(__name__)


def shared_session_processor(request):
    if not request.user.is_authenticated:
        return {}
    context = {"current_session_owner": False}
    current_session_obj = request.user.current_session
    if current_session_obj:
        time_worked = current_session_obj.timespent
        judgments_for_session = Judgment.objects.filter(session=current_session_obj)
        positive_judgments = judgments_for_session.filter(relevance__in=[1, 2]).count()
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

        # allowed: after nudge,
        # not allowed: integrated cal, no nudge, less than 5 judgments
        is_cal_allowed = not current_session_obj.integrated_cal and (
            (current_session_obj.nudge_to_cal and positive_judgments >= 5)
            or not current_session_obj.nudge_to_cal)

        on_last_task = (current_session_obj.session_order and
                                  current_session_obj.session_order >= 4)
        context['is_task_in_progress'] = False
        context["experiment_completed"] = False
        if not current_session_obj.max_time and not current_session_obj.session_order:
            context["form_to_show"] = 'none'
            context['is_task_in_progress'] = True
        elif not current_session_obj.experiment_forms.filter(form_type="pre_task").exists():
            context["form_to_show"] = 'pre_task'
        elif (not current_session_obj.experiment_forms.filter(form_type="post_task").exists() and
              current_session_obj.max_time <= current_session_obj.timespent):
            context["form_to_show"] = 'post_task'
        elif on_last_task and current_session_obj.max_time > current_session_obj.timespent:
            context["form_to_show"] = 'none'
            context["experiment_completed"] = False
            context['is_task_in_progress'] = True
        elif on_last_task and not ExperimentForm.objects.filter(
                form_type="post_experiment", user=request.user).exists():
            context["form_to_show"] = 'post_experiment'
            context["experiment_completed"] = True
        elif not on_last_task:
            context["experiment_completed"] = False
            context["form_to_show"] = 'none'
            context['is_task_in_progress'] = True
        else:
            context["experiment_completed"] = True
            context["form_to_show"] = 'none'
        context["current_session_owner"] = True
        context["share_session_form"] = ShareSessionForm(user=request.user)
        context["is_cal_allowed"] = is_cal_allowed
        context["disable_search"] = current_session_obj.disable_search
        context["time_worked"] = f'{time_worked//60} minutes and {time_worked:.2f} seconds'

    return context


def create_form_processor(request):
    if not request.user.is_authenticated:
        return {}
    # FORMS
    context = {'form_custom': SessionForm(),
               'form_predefined': SessionPredefinedTopicForm(),
               'form_pre_task': PreTaskQuestionnaireForm(),
                'form_post_task': PostTaskQuestionnaireForm(),
               'form_post_experiment': PostExperimentQuestionnaireForm(),
               }
    return context


def get_current_year_to_context(request):
    current_datetime = datetime.datetime.now()
    return {'current_year': current_datetime.year}
