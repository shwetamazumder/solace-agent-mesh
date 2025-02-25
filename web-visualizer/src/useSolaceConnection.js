import { useCallback, useEffect, useState } from "react";
import SolaceManager from "./solaceManager";
import io from "socket.io-client";
import { processMessage, processCapabilityMessage } from "./messageProcessor";

const useSolaceConnection = (onMessage) => {
  const [solaceManager] = useState(new SolaceManager());
  const [connected, setConnected] = useState(false);
  const [socket, setSocket] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);

  const connectToSolace = useCallback(
    async (config) => {
      if (!config || isConnecting) {
        console.info("No configuration provided or already connecting");
        return;
      }
      const connectionType = config.connectionType || "solace";
      
      setIsConnecting(true);
      try {
        setConnected(false);
        if (connectionType === "solace") {
          solaceManager.disconnect();
          await solaceManager.connect(config);
          solaceManager.setMessageCallback(onMessage);
          setConnected(true);
        } else {
          if (socket) {
            socket.disconnect();
          }
          const newSocket = io(config.websocketUrl, {
            transports: ["websocket"],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
          });

          newSocket.on("connect", () => {
            setSocket(newSocket);
            setConnected(true);
          });

          newSocket.on("message", (data) => {
            // First parse the JSON data
            try {
              data = JSON.parse(data);
            } catch (error) {
              console.error(
                "Error parsing JSON data in websocket received message:",
                error,
                data
              );
              return;
            }
            const { payload, topic, user_properties } = data;
            const processedMessage = processMessage(
              topic,
              payload,
              user_properties
            );
            if (processedMessage) {
              onMessage(processedMessage);
            }
          });

          newSocket.on("capability", (data) => {
            const processedCapability = processCapabilityMessage(data);
            if (solaceManager.capabilityCallback) {
              solaceManager.capabilityCallback(processedCapability);
            }
          });

          newSocket.on("connect_error", (error) => {
            console.error("Socket.IO connection error:", error);
            setConnected(false);
          });

          newSocket.on("disconnect", (reason) => {
            console.log("Socket.IO connection closed:", reason);
            setConnected(false);
          });

          setSocket(newSocket);        }
      } catch (error) {
        console.error("Error connecting:", error);
        setConnected(false);
        throw error;
      } finally {
        setIsConnecting(false);
      }
    },
    [onMessage, socket, solaceManager, isConnecting]
  );

  const disconnect = useCallback(() => {
    if (solaceManager) {
      solaceManager.disconnect();
    }
    if (socket) {
      socket.disconnect();
    }
    setConnected(false);
    setSocket(null);
  }, [solaceManager, socket]);

  useEffect(() => {
    return disconnect;
  }, [disconnect]);

  return [connectToSolace, disconnect, connected, setConnected];
};

export default useSolaceConnection;
