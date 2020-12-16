from braces import views
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic


class ReviewHomePageView(views.LoginRequiredMixin,
                         generic.TemplateView):
    template_name = 'review/review.html'

    def get(self, request, *args, **kwargs):
        if not self.request.user.current_session:
            return HttpResponseRedirect(reverse_lazy('core:home'))
        return super(ReviewHomePageView, self).get(self, request, *args, **kwargs)
