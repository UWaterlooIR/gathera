from django.urls import path

from web.CAL import views

app_name = "CAL"

urlpatterns = [
    path('', views.CALHomePageView.as_view(),
         name='main'),

    # Ajax views
    path('post_log/', views.CALMessageAJAXView.as_view(),
         name='post_log_msg'),
    path('get_docs/', views.DocAJAXView.as_view(),
         name='get_docs'),
    path('get_docs_ids/', views.DocAJAXView.as_view(),
         name='get_docs_ids'),
]
