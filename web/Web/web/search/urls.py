from django.urls import path

from web.search import views

app_name = "search"

urlpatterns = [
    path('', views.SimpleSearchView.as_view(),
         name='main'),


    # Ajax views
    path('post_search_request/', views.SearchButtonView.as_view(),
         name='post_search_request'),

]
