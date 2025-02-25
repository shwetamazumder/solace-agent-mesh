import React from 'react';

const StimulusDetails = ({ selectedStimulus }) => {
  return (
    <div className="w-2/3 p-4">
      <h2 className="text-xl font-bold mb-4">Stimulus Flow</h2>
      {selectedStimulus ? (
        <pre>{JSON.stringify(selectedStimulus, null, 2)}</pre>
      ) : (
        <p>Select a stimulus to view its flow</p>
      )}
    </div>
  );
};

export default StimulusDetails;
