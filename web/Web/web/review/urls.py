from django.urls import path

from web.review import views

app_name = "review"

urlpatterns = [
    path('', views.ReviewHomePageView.as_view(),
         name='main'),

    # Ajax views
    path('post_log/', views.ReviewMessageAJAXView.as_view(),
         name='post_log_msg'),
    path('get_docs/', views.DocAJAXView.as_view(),
         name='get_docs'),
    path('get_docs_ids/', views.DocAJAXView.as_view(),
         name='get_docs_ids'),
]
