from django.urls.conf import path
from django.urls.conf import re_path

from web.topic import views

app_name = "topic"

urlpatterns = [
    re_path(r'^(?P<pk>[\w.@+-]+)$', views.TopicView.as_view(), name='detail'),
    path('create/', views.TopicCreateView.as_view(), name='create'),
    path('list/', views.TopicListView.as_view(), name='list'),
    path('activate/', views.TopicActivateView.as_view(), name='activate'),
    path('delete/', views.TopicDeleteView.as_view(), name='delete'),
]
