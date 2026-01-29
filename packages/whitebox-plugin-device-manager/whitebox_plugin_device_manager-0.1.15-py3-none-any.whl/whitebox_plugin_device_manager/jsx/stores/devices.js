import { create } from "zustand";

const { api, toasts } = Whitebox;

const devicesStore = (set) => ({
  fetchState: "initial",
  devices: null,

  fetchDevices: async () => {
    let data;

    const url = api.getPluginProvidedPath(
      "device.device-connection-management"
    );

    try {
      const response = await api.client.get(url);
      data = await response.data;
    } catch {
      set({ fetchState: "error" });
      return false;
    }

    set({
      devices: data,
      fetchState: "loaded",
    });
    return true;
  },

  toggleDeviceConnection: async (deviceId, isConnected) => {
    const url = api.getPluginProvidedPath(
      "device.device-connection-management"
    );

    try {
      const usePath = isConnected ? "wifi/disconnect" : "wifi/connect";
      const fullUrl = `${url}${usePath}?device_id=${deviceId}`;
      await api.client.get(fullUrl);
      // State will be updated via WebSocket event in DeviceManagerServiceComponent
    } catch (e) {
      console.error("Error toggling device connection:", e);
      toasts.error({ message: "Failed to toggle device connection" });
    }
  },

  updateDeviceConnectionStatus: (deviceId, newStatus) => {
    set((state) => {
      if (!state.devices) {
        return state;
      }

      const updatedDevices = state.devices.map((device) => {
        if (device.id === deviceId) {
          return {
            ...device,
            connection_status: newStatus,
          };
        }
        return device;
      });

      return { devices: updatedDevices };
    });
  },
});

const useDevicesStore = create(devicesStore);

export default useDevicesStore;
