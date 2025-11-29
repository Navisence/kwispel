from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# Helper function to trigger refresh via websocket
def trigger_refresh():
    """
    Trigger a refresh event to all connected clients
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(  # type: ignore
        "refresh_group",
        {"type": "refresh_page"}
    )
