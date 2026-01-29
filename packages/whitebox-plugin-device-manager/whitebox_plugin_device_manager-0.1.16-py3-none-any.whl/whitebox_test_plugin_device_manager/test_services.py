from unittest.mock import patch, MagicMock
from django.test import TestCase

from whitebox_plugin_device_manager.services import DeviceConnectionService
from whitebox.events import event_emitter


class TestDeviceConnectionService(TestCase):
    @patch.object(event_emitter, "emit_sync")
    @patch("whitebox_plugin_device_manager.services.DeviceConnectionStatusSerializer")
    def test_emit_connection_status_update(self, mock_serializer, mock_emit_sync):
        # GIVEN
        mock_device_connection = MagicMock()
        mock_device_connection.id = 1
        mock_device_connection.name = "Test Camera"
        mock_device_connection.connection_status = "connected"
        mock_device_connection.last_connection_attempt = None
        mock_device_connection.last_successful_connection = None
        mock_device_connection.connection_error_message = ""

        serialized_data = {
            "id": 1,
            "name": "Test Camera",
            "connection_status": "connected",
            "last_connection_attempt": None,
            "last_successful_connection": None,
            "connection_error_message": "",
        }
        mock_serializer.return_value.data = serialized_data

        # WHEN
        DeviceConnectionService.emit_device_connection_status_update(
            mock_device_connection
        )

        # THEN
        mock_serializer.assert_called_once_with(instance=mock_device_connection)
        mock_emit_sync.assert_called_once_with(
            "device.connection_status.update",
            serialized_data,
        )
