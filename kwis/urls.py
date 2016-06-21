from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ranking/$', views.ranking, name='ranking'),
    url(r'^round/(?P<rnd_id>[0-9]+)/$', views.rnd_detail, name='rnd_detail'),
    url(r'^team/(?P<team_id>[0-9]+)/$', views.team_detail, name='team_detail'),
    url(r'^team/(?P<team_id>[0-9]+)/result.png$', views.team_result),
    url(r'^vote/(?P<rnd_id>[0-9]+)/(?P<team_id>[0-9]+)/$', views.vote, name='vote'),
]
