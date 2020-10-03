from config.utils import never_ever_cache
import json
import logging
from collections import OrderedDict

from braces import views
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.urls import reverse_lazy
from django.views import generic
import requests

from web.core.mixin import RetrievalMethodPermissionMixin
from web.interfaces.DocumentSnippetEngine import functions as DocEngine
from config.settings.base import SEARCH_ENGINE
from django.utils.module_loading import import_string
from web.search import helpers
from web.search.models import Query
from web.search.models import SearchResult
from web.search.models import SERPClick

from web.interfaces.SearchEngine.base import SearchInterface

SearchEngine : SearchInterface = import_string(SEARCH_ENGINE)
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


class SearchListView(views.LoginRequiredMixin, generic.TemplateView):
    template_name = 'search/search.html'

    def get_context_data(self, **kwargs):
        query_id = kwargs.get('query_id', None)
        SERPInstance = get_object_or_404(SearchResult, query__query_id=query_id)
        prev_clicks = SERPClick.objects.filter(username=self.request.user).values_list('docno', flat=True).distinct()
        prev_clicks = list(prev_clicks)

        context = {
            "isQueryPage": True,
            "queryID": query_id,
            "query": SERPInstance.query.query,
            "prevClickedUrlsDuringSession": prev_clicks,
            "SERP": SERPInstance.SERP,
        }
        print(SERPInstance.SERP)

        return context

    @never_ever_cache
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class SearchSubmitView(views.CsrfExemptMixin,
                       views.LoginRequiredMixin,
                       generic.base.View):

    def get_success_url(self, params):
        return reverse('search:query_result', kwargs=params)

    def get_failed_url(self,):
        return reverse_lazy('failed')

    def post(self, request, *args, **kwargs):
        context = {}

        try:
            search_input = request.POST.get("search_input")
        except KeyError:
            context['error'] = "Error happened. No search input."
            messages.add_message(request, messages.ERROR, context)
            return HttpResponseRedirect(self.get_failed_url())

        # Create a query instance once we receive query
        query_instance = Query.objects.create(
            username=request.user,
            query=search_input,
            session=request.user.current_session,
        )

        # Call search API to get search results
        SERP = SearchEngine.search(search_input, size=10)

        # Create search result instance with the result of the search API call.
        SearchResult.objects.create(
            username=request.user,
            session=request.user.current_session,
            query=query_instance,
            SERP=SERP,
        )

        return JsonResponse({
            "query_url": self.get_success_url({"query_id": str(query_instance.query_id)})
        })


# class SearchListView(views.CsrfExemptMixin, generic.base.View):
#     template = 'search/search_list.html'
#
#     def post(self, request, *args, **kwargs):
#         template = loader.get_template(self.template)
#         try:
#             search_input = request.POST.get("search_input")
#             numdisplay = request.POST.get("numdisplay", 10)
#         except KeyError:
#             rendered_template = template.render({})
#             return HttpResponse(rendered_template, content_type='text/html')
#         context = {}
#         documents_values, document_ids = None, None
#         try:
#             documents_values, document_ids, total_time = SearchEngine.get_documents(
#                                                             search_input,
#                                                             numdisplay=numdisplay
#                                                          )
#         except (TimeoutError, httplib2.HttpLib2Error):
#             context['error'] = "Error happened. Please check search server."
#
#         if document_ids:
#             # document_ids = helpers.padder(document_ids)
#             documents_values = helpers.join_judgments(documents_values, document_ids,
#                                                       self.request.user,
#                                                       self.request.user.current_session)
#
#         context["documents"] = documents_values
#         context["query"] = search_input
#         if total_time:
#             context["total_time"] = "{0:.2f}".format(round(float(total_time), 2))
#
#         rendered_template = template.render(context)
#         return HttpResponse(rendered_template, content_type='text/html')



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
