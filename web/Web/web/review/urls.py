from django.urls import path

from web.review import views

app_name = "review"

urlpatterns = [
    path('', views.ReviewHomePageView.as_view(),
         name='main'),

    # Ajax views
    path('get_docs_ids/', views.DocAJAXView.as_view(),
         name='get_docs_ids')
]
