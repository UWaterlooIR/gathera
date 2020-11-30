import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from web.core.models import SharedSession

logger = logging.getLogger(__name__)


class RetrievalMethodPermissionMixin(object):
    """
    Mixin that gives checks if user is allowed to use a retrieval component
    (e.g. CAL or Search).
    """

    def __init__(self):
        self.disallow_message = 'Sorry, you are not allowed to ' \
                                'use {} in this session.'

    def dispatch(self, request, *args, **kwargs):
        current_session_obj = request.user.current_session

        if "scal" in request.user.current_session.strategy and "search" in request.resolver_match.app_names:
            messages.add_message(request,
                                 messages.ERROR,
                                 self.disallow_message.format("search"))
            return HttpResponseRedirect(reverse_lazy('core:home'))

        if current_session_obj and current_session_obj.username != request.user:
            try:
                shared_session_obj = SharedSession.objects.get(
                    refers_to=current_session_obj,
                    shared_with=request.user
                )
                # TODO: Fix hard coded app_names of CAL and search
                if "CAL" in request.resolver_match.app_names:
                    if shared_session_obj.disallow_CAL:
                        messages.add_message(request,
                                             messages.ERROR,
                                             self.disallow_message.format("CAL"))
                        return HttpResponseRedirect(reverse_lazy('core:home'))

                if "search" in request.resolver_match.app_names:
                    if shared_session_obj.disallow_search:
                        messages.add_message(request,
                                             messages.ERROR,
                                             self.disallow_message.format("search"))
                        return HttpResponseRedirect(reverse_lazy('core:home'))

            except SharedSession.DoesNotExist:
                logger.error("Could not find a shared session obj of activated session")
                return HttpResponseRedirect(reverse_lazy('core:home'))

        return super(RetrievalMethodPermissionMixin, self).dispatch(
            request, *args, **kwargs)
