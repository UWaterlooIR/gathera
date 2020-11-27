import json
import logging

from braces import views
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import generic
from interfaces.DocumentSnippetEngine import functions as DocEngine
from web.core.mixin import RetrievalMethodPermissionMixin
from web.judgment.models import Judgment

logger = logging.getLogger(__name__)


class ReviewHomePageView(views.LoginRequiredMixin,
                      RetrievalMethodPermissionMixin,
                      generic.TemplateView):
    template_name = 'review/review.html'

    def get(self, request, *args, **kwargs):
        if not self.request.user.current_session:
            return HttpResponseRedirect(reverse_lazy('core:home'))
        return super(ReviewHomePageView, self).get(self, request, *args, **kwargs)


class DocAJAXView(views.CsrfExemptMixin,
                  RetrievalMethodPermissionMixin,
                  views.LoginRequiredMixin,
                  views.JsonRequestResponseMixin,
                  views.AjaxResponseMixin, generic.View):
    """
    View to get a list of documents (with their content)
    """
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
        session = self.request.user.current_session.uuid
        seed_query = self.request.user.current_session.topic.seed_query

        try:
            latest = Judgment.objects.filter(
                user=self.request.user,
                session=self.request.user.current_session,
            ).filter(
                relevance__isnull=False
            ).order_by('-relevance')

            documents = []

            next_patch_ids = []
            for judgment in latest:
                next_patch_ids.append(judgment.doc_id)

            doc_ids_hack = []
            for doc_id in next_patch_ids:
                doc = {'doc_id': doc_id}
                if '.' in doc_id:
                    doc['doc_id'], doc['para_id'] = doc_id.split('.')
                doc_ids_hack.append(doc)

            if 'doc' in self.request.user.current_session.strategy:
                documents = DocEngine.get_documents(next_patch_ids,
                                                    seed_query)
            else:
                documents = DocEngine.get_documents_with_snippet(doc_ids_hack,
                                                                 seed_query)

            return self.render_json_response(documents)
    
        except TimeoutError:
            error_dict = {u"message": u"Timeout error. Please check status of servers."}
            return self.render_timeout_request_response(error_dict)

