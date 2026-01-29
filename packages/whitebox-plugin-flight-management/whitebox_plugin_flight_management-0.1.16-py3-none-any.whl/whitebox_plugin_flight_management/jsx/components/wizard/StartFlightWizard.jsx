import useStartFlightWizardStore from "../../stores/start_flight_wizard";
import useMissionControlStore from "../../stores/mission_control";
import useFlightPlanStore from "../../stores/flight_plan";
import InstalledDevicesStep from "./steps/InstalledDevicesStep";
import PreviewConnectedDevicesStep from "./steps/PreviewConnectedDevicesStep";
import FlightPlanStep from "./steps/FlightPlanStep";

const { importWhiteboxComponent } = Whitebox;

const StartFlightWizardStepWidget = ({ thisStepNumber }) => {
  const { stepNumber, setStep } = useStartFlightWizardStore();

  return (
    <div
      className={`w-full border-4 rounded-full ${
        thisStepNumber === stepNumber ? "border-gray-1" : "border-gray-5"
      }`}
      onClick={() => setStep(thisStepNumber)}
    ></div>
  );
};

const StartFlightWizardStepsWidget = () => {
  const { stepNumber, maxStepNumber } = useStartFlightWizardStore();

  return (
    <div>
      <div className="flex gap-2 mb-4 w-full">
        <StartFlightWizardStepWidget thisStepNumber={1} />
        <StartFlightWizardStepWidget thisStepNumber={2} />
        <StartFlightWizardStepWidget thisStepNumber={3} />
      </div>
      <p className="font-light text-base text-gray-2">
        Step {stepNumber} of {maxStepNumber}
      </p>
    </div>
  );
};

const StartFlightWizardContent = () => {
  const { stepNumber } = useStartFlightWizardStore();

  return (
    <div className="px-64 py-8">
      <StartFlightWizardStepsWidget />
      {stepNumber === 1 && <InstalledDevicesStep />}
      {stepNumber === 2 && <PreviewConnectedDevicesStep />}
      {stepNumber === 3 && <FlightPlanStep />}
    </div>
  );
};

const StartFlightWizardFooterNav = () => {
  const PrimaryButton = importWhiteboxComponent("ui.button-primary");
  const SecondaryButton = importWhiteboxComponent("ui.button-secondary");
  const { close, nextStep } = useStartFlightWizardStore();

  return (
    <div className="flex justify-between px-8 py-4 border-t border-gray-5">
      <SecondaryButton text="Close" onClick={close} />
      <PrimaryButton text="Next" onClick={nextStep} />
    </div>
  );
};

const StartFlightWizardFooterFinal = () => {
  const PrimaryButton = importWhiteboxComponent("ui.button-primary");
  const SecondaryButton = importWhiteboxComponent("ui.button-secondary");
  const { setCompleteLater, close } = useStartFlightWizardStore();
  const { enterFlightMode } = useMissionControlStore();

  const { toggleFlightSession } = useMissionControlStore();
  const { getFlightPlan } = useFlightPlanStore();

  const handleStartFlight = () => {
    // Get flight plan data from the store
    const flightPlan = getFlightPlan();

    // Prepare flight plan data in the format expected by the backend
    const flightPlanData = {
      takeoff_location: flightPlan.takeOffLocation,
      arrival_location: flightPlan.arrivalLocation,
      waypoints: flightPlan.waypoints.map((wp) => ({
        id: wp.id,
        name: wp.name,
        icao: wp.icao,
        coordinates: wp.coordinates,
      })),
    };

    toggleFlightSession(flightPlanData);
    setCompleteLater(false);
    enterFlightMode();
    close();
  };

  return (
    <div className="flex justify-between px-8 py-4 border-t border-gray-5">
      <SecondaryButton
        text="Complete later"
        onClick={() => setCompleteLater(true)}
      />
      <PrimaryButton text="Start Flight" onClick={handleStartFlight} />
    </div>
  );
};

const StartFlightWizard = ({ onClose }) => {
  const FullScreenPopOut = importWhiteboxComponent("ui.full-screen-pop-out");
  const { stepNumber, maxStepNumber } = useStartFlightWizardStore();

  return (
    <>
      <FullScreenPopOut title="Flight #010" onClose={onClose}>
        <div className="h-full flex flex-col min-h-0">
          {/* Scrollable content area */}
          <div className="flex-1 overflow-y-auto">
            <StartFlightWizardContent />
          </div>

          {/* Fixed button bar at bottom */}
          {stepNumber < maxStepNumber && <StartFlightWizardFooterNav />}
          {stepNumber === maxStepNumber && <StartFlightWizardFooterFinal />}
        </div>
      </FullScreenPopOut>
    </>
  );
};

export default StartFlightWizard;
