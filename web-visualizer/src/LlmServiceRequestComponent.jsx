import React, { useState } from "react";
import LlmServiceResponseComponent from "./LlmServiceResponseComponent";

const LlmServiceRequestComponent = ({ message, elapsedTime }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="message-box llm-service-request">
      <div className="message-header">
        <span className="message-type">LLM Service Request</span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      <div className="message-content">
        {expanded ? (
          <pre>{JSON.stringify(message.content, null, 2)}</pre>
        ) : (
          <p>{JSON.stringify(message.content).slice(0, 100)}...</p>
        )}
        <button className="more-button" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show Less" : "Show More"}
        </button>
      </div>
      {message.response && (
        <LlmServiceResponseComponent
          message={message.response}
          elapsedTime={message.response.elapsedTime}
        />
      )}
    </div>
  );
};

export default LlmServiceRequestComponent;
