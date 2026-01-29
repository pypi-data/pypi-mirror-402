import useStartFlightWizardStore from "./stores/start_flight_wizard";
import useMissionControlStore from "./stores/mission_control";
import StartFlightWizard from "./components/wizard/StartFlightWizard";

const { importWhiteboxComponent } = Whitebox;

const PrimaryButton = importWhiteboxComponent("ui.button-primary");

const TriggerButton = () => {
  const { isOpen, open, close } = useStartFlightWizardStore();

  const { isFlightSessionActive, toggleFlightSession } =
    useMissionControlStore();

  const handleClick = () => {
    if (isFlightSessionActive()) {
      toggleFlightSession();
    } else {
      open();
    }
  };

  if (!isOpen) {
    return (
      <PrimaryButton
        text={isFlightSessionActive() ? "End flight" : "Start flight"}
        className="font-semibold"
        onClick={handleClick}
      />
    );
  }

  return <StartFlightWizard onClose={close} />;
};

export { TriggerButton };
export default TriggerButton;
