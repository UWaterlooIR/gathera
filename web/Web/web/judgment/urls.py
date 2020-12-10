from django.urls import path
from django.urls import re_path

from web.judgment import views

app_name = "judgment"

urlpatterns = [

    path('view/', views.JudgmentsView.as_view(),
         name='view'),

    # Ajax views
    path('post_judgment/', views.JudgmentAJAXView.as_view(),
         name='post_judgment'),
    path('post_nojudgment/', views.NoJudgmentAJAXView.as_view(),
         name='post_nojudgment'),
    re_path(r'^get_latest/(?P<number_of_docs_to_show>\d+)/$',
            views.GetLatestAJAXView.as_view(),
            name='get_latest'),
    path('get_all/', views.GetAllAJAXView.as_view(),
         name='get_all'),
]
