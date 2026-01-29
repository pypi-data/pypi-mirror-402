import StepIntro from "../StepIntro";

const { importWhiteboxComponent } = Whitebox;

const PreviewConnectedDevicesStep = () => {
  const InputPreview = importWhiteboxComponent("device.camera-input-preview");

  return (
    <>
      <StepIntro
        title="Preview Connected Devices"
        description="Preview the inputs to ensure everything is in place and connected."
      />
      <InputPreview />
    </>
  );
};

export default PreviewConnectedDevicesStep;
