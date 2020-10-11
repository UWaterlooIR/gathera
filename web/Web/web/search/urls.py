from django.urls import path

from web.search import views

app_name = "search"

urlpatterns = [
    path('', views.SimpleSearchView.as_view(),
         name='main'),
    path('get_single_doc/',
         views.SearchGetDocAJAXView.as_view(),
         name='get_doc'),


    # Ajax views
    path('post_search_request/', views.SearchButtonView.as_view(),
         name='post_search_request'),

]
