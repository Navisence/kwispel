from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

cache_timeout = 20  # seconds

urlpatterns = [
    path('', views.index, name='index'),
    path('team_overview.png', cache_page(cache_timeout)(views.team_overview)),
    path('rnd_overview.png', cache_page(cache_timeout)(views.rnd_overview)),
    path('ranking/', views.ranking, name='ranking'),
    path('ranking/overview.png', cache_page(cache_timeout)(views.ranking_overview)),
    path('round/<int:rnd_id>', views.rnd_detail, name='rnd_detail'),
    path('round/<int:rnd_id>/result.png', cache_page(cache_timeout)(views.rnd_result)),
    path('team/<int:team_id>', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/result.png', cache_page(cache_timeout)(views.team_result)),
    path('vote/<int:rnd_id>/<int:team_id>', views.vote, name='vote'),
]
