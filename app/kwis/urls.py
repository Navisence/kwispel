from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('team_overview.png', views.team_overview),
    path('rnd_overview.png', views.rnd_overview),
    path('ranking/', views.ranking, name='ranking'),
    path('ranking/overview.png', views.ranking_overview),
    path('round/<int:rnd_id>', views.rnd_detail, name='rnd_detail'),
    path('round/<int:rnd_id>/result.png', views.rnd_result),
    path('team/<int:team_id>', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/result.png', views.team_result),
    path('vote/<int:rnd_id>/<int:team_id>', views.vote, name='vote'),
]
