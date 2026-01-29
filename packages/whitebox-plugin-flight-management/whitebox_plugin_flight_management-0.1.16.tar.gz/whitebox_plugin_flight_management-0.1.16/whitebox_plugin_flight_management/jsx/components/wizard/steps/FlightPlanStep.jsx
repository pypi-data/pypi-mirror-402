import StepIntro from "../StepIntro";
import FlightPlan from "../../flight-plan/FlightPlan";

const FlightPlanStep = () => {
  return (
    <>
      <StepIntro
        title="Flight Plan"
        description="Add some details to plan out your flight."
      />
      <FlightPlan />
    </>
  );
};

export default FlightPlanStep;
