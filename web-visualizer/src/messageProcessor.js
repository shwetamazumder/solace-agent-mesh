export function processMessage(topic, content, userProperties) {
  console.log("EDE Processing message:", topic, content, userProperties);
  let type;
  if (topic.includes("orchestrator/reinvokeModel")) {
    type = "orchestratorReinvoke";
  } else if (topic.includes("solace-agent-mesh/v1/stimulus/")) {
    type = "stimulus";
  } else if (topic.includes("solace-agent-mesh/v1/response/")) {
    type = "response";
  } else if (topic.includes("solace-agent-mesh/v1/streamingResponse/")) {
    type = "streamingResponse";
  } else if (topic.includes("solace-agent-mesh/v1/responseComplete/")) {
    type = "responseComplete";
  } else if (topic.includes("solace-agent-mesh/v1/actionRequest/")) {
    type = "actionRequest";
  } else if (topic.includes("solace-agent-mesh/v1/actionResponse/")) {
    type = "actionResponse";
  } else if (topic.includes("solace-agent-mesh/v1/register/agent/")) {
    type = "registration";
  } else if (topic.includes("solace-agent-mesh/v1/llm-service/request/")) {
    type = "llmServiceRequest";
  } else if (topic.includes("solace-agent-mesh/v1/llm-service/response/")) {
    type = "llmServiceResponse";
  } else {
    console.warn("Unknown message type for topic:", topic);
    return null;
  }
  const stimulus_uuid = userProperties.stimulus_uuid;

  let broker_request_reply = null;
  if (userProperties.__solace_ai_connector_broker_request_reply_metadata__) {
    try {
      broker_request_reply = JSON.parse(
        userProperties.__solace_ai_connector_broker_request_reply_metadata__
          ._value ||
          userProperties.__solace_ai_connector_broker_request_reply_metadata__
      );
    } catch (error) {
      console.warn("Failed to parse broker request reply metadata:", error);
    }
  }

  return {
    type,
    content,
    userProperties,
    stimulus_uuid,
    timestamp: new Date().toISOString(),
    broker_request_reply,
  };
}

export function processCapabilityMessage(content) {
  return {
    type: "capability",
    content: content,
    timestamp: new Date().toISOString(),
  };
}
