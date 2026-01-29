import { useEffect } from "react";
import useDevicesStore from "./stores/devices";

const { toasts } = Whitebox;

const DeviceManagerServiceComponent = () => {
  // Immediately on page load, fetch device list and populate the state store
  // with it, so that it's immediately available anywhere it's needed

  const fetchDevices = useDevicesStore((state) => state.fetchDevices);
  const updateDeviceConnectionStatus = useDevicesStore(
    (state) => state.updateDeviceConnectionStatus
  );

  useEffect(() => {
    fetchDevices();
  }, []);

  useEffect(() => {
    return Whitebox.sockets.addEventListener(
      "management",
      "message",
      (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "device.connection_status.update") {
          updateDeviceConnectionStatus(
            data.data.id,
            data.data.connection_status
          );

          // Show error toast if connection failed
          if (
            data.data.connection_status === "failed" &&
            data.data.connection_error_message
          ) {
            toasts.error({ message: data.data.connection_error_message });
          }
        }
      }
    );
  }, []);

  return null;
};

export { DeviceManagerServiceComponent };
export default DeviceManagerServiceComponent;
