---
title: Monitors
sidebar_position: 30
---

# Monitors


Monitors are passive components within the Solace Agent Mesh framework that observe system behavior by subscribing to events flowing through the system. 

Monitors can serve functions such as system monitoring, policy enforcement, analytics collection, and automated notification generation.

:::tip[In one sentence]
Monitors are essentially the system's passive observers.
:::

## Key Functions

1. **Event Subscription**: 
   - Subscribe to Solace Agent Mesh events of interest
   - Can monitor any event type including stimuli, actions, agent registrations, etc.
   - Use topic wildcards to efficiently capture relevant event streams

2. **Policy Enforcement**:
   - Verify system behavior against defined policies and constraints
   - Monitor for security violations
   - Ensure compliance with business rules and operational guidelines
   - Can trigger notifications or corrective actions when violations occur

3. **Analytics Collection**:
   - Gather metrics about system performance and behavior
   - Track usage patterns and event flows
   - Collect statistics about component interactions
   - Enable data-driven optimization of system configuration

4. **Automated Notifications**:
   - Raise alerts when anomalies or issues are detected
   - Optionally generate notifications through multiple channels:
     - Creating new stimuli in the system
     - Calling agents to post to external systems

5. **Debugging Support**:
   - Maintain detailed stimulus lifecycle logs
   - Help diagnose issues by tracking event patterns
   - Support interactive debugging sessions
   - Provide visibility into system internals

## Implementation Approaches

Monitors can be implemented in several ways depending on their purpose:

1. **Simple Event Loggers**:
   - Subscribe to events and log them for analysis
   - Minimal processing, focused on data collection
   - Useful for audit trails and debugging

2. **Policy Checkers**:
   - Apply rule engines to verify event compliance
   - Can block or flag non-compliant actions
   - Maintain policy enforcement statistics

3. **Analytics Engines**:
   - Process event streams to generate metrics
   - May use complex event processing (CEP)
   - Generate reports and dashboards

4. **Active Monitors**:
   - Watch for specific conditions or patterns
   - Trigger automated responses when needed
   - May create new stimuli or call agents

## Interaction with Other Components

Monitors primarily interact with:

1. **Event Broker**:
   - Subscribe to relevant event topics
   - May publish notification events
   - Use broker features for efficient event filtering

2. **Agents**:
   - May call agents to perform actions (e.g., sending notifications)
   - Can monitor agent behavior and performance
   - Track agent registration and capabilities

3. **Gateways**:
   - Monitor incoming/outgoing traffic patterns
   - Track gateway performance and errors
   - Verify gateway configuration compliance

4. **Orchestrator**:
   - Observe workflow patterns and decisions
   - Monitor orchestration performance
   - Track stimulus processing flows

By implementing appropriate monitors, organizations can ensure their Solace Agent Mesh deployment operates efficiently, securely, and reliably while maintaining compliance with all relevant policies and constraints.
