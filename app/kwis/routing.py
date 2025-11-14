from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/ranking/$", consumers.RankingConsumer.as_asgi()),  # type: ignore[arg-type]
]
