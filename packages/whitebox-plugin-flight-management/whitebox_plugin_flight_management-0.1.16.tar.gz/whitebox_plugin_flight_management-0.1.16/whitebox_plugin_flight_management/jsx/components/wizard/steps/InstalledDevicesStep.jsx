import { useEffect } from "react";
import StepIntro from "../StepIntro";

const { importWhiteboxComponent, importWhiteboxStateStore } = Whitebox;

const InstalledDevicesStep = () => {
  const DeviceList = importWhiteboxComponent("device-wizard.device-list");

  useEffect(() => {
    async function fetchDevices() {
      const useDevicesStore = await importWhiteboxStateStore("devices");
      const _fetchDevices = useDevicesStore.getState().fetchDevices;
      _fetchDevices();
    }

    fetchDevices();
  }, []);

  return (
    <>
      <StepIntro
        title="Installed Devices"
        description="To get the best experience, ensure that your devices are connected."
      />
      <DeviceList />
    </>
  );
};

export default InstalledDevicesStep;
