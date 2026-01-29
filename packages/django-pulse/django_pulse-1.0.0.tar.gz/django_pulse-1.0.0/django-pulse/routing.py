from django.urls import re_path
from .consumers import SyncConsumer

websocket_urlpatterns = [
    re_path(r'ws/pulse/sync/$', SyncConsumer.as_asgi()),
]