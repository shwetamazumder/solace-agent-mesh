#!/usr/bin/env python3
"""
Simple CLI tool to test the PLM Writing Assistant agent without requiring an external broker.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath("."))

# Import the action class directly
from product_manager_plugin.src.agents.plm_writing_assistant.actions.plm_writing_assistant import PlmWritingAssistant
from solace_agent_mesh.common.action_response import ActionResponse

def get_user_input():
    """Get Jira issue numbers and Confluence links from user input"""
    print("\n=== PLM Writing Assistant Test CLI ===\n")
    
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
    
    # Get human prompt (optional)
    print("\nEnter additional instructions (optional):")
    human_prompt = input("> ")
    
    return jira_issues, confluence_urls, human_prompt

def main():
    # Load environment variables
    load_dotenv()
    
    # Get user input
    jira_issues, confluence_urls, human_prompt = get_user_input()
    
    # Create an instance of the action
    action = PlmWritingAssistant()
    
    # Prepare the parameters
    params = {
        "jira_issues": jira_issues,
        "confluence_urls": confluence_urls
    }
    
    # Add human prompt if provided
    if human_prompt:
        params["human_prompt"] = human_prompt
    
    # Display request summary
    print("\nRequest Summary:")
    print(f"- Jira Issues: {', '.join(jira_issues)}")
    print(f"- Confluence URLs: {', '.join(confluence_urls) if confluence_urls else 'None'}")
    if human_prompt:
        print(f"- Additional Instructions: {human_prompt}")
    
    print("\nProcessing request...")
    
    # Invoke the action
    try:
        response = action.invoke(params)
        
        # Display the response
        print("\n=== Response ===\n")
        if isinstance(response, ActionResponse):
            print(response.message)
        else:
            print(response)
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()