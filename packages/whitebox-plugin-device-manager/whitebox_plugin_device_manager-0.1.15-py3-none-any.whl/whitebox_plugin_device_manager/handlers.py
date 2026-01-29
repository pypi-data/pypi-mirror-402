from channels.layers import get_channel_layer

from whitebox.events import EventHandler


channel_layer = get_channel_layer()


class DeviceConnectionStatusUpdateHandler(EventHandler):
    """
    Handler for handling the `device.connection_status.update` event.
    """

    @staticmethod
    async def emit_device_connection_status_update(data, ctx):
        data = ctx["data"]

        await channel_layer.group_send(
            "management", {"type": "device.connection_status.update", "data": data}
        )

    default_callbacks = [
        emit_device_connection_status_update,
    ]

    async def handle(self, data):
        return {"data": data}
