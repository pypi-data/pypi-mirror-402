from unittest.mock import patch, AsyncMock
from django.test import TestCase

from whitebox_plugin_device_manager.handlers import (
    DeviceConnectionStatusUpdateHandler,
)


class TestDeviceConnectionStatusUpdateHandler(TestCase):
    async def test_handle(self):
        # GIVEN
        handler = DeviceConnectionStatusUpdateHandler()
        data = {
            "id": 1,
            "name": "Test Camera",
            "connection_status": "connected",
            "last_connection_attempt": "2024-01-01T00:00:00Z",
            "last_successful_connection": "2024-01-01T00:00:00Z",
            "connection_error_message": "",
        }

        # WHEN
        result = await handler.handle(data)

        # THEN
        expected = {
            "data": {
                "id": 1,
                "name": "Test Camera",
                "connection_status": "connected",
                "last_connection_attempt": "2024-01-01T00:00:00Z",
                "last_successful_connection": "2024-01-01T00:00:00Z",
                "connection_error_message": "",
            }
        }
        self.assertEqual(result, expected)

    @patch("whitebox_plugin_device_manager.handlers.channel_layer")
    async def test_emit_device_connection_status_update(self, mock_channel_layer):
        # GIVEN
        mock_channel_layer.group_send = AsyncMock()
        data = {}
        ctx = {
            "data": {
                "id": 1,
                "name": "Test Camera",
                "connection_status": "connected",
                "last_connection_attempt": "2024-01-01T00:00:00Z",
                "last_successful_connection": "2024-01-01T00:00:00Z",
                "connection_error_message": "",
            }
        }

        # WHEN
        await DeviceConnectionStatusUpdateHandler.emit_device_connection_status_update(
            data, ctx
        )

        # THEN
        mock_channel_layer.group_send.assert_awaited_once_with(
            "management",
            {
                "type": "device.connection_status.update",
                "data": {
                    "id": 1,
                    "name": "Test Camera",
                    "connection_status": "connected",
                    "last_connection_attempt": "2024-01-01T00:00:00Z",
                    "last_successful_connection": "2024-01-01T00:00:00Z",
                    "connection_error_message": "",
                },
            },
        )
