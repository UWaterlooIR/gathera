from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView
import notifications.urls

from config.logger import LoggerView

urlpatterns = [
    path('', include('web.core.urls', namespace='core')),
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),

    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, admin.site.urls),

    # User management
    path('users/', include('web.users.urls', namespace='users')),
    path('accounts/', include('allauth.urls')),

    # Notifications
    path('inbox/notifications/', include(notifications.urls, namespace='notifications')),

    # Custom urls includes go here
    path('discovery/', include('web.CAL.urls', namespace='CAL')),
    path('search/', include('web.search.urls', namespace='search')),
    path('topic/', include('web.topic.urls', namespace='topic')),
    path('judgment/', include('web.judgment.urls', namespace='judgment')),

    # Logger
    path(r'logger/', LoggerView.as_view(), name='logger'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        url(r'^403/$', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        url(r'^404/$', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        url(r'^500/$', default_views.server_error),
    ]
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
