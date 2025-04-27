#!/usr/bin/env python3
"""
Test script that generates a test configuration for the PLM Writing Assistant
and runs it using the solace-agent-mesh CLI.
"""

import os
import sys
import json
import subprocess
import tempfile

def get_user_input():
    """Get Jira issue numbers and Confluence links from user input"""
    print("\n=== PLM Writing Assistant Test ===\n")
    
    # Get Jira issues
    jira_issues = []
    print("Enter Jira issue numbers (one per line, leave blank when done):")
    while True:
        issue = input("> ")
        if not issue:
            break
        jira_issues.append(issue)
    
    if not jira_issues:
        print("No Jira issues entered. Adding a default example.")
        jira_issues = ["PLM-123"]
    
    # Get Confluence links
    confluence_urls = []
    print("\nEnter Confluence page URLs (one per line, leave blank when done):")
    while True:
        url = input("> ")
        if not url:
            break
        confluence_urls.append(url)
    
    return jira_issues, confluence_urls

def main():
    # Get user input
    jira_issues, confluence_urls = get_user_input()
    
    # Create a temporary test config file
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as f:
        test_config = f.name
        f.write(f"""# Test configuration for PLM Writing Assistant
---
log:
  stdout_log_level: INFO
  log_file_level: INFO
  log_file: solace_ai_connector.log

# Test data
test_data:
  jira_issues: {jira_issues}
  confluence_urls: {confluence_urls}

# Run the agent in dev mode
shared_config:
  - broker_config: &broker_connection
      dev_mode: true
      broker_url: ws://localhost:8008
      broker_username: admin
      broker_password: admin
      broker_vpn: default
      temporary_queue: false

flows:
  - name: test_plm_writing_assistant
    components:
      - component_name: action_request_processor
        component_base_path: .
        component_module: product_manager_plugin.src.agents.plm_writing_assistant.plm_writing_assistant_agent_component
        component_config:
          llm_service_topic: shweta_ai_project/solace-agent-mesh/v1/llm-service/request/general-good/
          embedding_service_topic: shweta_ai_project/solace-agent-mesh/v1/embedding-service/request/text/
        broker_request_response:
          enabled: true
          broker_config: *broker_connection
          request_expiry_ms: 120000
          payload_encoding: utf-8
          payload_format: json
          response_topic_prefix: shweta_ai_project/solace-agent-mesh/v1
          response_queue_prefix: shweta_ai_project/solace-agent-mesh/v1
""")
    
    # Display request summary
    print("\nTest Configuration:")
    print(f"- Jira Issues: {', '.join(jira_issues)}")
    print(f"- Confluence URLs: {', '.join(confluence_urls) if confluence_urls else 'None'}")
    
    # Run the solace-agent-mesh CLI with the test config
    print(f"\nRunning solace-agent-mesh with test config: {test_config}")
    print("Press Ctrl+C to stop the test")
    
    try:
        # Use the full path to the solace-agent-mesh command or use python -m
        subprocess.run(['python', '-m', 'cli.main', 'run', test_config], check=True)
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\nError running solace-agent-mesh: {e}")
    finally:
        # Clean up the temporary file
        os.unlink(test_config)
        print(f"Removed temporary test config: {test_config}")

if __name__ == "__main__":
    main()