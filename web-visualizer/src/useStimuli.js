import { useState, useCallback, useEffect } from "react";
import { getFromIndexedDB, clearIndexedDB } from "./IndexedDBManager";

const useStimuli = () => {
  const [stimuli, setStimuli] = useState({});
  const [isLoading, setIsLoading] = useState(true);

  const handleNewMessage = useCallback((message) => {
    setStimuli((prev) => {
      let updatedStimuli = { ...prev };
      const clientMsgId = message.stimulus_uuid;

      if (message.type === "stimulus") {
        if (!updatedStimuli[clientMsgId]) {
          updatedStimuli[clientMsgId] = {
            ...message,
            responses: [],
          };
        }
      } else if (
        [
          "OrchestratorReinvoke",
          "response",
          "streamingResponse",
          "responseComplete",
          "actionRequest",
          "actionResponse",
          "llmServiceRequest",
          "llmServiceResponse",
        ].includes(message.type)
      ) {
        if (!updatedStimuli[clientMsgId]) {
          // Just drop the message if there is no stimulus to attach it to
          return prev;
        }

        if (message.type === "streamingResponse") {
          const { uuid, first_chunk, last_chunk, text } = message.content;
          const existingResponseIndex = updatedStimuli[
            clientMsgId
          ].responses.findIndex(
            (response) =>
              response.type === "streamingResponse" &&
              response.content.uuid === uuid
          );

          if (existingResponseIndex !== -1) {
            // Update existing streaming response
            updatedStimuli[clientMsgId].responses[
              existingResponseIndex
            ].content.text = text;
            updatedStimuli[clientMsgId].responses[
              existingResponseIndex
            ].content.last_chunk = last_chunk;
          } else if (first_chunk) {
            // Add new streaming response
            updatedStimuli[clientMsgId].responses.push(message);
          }
        } else if (message.type === "llmServiceResponse") {
          // For LLM Service Responses, just replace the existing response inside the llm request
          const llmRequestIndex = updatedStimuli[
            clientMsgId
          ].responses.findIndex(
            (response) =>
              response.type === "llmServiceRequest" &&
              message.broker_request_reply &&
              message.broker_request_reply[0]?.request_id &&
              response.broker_request_reply[0]?.request_id ===
                message.broker_request_reply[0]?.request_id
          );

          if (llmRequestIndex !== -1) {
            updatedStimuli[clientMsgId].responses[llmRequestIndex].response =
              message;
          } else {
            const messageExists = updatedStimuli[clientMsgId].responses.some(
              (response) =>
                response.timestamp === message.timestamp &&
                response.type === message.type
            );

            if (!messageExists) {
              updatedStimuli[clientMsgId].responses.push(message);
            }
          }
        } else {
          // For non-streaming responses, check if the message already exists
          const messageExists = updatedStimuli[clientMsgId].responses.some(
            (response) =>
              response.timestamp === message.timestamp &&
              response.type === message.type
          );

          if (!messageExists) {
            updatedStimuli[clientMsgId].responses.push(message);
          }
        }
      }

      // Sort the stimuli by timestamp (oldest first)
      const sortedEntries = Object.entries(updatedStimuli).sort(
        (a, b) => new Date(a[1].timestamp) - new Date(b[1].timestamp)
      );
      return Object.fromEntries(sortedEntries);
    });
  }, []);

  const handleDiscardStimuli = useCallback(async () => {
    if (window.confirm("Are you sure you want to discard all stimuli?")) {
      setIsLoading(true);
      await clearIndexedDB();
      setStimuli({});
      setIsLoading(false);
    }
  }, []);

  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      const storedStimuli = await getFromIndexedDB();
      const sortedStimuli = Object.fromEntries(
        Object.entries(storedStimuli).sort(
          (a, b) => new Date(a[1].timestamp) - new Date(b[1].timestamp)
        )
      );
      setStimuli(sortedStimuli);
    } catch (error) {
      console.error("Error loading initial data:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  return {
    stimuli,
    isLoading,
    handleNewMessage,
    handleDiscardStimuli,
    loadInitialData,
  };
};

export default useStimuli;
