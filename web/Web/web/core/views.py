from config.settings.base import TIME_ZONE
import json
import logging
import random
import string

from allauth.account.adapter import get_adapter
from allauth.account.utils import perform_login
from braces import views
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Case
from django.db.models import Count
from django.db.models import When
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views import generic
from interfaces.DocumentSnippetEngine import functions as DocEngine

import pytz
from web.core.forms import SessionForm
from web.core.forms import SessionPredefinedTopicForm
from web.core.forms import ShareSessionForm
from web.core.mixin import RetrievalMethodPermissionMixin
from web.core.models import Session
from web.core.models import SharedSession
from web.core.session_utils import activate_session_submit_form
from web.core.session_utils import delete_session_submit_form
from web.core.session_utils import revoke_shared_session_submit_form
from web.core.session_utils import share_session_submit_form
from web.core.session_utils import submit_new_predefined_topic_session_form
from web.core.session_utils import submit_new_session_form
from web.judgment.models import Judgment

logger = logging.getLogger(__name__)


class Home(views.LoginRequiredMixin, generic.TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)

        # COUNTERS
        counters = Judgment.objects.filter(user=self.request.user,
                                           source="CAL",
                                           session=self.request.user.current_session).aggregate(
            total_highlyRelevant=Count(Case(When(relevance=2, then=1))),
            total_relevant=Count(Case(When(relevance=1, then=1))),
            total_nonrelevant=Count(Case(When(relevance=0, then=1)))
        )

        context["total_highlyRelevant_CAL"] = counters["total_highlyRelevant"]
        context["total_nonrelevant_CAL"] = counters["total_nonrelevant"]
        context["total_relevant_CAL"] = counters["total_relevant"]

        counters = Judgment.objects.filter(user=self.request.user,
                                           source__contains="search",
                                           session=self.request.user.current_session).aggregate(
            total_highlyRelevant=Count(Case(When(relevance=2, then=1))),
            total_relevant=Count(Case(When(relevance=1, then=1))),
            total_nonrelevant=Count(Case(When(relevance=0, then=1)))
        )

        context["total_highlyRelevant_search"] = counters["total_highlyRelevant"]
        context["total_nonrelevant_search"] = counters["total_nonrelevant"]
        context["total_relevant_search"] = counters["total_relevant"]

        collaborators = []
        shared_with_objs = SharedSession.objects.filter(
            refers_to=self.request.user.current_session
        )
        if self.request.user.current_session:
            collaborators.append(self.request.user.current_session.username)
        for shared_obj in shared_with_objs:
            collaborators.append(shared_obj.shared_with)
        context["collaborators"] = collaborators

        return context

    def get(self, request, *args, **kwargs):
        return super(Home, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        if "submit-session-predefine-topic-form" in request.POST:
            submit_new_predefined_topic_session_form(request)
        elif "submit-session-form" in request.POST:
            submit_new_session_form(request)
        elif request.POST.get("share_sessionid"):
            share_session_submit_form(request)
        elif request.POST.get("revoke_sessionid"):
            revoke_shared_session_submit_form(request)
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                 'Ops. Something went wrong.')
        return HttpResponseRedirect(reverse_lazy('core:home'))


class SessionListView(views.LoginRequiredMixin, generic.TemplateView):
    template_name = 'core/sessions.html'

    def get_context_data(self, **kwargs):
        context = super(SessionListView, self).get_context_data(**kwargs)
        context["share_session_form"] = ShareSessionForm(user=self.request.user)

        user_sessions_queryset = Session.objects.filter(username=self.request.user).order_by("created_at")
        sessions = []
        for session_obj in user_sessions_queryset:
            session_info = {"session_obj": session_obj,
                            "created_at": timezone.localtime(session_obj.created_at,
                                                             pytz.timezone(TIME_ZONE))
                            }
            sessions.append(session_info)
        context["sessions"] = sessions

        shared_sessions = []
        shared_sessions_queryset = SharedSession.objects.filter(shared_with=self.request.user).order_by('created_at')
        for shared_session_obj in shared_sessions_queryset:

            shared_sessions.append({
                "shared_session_obj": shared_session_obj,
                "created_at": timezone.localtime(shared_session_obj.created_at,
                                                 pytz.timezone(TIME_ZONE))
            })
        context["shared_sessions"] = shared_sessions
        return context

    def get(self, request, *args, **kwargs):
        return super(SessionListView, self).get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get("activate_sessionid"):
            if activate_session_submit_form(request):
                HttpResponseRedirect(reverse_lazy('core:home'))
        elif request.POST.get("delete_sessionid"):
            delete_session_submit_form(request)
        elif request.POST.get("share_sessionid"):
            share_session_submit_form(request)
        elif request.POST.get("revoke_sessionid"):
            revoke_shared_session_submit_form(request)

        return HttpResponseRedirect(reverse_lazy('core:sessions'))


class SessionDetailsAJAXView(views.CsrfExemptMixin, views.LoginRequiredMixin,
                             views.JsonRequestResponseMixin,
                             views.AjaxResponseMixin, generic.View):

    require_json = False

    def render_timeout_request_response(self, error_dict=None):
        if error_dict is None:
            error_dict = self.error_response_dict
        json_context = json.dumps(
            error_dict,
            cls=self.json_encoder_class,
            **self.get_json_dumps_kwargs()
        ).encode('utf-8')
        return HttpResponse(json_context, content_type=self.get_content_type(), status=502)

    def get_ajax(self, request, *args, **kwargs):
        session_id = request.GET.get('uuid')
        is_shared_session = request.GET.get('is_shared_session', False)
        is_shared_session = is_shared_session == "true"

        if not session_id:
            return JsonResponse({"message": "Ops! Session not found."}, status=404)
        session = {
            "uuid": session_id,
        }

        if is_shared_session:
            try:
                shared_session_obj = SharedSession.objects.get(uuid=session_id, shared_with=self.request.user)
                session_obj = shared_session_obj.refers_to
                session['uuid'] = session_obj.uuid
                shared_with_queryset_values = []
                session["owner"] = False
            except SharedSession.DoesNotExist:
                return JsonResponse({"message": "Ops! Session not found."}, status=404)
        else:
            try:
                session_obj = Session.objects.get(username=self.request.user, uuid=session_id)
                shared_with_queryset = SharedSession.objects.filter(
                    refers_to__uuid=session_id,
                    creator=self.request.user
                )
                shared_with_queryset_values = []
                for shared_session_obj in shared_with_queryset:
                    shared_with_queryset_values.append({
                        "uuid": shared_session_obj.uuid,
                        "shared_by": shared_session_obj.creator.username,
                        "shared_with": shared_session_obj.shared_with.username,
                        "shared_on": timezone.localtime(shared_session_obj.created_at,
                                                             pytz.timezone(TIME_ZONE)),
                        "disallow_search": shared_session_obj.disallow_search,
                        "disallow_CAL": shared_session_obj.disallow_CAL,
                    })
                session["owner"] = True
            except Session.DoesNotExist:
                return JsonResponse({"message": "Ops! Session not found."}, status=404)

        session['is_active_session'] = self.request.user.current_session == session_obj
        session['shared_with'] = shared_with_queryset_values
        session['topic_title'] = session_obj.topic.title
        session['topic_number'] = session_obj.topic.number
        session['topic_description'] = session_obj.topic.description
        session['topic_seed_query'] = session_obj.topic.seed_query
        session['topic_narrative'] = session_obj.topic.narrative

        session['strategy'] = session_obj.get_strategy_display()
        session['effort'] = session_obj.max_number_of_judgments
        session['show_full_document_content'] = session_obj.show_full_document_content
        session['created_at'] = session_obj.created_at

        counters = Judgment.objects.filter(user=self.request.user,
                                           session=session_obj).aggregate(
            total_highlyRelevant=Count(Case(When(relevance=2, then=1))),
            total_relevant=Count(Case(When(relevance=1, then=1))),
            total_nonrelevant=Count(Case(When(relevance=0, then=1)))
        )

        session["total_highlyRelevant"] = counters["total_highlyRelevant"]
        session["total_nonrelevant"] = counters["total_nonrelevant"]
        session["total_relevant"] = counters["total_relevant"]
        session["total_judged"] = counters["total_highlyRelevant"] + counters["total_nonrelevant"] + counters["total_relevant"]

        return self.render_json_response(session)


class SessionShareView(View):
    def post(self, request):
        if request.POST.get("share_sessionid"):
            share_session_submit_form(request)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class GetDocAJAXView(views.CsrfExemptMixin,
                     views.LoginRequiredMixin,
                     RetrievalMethodPermissionMixin,
                     views.JsonRequestResponseMixin,
                     views.AjaxResponseMixin, generic.View):

    require_json = False

    def get_ajax(self, request, *args, **kwargs):
        try:
            doc_id = request.GET.get('docid')
            doc_id = str(doc_id)
        except KeyError:
            return JsonResponse({"message": "Docid was not passed."}, status=400)

        l = []
        doc = {'doc_id': doc_id}
        if '.' in doc_id:
            doc['doc_id'], doc['para_id'] = doc_id.split('.')
        l.append(doc)
        seed_query = self.request.user.current_session.topic.seed_query
        if 'doc' in self.request.user.current_session.strategy:
            result = DocEngine.get_documents([doc_id], seed_query)
        else:
            result = DocEngine.get_documents_with_snippet(l, seed_query)

        exists = Judgment.objects.filter(doc_id=doc_id,
                                         user=self.request.user,
                                         session=self.request.user.current_session
                                         )
        if exists:
            result[0]["rel"] = exists.first().relevance
            result[0]["additional_judging_criteria"] = exists.first().additional_judging_criteria

        return self.render_json_response(result)

        # if not docid:
        #     return self.render_json_response([])
        # try:
        #     document = DocEngine.get_documents([docid])
        # except TimeoutError:
        #     error_dict = {u"message": u"Timeout error. Please check status of servers."}
        #     return self.render_timeout_request_response(error_dict)
        #
        # return self.render_json_response(document)


class VisitAJAXView(views.CsrfExemptMixin, views.LoginRequiredMixin,
                    views.JsonRequestResponseMixin,
                    generic.View):
    require_json = False

    def post(self, request, *args, **kwargs):
        try:
            client_time = self.request_json.get(u"client_time")
            page_title = self.request_json.get(u"page_title")
            page_file = self.request_json.get(u"page_file")
        except KeyError:
            error_dict = {u"message": u"your input must include client_time,"
                                      u"pag_file and page_title"}
            return self.render_bad_request_response(error_dict)

        context = {u"message": u"Your visit has been recorded"}
        return self.render_json_response(context)


class CtrlFAJAXView(views.CsrfExemptMixin, views.LoginRequiredMixin,
                    views.JsonRequestResponseMixin,
                    generic.View):
    require_json = False

    def post(self, request, *args, **kwargs):
        try:
            client_time = self.request_json.get(u"client_time")
            search_field_value = self.request_json.get(u"search_field_value")
            page_title = self.request_json.get(u"page_title")
            extra_context = self.request_json.get(u"extra_context")
        except KeyError:
            error_dict = {u"message": u"your input must include client_time, "
                                      u"extra_context and search_field_value"}
            return self.render_bad_request_response(error_dict)

        context = {u"message": u"Your event has been recorded"}
        return self.render_json_response(context)


class FindKeystrokeAJAXView(views.CsrfExemptMixin, views.LoginRequiredMixin,
                            views.JsonRequestResponseMixin,
                            generic.View):
    require_json = False

    def post(self, request, *args, **kwargs):
        try:
            client_time = self.request_json.get(u"client_time")
            doc_id = self.request_json.get(u"doc_id")
            page_title = self.request_json.get(u"page_title")
            character = self.request_json.get(u"character")
            isSearchbarFocused = self.request_json.get(u"isSearchbarFocused")
            search_bar_value = self.request_json.get(u"search_bar_value")
        except KeyError:
            error_dict = {u"message": u"your input must include client_time,"
                                      u" doc_id, character, isSearchbarFocused,"
                                      u" page_title and search bar value."}
            return self.render_bad_request_response(error_dict)

        context = {u"message": u"Your visit has been recorded."}
        return self.render_json_response(context)


class MessageAJAXView(views.CsrfExemptMixin, views.LoginRequiredMixin,
                      views.JsonRequestResponseMixin,
                      generic.View):
    """
    Generic view to capture specific log messages from browser
    """
    require_json = False

    def post(self, request, *args, **kwargs):
        try:
            client_time = self.request_json.get(u"client_time")
            message = self.request_json.get(u"message")
            action = self.request_json.get(u"action")
            page_title = self.request_json.get(u"page_title")
            extra_context = self.request_json.get(u'extra_context')
        except KeyError:
            error_dict = {u"message": u"your input must include client_time, "
                                      u"message, ... etc"}
            return self.render_bad_request_response(error_dict)

        context = {u"message": u"Your log message with action '{}' "
                               u"has been logged.".format(action)}

        return self.render_json_response(context)


class PracticeCompleteView(views.LoginRequiredMixin, generic.TemplateView):
    def get(self, request, *args, **kwargs):
        adapter = get_adapter(self.request)
        adapter.logout(self.request)
        return HttpResponseRedirect(reverse_lazy('account_login'))


class PracticeView(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        practice_group, created = Group.objects.get_or_create(name='practice')

        # Create practice user and save to the database
        lst = [random.choice(string.ascii_letters + string.digits) for n in range(5)]
        randomstr = "".join(lst)
        username = password = "{}_practice".format(randomstr)
        User = get_user_model()
        practice_user = User.objects.create_user(username,
                                                 '{}@crazymail.com'.format(username),
                                                 password)

        practice_group.user_set.add(practice_user)
        practice_group.save()

        credentials = {
            "username": username,
            "password": password
        }

        user = get_adapter(self.request).authenticate(
            self.request,
            **credentials)
        ret = perform_login(request, user,
                            email_verification=False,
                            redirect_url=reverse_lazy('core:home'))
        return ret
