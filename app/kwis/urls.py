from django.urls import path
from django.contrib import admin
from django.views.decorators.cache import cache_page
from . import views

cache_timeout = 5  # seconds

admin.site.site_title = "Kwispel Admin"
admin.site.site_header = "Kwispel Administration"
admin.site.index_title = "Kwispel Admin Portal"

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
    path('delete/<int:rnd_id>/<int:team_id>', views.delete, name='delete'),
    path('reveal_next', views.reveal_next, name='reveal_next'),
    path('trigger_refresh', views.trigger_refresh_view, name='trigger_refresh'),
]
