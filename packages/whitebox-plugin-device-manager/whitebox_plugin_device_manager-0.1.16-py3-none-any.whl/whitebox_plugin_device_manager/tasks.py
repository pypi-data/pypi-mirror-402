from datetime import timedelta

import django_rq

from whitebox import get_plugin_logger
from .models import DeviceConnection, ConnectionStatus
from .wireless_interface_manager import wireless_interface_manager, WiFiConnectionStatus
from .services import DeviceConnectionService


logger = get_plugin_logger(__name__)


DEFAULT_MONITORING_INTERVAL_SECONDS = 2
DEVICE_CONNECTION_MONITORING_JOB_ID = "device_connection_monitoring"


def connect_to_device_wifi(device_connection_id: int) -> bool:
    """
    Connect to a device's WiFi network.

    Args:
        device_connection_id: The ID of the DeviceConnection to connect to

    Returns:
        bool: True if connection was successful, False otherwise
    """
    try:
        device_connection = DeviceConnection.objects.get(id=device_connection_id)
    except DeviceConnection.DoesNotExist:
        logger.error(f"DeviceConnection with ID {device_connection_id} not found")
        return False

    if not device_connection.is_wifi_connection:
        logger.error(
            f"DeviceConnection {device_connection_id} is not a WiFi connection"
        )
        return False

    logger.info(f"Connecting to WiFi for device: {device_connection.name}")

    # Update status to connecting
    device_connection.update_connection_status(ConnectionStatus.CONNECTING)

    # Emit status update via WebSocket
    _emit_connection_status_update(device_connection)

    # Attempt to connect
    success, message = wireless_interface_manager.connect_to_wifi(
        device_connection.id,
        device_connection.wifi_ssid,
        device_connection.wifi_password,
    )

    if success:
        device_connection.update_connection_status(ConnectionStatus.CONNECTED)
        logger.info(
            f"Successfully connected to WiFi for device: {device_connection.name}"
        )
    else:
        device_connection.update_connection_status(ConnectionStatus.FAILED, message)
        logger.error(
            f"Failed to connect to WiFi for device {device_connection.name}: {message}"
        )

    # Emit updated status via WebSocket
    _emit_connection_status_update(device_connection)

    return success


def disconnect_from_device_wifi(device_connection_id: int) -> bool:
    """
    Disconnect from a device's WiFi network.

    Args:
        device_connection_id: The ID of the DeviceConnection to disconnect from

    Returns:
        bool: True if disconnection was successful, False otherwise
    """
    try:
        device_connection = DeviceConnection.objects.get(id=device_connection_id)
    except DeviceConnection.DoesNotExist:
        logger.error(f"DeviceConnection with ID {device_connection_id} not found")
        return False

    if not device_connection.is_wifi_connection:
        logger.error(
            f"DeviceConnection {device_connection_id} is not a WiFi connection"
        )
        return False

    logger.info(f"Disconnecting from WiFi for device: {device_connection.name}")

    device_connection.update_connection_status(ConnectionStatus.DISCONNECTING)
    _emit_connection_status_update(device_connection)

    success, message = wireless_interface_manager.disconnect_from_wifi(
        device_connection.id, device_connection.wifi_ssid
    )

    if success:
        device_connection.update_connection_status(ConnectionStatus.DISCONNECTED)
        logger.info(
            f"Successfully disconnected from WiFi for device: {device_connection.name}"
        )
    else:
        device_connection.update_connection_status(ConnectionStatus.CONNECTED)
        logger.error(
            f"Failed to disconnect from WiFi for device {device_connection.name}: {message}"
        )

    # Emit updated status via WebSocket
    _emit_connection_status_update(device_connection)

    return success


def check_device_connection_status(device_connection_id: int) -> bool:
    """
    Check the current connection status for a device.

    Args:
        device_connection_id: The ID of the DeviceConnection to check

    Returns:
        bool: True if device is connected, False otherwise
    """
    try:
        device_connection = DeviceConnection.objects.get(id=device_connection_id)
    except DeviceConnection.DoesNotExist:
        logger.error(f"DeviceConnection with ID {device_connection_id} not found")
        return False

    if not device_connection.is_wifi_connection:
        return False

    current_status = wireless_interface_manager.check_wifi_connection_status(
        device_connection.id, device_connection.wifi_ssid
    )

    if current_status is None:
        return device_connection.connection_status == ConnectionStatus.CONNECTED

    # Convert WiFiConnectionStatus to ConnectionStatus
    if current_status == WiFiConnectionStatus.CONNECTED:
        db_status = ConnectionStatus.CONNECTED
    elif current_status == WiFiConnectionStatus.CONNECTING:
        db_status = ConnectionStatus.CONNECTING
    elif current_status == WiFiConnectionStatus.FAILED:
        db_status = ConnectionStatus.FAILED
    else:
        db_status = ConnectionStatus.DISCONNECTED

    # Only update if status has changed
    if device_connection.connection_status != db_status:
        device_connection.update_connection_status(db_status)
        _emit_connection_status_update(device_connection)
        logger.info(
            f"Connection status updated for {device_connection.name}: {db_status}"
        )

    return current_status == WiFiConnectionStatus.CONNECTED


def monitor_all_device_connections() -> None:
    """
    Check the connection status of all WiFi-enabled devices.
    This task should be run periodically.
    """
    logger.debug("Starting device connection monitoring sweep")

    wifi_connections = DeviceConnection.objects.filter(connection_type="wifi")

    for device_connection in wifi_connections:
        try:
            check_device_connection_status(device_connection.id)
        except Exception as e:
            logger.error(
                f"Error checking connection status for device {device_connection.name}: {str(e)}"
            )

    logger.debug(
        f"Device connection monitoring complete. Checked {wifi_connections.count()} devices"
    )


def cancel_existing_connection_monitoring_jobs() -> None:
    """
    Cancel and delete any existing device connection monitoring jobs.
    """
    try:
        queue = django_rq.get_queue("default")
        scheduler = django_rq.get_scheduler("default")

        # Try to cancel and delete existing job with the same ID
        try:
            existing_job = queue.fetch_job(DEVICE_CONNECTION_MONITORING_JOB_ID)
            if existing_job:
                existing_job.cancel()
                existing_job.delete()
                logger.info(
                    f"Cancelled and deleted existing job: {DEVICE_CONNECTION_MONITORING_JOB_ID}"
                )
        except Exception as e:
            logger.warning(f"No existing job to cancel: {e}")

        # Cancel and delete from scheduler too
        try:
            for job in scheduler.get_jobs():
                if job.id == DEVICE_CONNECTION_MONITORING_JOB_ID:
                    scheduler.cancel(job)
                    job.delete()
                    logger.info(
                        f"Cancelled and deleted existing scheduled job: {DEVICE_CONNECTION_MONITORING_JOB_ID}"
                    )
        except Exception as e:
            logger.warning(f"No existing scheduled job to cancel: {e}")

        # Also check for jobs by function name
        job_func_name = "whitebox_plugin_device_manager.tasks.monitor_all_device_connections_with_reschedule"

        # Cancel jobs in queue by function name
        for job in queue.get_jobs():
            if job.func_name == job_func_name:
                job.cancel()
                job.delete()
                logger.info(
                    f"Cancelled and deleted monitoring job by function name: {job.id}"
                )

        # Cancel scheduled jobs by function name
        for job in scheduler.get_jobs():
            if job.func_name == job_func_name:
                scheduler.cancel(job)
                job.delete()
                logger.info(
                    f"Cancelled and deleted scheduled monitoring job by function name: {job.id}"
                )

    except Exception as e:
        logger.warning(f"Error clearing existing jobs: {e}")


def start_periodic_connection_monitoring() -> None:
    """
    Start periodic monitoring of device connections.
    """
    logger.info("Clearing existing device connection monitoring jobs")
    cancel_existing_connection_monitoring_jobs()

    # Schedule the first monitoring job
    logger.info("Starting periodic device connection monitoring")
    queue = django_rq.get_queue("default")
    queue.enqueue_in(
        timedelta(seconds=DEFAULT_MONITORING_INTERVAL_SECONDS),
        monitor_all_device_connections_with_reschedule,
        job_id=DEVICE_CONNECTION_MONITORING_JOB_ID,
    )

    logger.info("Periodic monitoring scheduled")


def monitor_all_device_connections_with_reschedule() -> None:
    """
    Monitor all device connections and reschedule the next run.
    This creates a self-perpetuating monitoring loop.
    """
    logger.debug("Running periodic device connection monitoring")

    # Run the actual monitoring
    monitor_all_device_connections()

    # Schedule the next run
    queue = django_rq.get_queue("default")
    queue.enqueue_in(
        timedelta(seconds=DEFAULT_MONITORING_INTERVAL_SECONDS),
        monitor_all_device_connections_with_reschedule,
        job_id=DEVICE_CONNECTION_MONITORING_JOB_ID,
    )

    logger.debug(
        f"Next monitoring run scheduled in {DEFAULT_MONITORING_INTERVAL_SECONDS} seconds"
    )


def _emit_connection_status_update(device_connection: DeviceConnection) -> None:
    """
    Emit a connection status update via WebSocket using the event system.

    Args:
        device_connection: The DeviceConnection instance to emit status for
    """
    try:
        DeviceConnectionService.emit_device_connection_status_update(device_connection)

        logger.debug(
            f"Emitted connection status update for device: {device_connection.name}"
        )

    except Exception as e:
        logger.error(f"Failed to emit connection status update: {str(e)}")
