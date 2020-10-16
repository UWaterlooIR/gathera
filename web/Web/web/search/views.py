import copy
import math

from config.settings.base import SEARCH_ENGINE
from config.settings.base import DEFAULT_NUM_DISPLAY

import json
import logging
from django.shortcuts import render
from braces import views

from django.http import HttpResponse

from django.utils.module_loading import import_string
from django.views import generic

from web.core.mixin import RetrievalMethodPermissionMixin
from web.interfaces.DocumentSnippetEngine import functions as DocEngine
from web.interfaces.SearchEngine.base import SearchInterface
from web.search.models import Query
from web.search.models import SearchResult
from web.search.models import SERPClick
from web.search import helpers

SearchEngine: SearchInterface = import_string(SEARCH_ENGINE)
logger = logging.getLogger(__name__)


class SimpleSearchView(views.LoginRequiredMixin,
                       RetrievalMethodPermissionMixin,
                       generic.TemplateView):
    template_name = 'search/search.html'

    def log_query(self, query, SERP, page_number, num_display):
        query_instance, q_was_created = Query.objects.get_or_create(
            username=self.request.user,
            query=query,
            session=self.request.user.current_session,
        )


        sr, sr_was_created = SearchResult.objects.get_or_create(
            username=self.request.user,
            session=self.request.user.current_session,
            query=query_instance,
            page_number=page_number,
            num_display=num_display,
            defaults={
                "SERP":SERP
            },
        )

        return query_instance, sr

    def get_params(self):
        try:
            page_number = int(self.request.GET.get('page_number', 1))
        except ValueError:
            page_number = 1
        num_display = DEFAULT_NUM_DISPLAY
        page_number = max(page_number, 1)
        offset = (page_number - 1) * num_display
        return page_number, num_display, offset

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        if query != '':
            page_number, num_display, offset = self.get_params()
            SERP = SearchEngine.search(query, offset=offset, size=num_display)
            q, sr = self.log_query(query, SERP, page_number, num_display)

            query_id = q.query_id
            serp_id = sr.id

            prev_clicks = SERPClick.objects.filter(username=self.request.user).values_list('docno', flat=True).distinct()
            prev_clicks = list(prev_clicks)

            SERP["hits"] = helpers.join_judgments(SERP["hits"],
                                                  [hit["docno"] for hit in SERP["hits"]],
                                                  self.request.user,
                                                  self.request.user.current_session)

            is_last_page = len(SERP["hits"]) != num_display

            context = {
                "isQueryPage": True,
                "queryID": query_id,
                "serpID": serp_id,
                "query": query,
                "prevClickedUrlsDuringSession": prev_clicks,
                "SERP": SERP,
                "pagination": {
                    "is_first_page": page_number == 1,
                    "page_number": page_number,
                    "page_range": range(max(1, page_number - 4),
                                        ((page_number + 4) if not is_last_page else page_number) + 1),
                    "is_last_page": is_last_page
                }
            }
        else:
            context = {
                "isQueryPage": False,
                "queryID": "NA",
                "query": "",
            }

        return render(request, self.template_name, context)



class SearchButtonView(views.CsrfExemptMixin,
                       views.LoginRequiredMixin,
                       RetrievalMethodPermissionMixin,
                       views.JsonRequestResponseMixin,
                       generic.View):
    require_json = False

    def post(self, request, *args, **kwargs):
        try:
            client_time = self.request_json.get(u"client_time")
            page_title = self.request_json.get(u"page_title")
            query = self.request_json.get(u"query")
            numdisplay = self.request_json.get(u"numdisplay")
        except KeyError:
            error_dict = {u"message": u"your input must include client_time,"
                                      u" page title, query, and numdisplay values"}
            return self.render_bad_request_response(error_dict)

        context = {u"message": u"Your search request has been recorded."}
        return self.render_json_response(context)


class SearchGetDocAJAXView(views.CsrfExemptMixin,
                           views.LoginRequiredMixin,
                           RetrievalMethodPermissionMixin,
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
        return HttpResponse(
            json_context, content_type=self.get_content_type(), status=502)

    def get_ajax(self, request, *args, **kwargs):
        docid = request.GET.get('docid')
        if not docid:
            return self.render_json_response([])
        try:
            document = DocEngine.get_documents([docid])
        except TimeoutError:
            error_dict = {u"message": u"Timeout error. Please check status of servers."}
            return self.render_timeout_request_response(error_dict)

        return self.render_json_response(document)
