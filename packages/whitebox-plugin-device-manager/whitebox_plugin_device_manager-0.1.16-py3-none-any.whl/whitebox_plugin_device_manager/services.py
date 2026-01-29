from whitebox.events import event_emitter
from .serializers import DeviceConnectionStatusSerializer


class DeviceConnectionService:
    """
    Service class for handling device connection-related operations.
    """

    @classmethod
    def emit_device_connection_status_update(
        cls,
        device_connection,
    ) -> None:
        """
        Emit a device connection status update event to all connected clients
        and plugins who are listening for device connection status updates.

        Parameters:
            device_connection: The DeviceConnection instance to emit status for
        """

        device_connection_status_data = DeviceConnectionStatusSerializer(
            instance=device_connection
        ).data
        event_emitter.emit_sync(
            "device.connection_status.update", device_connection_status_data
        )
