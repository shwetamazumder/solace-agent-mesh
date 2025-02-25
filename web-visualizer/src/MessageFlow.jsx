import React from "react";
import StimulusComponent from "./StimulusComponent";
import ResponseComponent from "./ResponseComponent";
import ActionRequestComponent from "./ActionRequestComponent";
import OrchestratorReinvokeComponent from "./OrchestratorReinvokeComponent";
import LlmServiceRequestComponent from "./LlmServiceRequestComponent";
import LlmServiceResponseComponent from "./LlmServiceResponseComponent";

const MessageFlow = ({ selectedStimulus }) => {
  if (!selectedStimulus) {
    return (
      <div className="message-flow">
        <div className="placeholder-message">
          Select a stimulus to view details
        </div>
      </div>
    );
  }

  const renderMessageComponent = (
    message,
    originalStimulusTime,
    actionResponses
  ) => {
    const elapsedTime = `${(
      (new Date(message.timestamp) - new Date(originalStimulusTime)) /
      1000
    ).toFixed(2)}s`;

    switch (message.type) {
      case "stimulus":
        return (
          <StimulusComponent message={message} elapsedTime={elapsedTime} />
        );
      case "response":
      case "streamingResponse":
        return (
          <ResponseComponent
            message={message}
            elapsedTime={elapsedTime}
            isStreaming={message.type === "streamingResponse"}
          />
        );
      case "responseComplete":
        return (
          <ResponseComponent
            message={message}
            elapsedTime={elapsedTime}
            isComplete={true}
          />
        );
      case "actionRequest": {
        const response =
          actionResponses[
            `${message.content.action_list_id}-${message.content.action_idx}`
          ];
        return (
          <ActionRequestComponent
            message={message}
            elapsedTime={elapsedTime}
            response={response}
          />
        );
      }
      case "orchestratorReinvoke":
        return (
          <OrchestratorReinvokeComponent
            message={message}
            elapsedTime={elapsedTime}
          />
        );
      case "llmServiceRequest":
        return (
          <LlmServiceRequestComponent
            message={message}
            elapsedTime={elapsedTime}
          />
        );
      case "llmServiceResponse":
        return (
          <LlmServiceResponseComponent
            message={message}
            elapsedTime={elapsedTime}
          />
        );
      default:
        return null;
    }
  };

  const actionResponses = selectedStimulus.responses.reduce((acc, response) => {
    if (response.type === "actionResponse") {
      const key = `${response.content.action_list_id}-${response.content.action_idx}`;
      acc[key] = response;
    }
    return acc;
  }, {});

  return (
    <div className="message-flow">
      {renderMessageComponent(
        selectedStimulus,
        selectedStimulus.timestamp,
        actionResponses
      )}
      {selectedStimulus.responses
        .filter((response) => response.type !== "actionResponse")
        .map((response, index) =>
          renderMessageComponent(
            response,
            selectedStimulus.timestamp,
            actionResponses
          )
        )}
    </div>
  );
};

export default MessageFlow;
