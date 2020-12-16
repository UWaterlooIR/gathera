from django.urls import path

from web.core import views
from web.core import practice_views

app_name = "core"

urlpatterns = [
    path('', views.Home.as_view(),
         name='home'),
    path('sessions/', views.SessionListView.as_view(),
         name='sessions'),

    # Practice views
    path('practice/', practice_views.PracticeView.as_view(),
         name='practice'),
    path('practice_complete/', practice_views.PracticeCompleteView.as_view(),
         name='practice_complete'),

    # Ajax views
    path('get_single_doc/', views.GetDocAJAXView.as_view(),
         name='get_single_doc'),

    path('get_session_details/', views.SessionDetailsAJAXView.as_view(),
         name='get_session_details'),
    path('share_session_view/', views.SessionShareView.as_view(),
         name='share_session'),
]
