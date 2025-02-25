import solace from "solclientjs";
import { processMessage } from "./messageProcessor";

const factoryProps = new solace.SolclientFactoryProperties();
factoryProps.profile = solace.SolclientFactoryProfiles.version10_5;
solace.SolclientFactory.init(factoryProps);
solace.SolclientFactory.setLogLevel(solace.LogLevel.DEBUG);

class SolaceManager {
  constructor() {
    this.session = null;
    this.messageCallback = null;
    this.capabilityCallback = null;
    this.registrationCallback = null;
  }

  async connect(config) {
    try {
      // Initialize Solace client factory
      solace.SolclientFactory.init();

      // Create session
      const properties = new solace.SessionProperties({
        url: config.url,
        vpnName: config.vpnName,
        userName: config.userName,
        password: config.password,
      });

      this.session = solace.SolclientFactory.createSession(properties);

      // Define session event listeners
      this.session.on(solace.SessionEventCode.UP_NOTICE, () => {
        // Add subscriptions
        let namespace = config.namespace || "";
        namespace = namespace.endsWith("/") ? namespace : `${namespace}/`;
        const topics = [
          `${namespace}solace-agent-mesh/v1/register/>`,
          `${namespace}solace-agent-mesh/v1/stimulus/>`,
          `${namespace}solace-agent-mesh/v1/response/>`,
          `${namespace}solace-agent-mesh/v1/streamingResponse/>`,
          `${namespace}solace-agent-mesh/v1/responseComplete/>`,
          `${namespace}solace-agent-mesh/v1/actionRequest/>`,
          `${namespace}solace-agent-mesh/v1/actionResponse/>`,
          `${namespace}solace-agent-mesh/v1/orchestrator/reinvoke/>`,
          `${namespace}solace-agent-mesh/v1/llm-service/request/>`,
          `${namespace}solace-agent-mesh/v1/llm-service/response/>`,
        ];

        topics.forEach((topic) => {
          try {
            this.session.subscribe(
              solace.SolclientFactory.createTopicDestination(topic),
              true,
              topic,
              10000
            );
          } catch (subscribeError) {
            console.error("Error subscribing to topic:", topic, subscribeError);
          }
        });
      });

      this.session.on(
        solace.SessionEventCode.CONNECT_FAILED_ERROR,
        (sessionEvent) => {
          console.error("Solace connection failed:", sessionEvent.infoStr);
        }
      );

      // Connect the session
      this.session.connect();
    } catch (error) {
      console.error("Error creating Solace session:", error);
      throw error;
    }

    this.session.on(solace.SessionEventCode.MESSAGE, (message) => {
      const topic = message.getDestination().getName();
      const content = JSON.parse(message.getBinaryAttachment());
      const userProperties = {};
      const userPropertyMap = message.getUserPropertyMap();
      if (userPropertyMap) {
        userPropertyMap.getKeys().forEach((key) => {
          userProperties[key] = userPropertyMap.getField(key);
        });
      }
      console.log("EDE Processing message:", topic, content, userProperties);
      if (this.messageCallback) {
        const processedMessage = processMessage(topic, content, userProperties);
        if (processedMessage) {
          this.messageCallback(processedMessage);
        }
      }
    });
  }

  setMessageCallback(callback) {
    this.messageCallback = callback;
  }

  subscribeToCapabilities(callback) {
    this.capabilityCallback = callback;
  }

  unsubscribeFromCapabilities() {
    this.capabilityCallback = null;
  }

  disconnect() {
    if (this.session) {
      this.session.disconnect();
      this.session = null;
    }
  }
}

export default SolaceManager;
