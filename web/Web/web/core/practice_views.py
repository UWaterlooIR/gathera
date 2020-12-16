import logging
import random
import string

from allauth.account.adapter import get_adapter
from allauth.account.utils import perform_login
from braces import views
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic


logger = logging.getLogger(__name__)

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
