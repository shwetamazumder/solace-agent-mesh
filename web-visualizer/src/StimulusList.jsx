import React from 'react';

const StimulusList = ({ stimuli, selectedStimulusId, onSelectStimulus }) => {
  const truncateText = (text, maxLength) => {
    if (!text) return 'No text content';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  if (Object.keys(stimuli).length === 0) {
    return (
      <div className="stimulus-list">
        <div className="placeholder-message">No stimuli available. New stimuli will appear here.</div>
      </div>
    );
  }

  return (
    <div className="stimulus-list">
      {Object.entries(stimuli).map(([stimulus_uuid, stimulus]) => (
        <div 
          key={stimulus_uuid} 
          className={`stimulus-item ${selectedStimulusId === stimulus_uuid ? 'selected' : ''}`}
          onClick={() => onSelectStimulus(stimulus_uuid)}
        >
          <div className="stimulus-header">
            <span className="user-email">{stimulus.content.identity || 'No identity'}</span>
            <span className="timestamp">{formatTimestamp(stimulus.timestamp)}</span>
          </div>
          <pre className="stimulus-text">{truncateText(stimulus.content.text, 200)}</pre>
        </div>
      ))}
    </div>
  );
};

export default StimulusList;
