const StepIntro = ({ title, description }) => {
  return (
    <div className="py-6">
      <h2 className="font-bold text-3xl">{title}</h2>
      <p className="font-light text-base text-gray-2">{description}</p>
    </div>
  );
};

export default StepIntro;
