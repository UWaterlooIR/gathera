from django.urls import path

from web.search import views

app_name = "search"

urlpatterns = [
    path('', views.SimpleSearchView.as_view(),
         name='main'),
    path('get_docs/',
         views.SearchListView.as_view(),
         name='get_docs'),
    path('get_single_doc/',
         views.SearchGetDocAJAXView.as_view(),
         name='get_doc'),
    # path('submit_search/',
    #      views.SearchSubmitView.as_view(),
    #      name='submit_search'),
    # path('query/<uuid:query_id>/',
    #      views.SearchListView.as_view(),
    #      name='query_result'),

    # Ajax views
    path('post_search_request/', views.SearchButtonView.as_view(),
         name='post_search_request'),

]
