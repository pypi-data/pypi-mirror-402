import DeviceConnection from "./common/DeviceConnection";
import useDevicesStore from "./stores/devices";

const { utils } = Whitebox;

const ToggleButton = ({ isEnabled, onClick, disabled = false }) => {
  return (
    <>
      <label
        className={`flex cursor-pointer select-none items-center ${
          disabled ? "opacity-50 cursor-not-allowed" : ""
        }`}
      >
        <div className="relative">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={disabled ? undefined : onClick}
            disabled={disabled}
            className="sr-only"
          />
          <div
            className={`block h-8 w-14 rounded-full transition-colors ${
              isEnabled ? "bg-full-emphasis" : "bg-gray-5"
            }`}
          ></div>
          <div
            className={`dot absolute left-1 top-1 h-6 w-6 rounded-full transition-all ${
              isEnabled ? "bg-white translate-x-6" : "bg-gray-3"
            }`}
          ></div>
        </div>
      </label>
    </>
  );
};

const ToggleableDeviceList = () => {
  const devices = useDevicesStore((state) => state.devices);
  const toggleDeviceConnection = useDevicesStore(
    (state) => state.toggleDeviceConnection
  );

  // Show message when no devices are available
  if (!devices || devices.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center self-stretch gap-2">
        <p className="text-gray-4 text-lg">No devices installed</p>
      </div>
    );
  }

  // Render list of devices with toggle buttons
  const deviceComponents = devices.map((device, index) => {
    const isConnected = device.connection_status === "connected";
    const isTransitioning =
      device.connection_status === "connecting" ||
      device.connection_status === "disconnecting";

    // Show connection info for transitioning states
    const getConnectionInfo = () => {
      if (device.connection_status === "connecting") return "Connecting...";
      if (device.connection_status === "disconnecting")
        return "Disconnecting...";
      if (device.connection_status === "failed") return "Connection failed";
      return null;
    };

    const handleToggle = () => {
      if (!isTransitioning) {
        toggleDeviceConnection(device.id, isConnected);
      }
    };

    const action = (
      <ToggleButton
        isEnabled={isConnected || device.connection_status === "connecting"}
        onClick={handleToggle}
        disabled={isTransitioning}
      />
    );

    const iconUrl = utils.buildStaticUrl(device.device_type_icon_url);
    const icon = <img src={iconUrl} alt={device.name} />;

    return (
      <DeviceConnection
        key={index}
        deviceName={device.name}
        isConnected={isConnected || device.connection_status === "connecting"}
        connectionInfo={getConnectionInfo()}
        icon={icon}
        action={action}
      />
    );
  });

  return (
    <div className="flex flex-1 flex-col items-center self-stretch gap-2">
      {deviceComponents}
    </div>
  );
};

export { ToggleableDeviceList };
export default ToggleableDeviceList;
