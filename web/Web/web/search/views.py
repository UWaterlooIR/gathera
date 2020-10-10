import math

from config.settings.base import SEARCH_ENGINE
from config.utils import never_ever_cache
import json
import logging
from django.shortcuts import render
from braces import views
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
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


class SearchView(views.LoginRequiredMixin,
                 RetrievalMethodPermissionMixin,
                 generic.TemplateView):
    template_name = 'search/search.html'

    def get_context_data(self, **kwargs):
        context = {
            "isQueryPage": False,
            "queryID": "NA",
            "query": "",
        }
        return context

    def get(self, request, *args, **kwargs):
        return super(SearchView, self).get(self, request, *args, **kwargs)


class SimpleSearchView(views.LoginRequiredMixin,
                 RetrievalMethodPermissionMixin,
                 generic.TemplateView):
    template_name = 'search/search.html'

    @staticmethod
    def log_query(request, query, SERP):
        q = query_instance = Query.objects.create(
            username=request.user,
            query=query,
            session=request.user.current_session,
        )

        sr = SearchResult.objects.create(
            username=request.user,
            session=request.user.current_session,
            query=query_instance,
            SERP=SERP,
        )

        return q


    def get_params(self, SERP):
        try:
            page_number = int(self.request.GET.get('page_number', 1))
        except ValueError:
            page_number = 1
        num_display = 10
        last_page = math.ceil(len(SERP["hits"]) / num_display)
        page_number = page_number if 1 <= page_number <= last_page else 1
        offset = (page_number - 1) * num_display
        return page_number, num_display, offset, last_page

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        if query != '':
            SERP = SearchEngine.search(query)
            q = self.log_query(request, query, SERP)

            query_id = q.query_id

            prev_clicks = SERPClick.objects.filter(username=self.request.user).values_list('docno', flat=True).distinct()
            prev_clicks = list(prev_clicks)

            page_number, num_display, offset, last_page = self.get_params(SERP)

            hits = SERP["hits"][offset: offset + num_display]

            SERP["hits"] = helpers.join_judgments(hits,
                                                  [hit["docno"] for hit in SERP["hits"]],
                                                  self.request.user,
                                                  self.request.user.current_session)

            context = {
                "isQueryPage": True,
                "queryID": query_id,
                "query": query,
                "prevClickedUrlsDuringSession": prev_clicks,
                "SERP": SERP,
                "pagination": {
                    "is_first_page": page_number == 1,
                    "is_last_page": page_number == last_page,
                    "page_number": page_number,
                    "page_range": range(max(1, page_number - 3), min(last_page, page_number + 3) + 1),
                    "last_page": last_page
                }
            }
        else:
            context = {
                "isQueryPage": False,
                "queryID": "NA",
                "query": "",
            }

        return render(request, self.template_name, context)





# class SearchListView(views.LoginRequiredMixin, generic.TemplateView):
#     template_name = 'search/search.html'
#
#     def get_context_data(self, **kwargs):
#         query_id = kwargs.get('query_id', None)
#         SERPInstance = get_object_or_404(SearchResult, query__query_id=query_id)
#         prev_clicks = SERPClick.objects.filter(username=self.request.user).values_list('docno', flat=True).distinct()
#         prev_clicks = list(prev_clicks)
#
#         SERP = SERPInstance.SERP
#
#         try:
#             page_number = int(self.request.GET.get('page_number', 1))
#         except ValueError:
#             page_number = 1
#         num_display = 10
#         last_page = math.ceil(len(SERP["hits"]) / num_display)
#         page_number = page_number if 1 <= page_number <= last_page else 1
#
#         offset = (page_number - 1) * num_display
#         hits = SERP["hits"][offset: offset + num_display]
#
#         SERP["hits"] = helpers.join_judgments(hits,
#                                               [hit["docno"] for hit in SERP["hits"]],
#                                               self.request.user,
#                                               self.request.user.current_session)
#
#         context = {
#             "isQueryPage": True,
#             "queryID": query_id,
#             "query": SERPInstance.query.query,
#             "prevClickedUrlsDuringSession": prev_clicks,
#             "SERP": SERP,
#             "pagination": {
#                 "is_first_page": page_number == 1,
#                 "is_last_page": page_number == last_page,
#                 "page_number": page_number,
#                 "page_range": range(max(1, page_number - 3), min(last_page, page_number + 3) + 1),
#                 "last_page": last_page
#             }
#
#         }
#
#         return context
#
#     @never_ever_cache
#     def get(self, request, *args, **kwargs):
#         return super().get(self, request, *args, **kwargs)
#
#
# class SearchSubmitView(views.CsrfExemptMixin,
#                        views.LoginRequiredMixin,
#                        generic.base.View):
#
#     def get_success_url(self, params):
#         return reverse('search:query_result', kwargs=params)
#
#     def get_failed_url(self,):
#         return reverse_lazy('failed')
#
#     def post(self, request, *args, **kwargs):
#         context = {}
#
#         try:
#             search_input = request.POST.get("search_input")
#         except KeyError:
#             context['error'] = "Error happened. No search input."
#             messages.add_message(request, messages.ERROR, context)
#             return HttpResponseRedirect(self.get_failed_url())
#
#         # Create a query instance once we receive query
#         query_instance = Query.objects.create(
#             username=request.user,
#             query=search_input,
#             session=request.user.current_session,
#         )
#
#         # Call search API to get search results
#         SERP = SearchEngine.search(search_input)
#
#         # Create search result instance with the result of the search API call.
#         SearchResult.objects.create(
#             username=request.user,
#             session=request.user.current_session,
#             query=query_instance,
#             SERP=SERP,
#         )
#
#         return HttpResponseRedirect(self.get_success_url({
#                 "query_id": str(query_instance.query_id)
#             })
#         )


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
