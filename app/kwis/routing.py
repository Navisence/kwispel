from django.urls import re_path
from .consumers import RefreshConsumer

websocket_urlpatterns = [
    re_path(r"ws/refresh/$", RefreshConsumer.as_asgi()),  # type: ignore[arg-type]
]
