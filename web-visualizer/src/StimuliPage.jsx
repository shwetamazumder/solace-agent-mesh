import { useState, useEffect } from "react";
import StimulusList from "./StimulusList";
import MessageFlow from "./MessageFlow";
import useStimuli from "./useStimuli";

const StimuliPage = () => {
  const [selectedStimulusId, setSelectedStimulusId] = useState(null);
  const { stimuli, isLoading, handleNewMessage, handleDiscardStimuli } = useStimuli();

  // Listen for new messages from App.jsx
  useEffect(() => {
    const handleNewMessageEvent = (event) => {
      handleNewMessage(event.detail);
    };

    const element = document.querySelector('.stimuli-page');
    if (element) {
      element.addEventListener('newMessage', handleNewMessageEvent);
      return () => {
        element.removeEventListener('newMessage', handleNewMessageEvent);
      };
    }
  }, [handleNewMessage]);
  const selectedStimulus = selectedStimulusId
    ? stimuli[selectedStimulusId]
    : null;

  return (
    <div className="stimuli-page">
      <div className="page-header">
        <h2>Stimuli</h2>
        <button
          className="button"
          onClick={handleDiscardStimuli}
          disabled={isLoading}
        >
          Discard All Stimuli
        </button>
      </div>
      <div className="stimuli-content">
        <StimulusList
          stimuli={stimuli}
          selectedStimulusId={selectedStimulusId}
          onSelectStimulus={setSelectedStimulusId}
        />
        <MessageFlow selectedStimulus={selectedStimulus} />
      </div>
      {isLoading && <div className="loading-overlay">Loading...</div>}
    </div>
  );
};

export default StimuliPage;
