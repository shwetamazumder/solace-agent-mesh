#!/usr/bin/env python3
"""
Test script for the PLM Writing Assistant agent using Solace Agent Mesh.
"""

import os
import sys
import json
import tempfile
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed and install them if needed"""
    required_packages = ['click', 'pyyaml']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing required dependencies: {', '.join(missing_packages)}")
        
        # Try different pip commands until one works
        pip_commands = [
            [sys.executable, "-m", "pip", "install"],  # Use the current Python's pip
            ["pip", "install"],                        # Try system pip
            ["pip3", "install"],                       # Try pip3
        ]
        
        success = False
        for cmd in pip_commands:
            try:
                subprocess.check_call(cmd + missing_packages)
                success = True
                break
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        if success:
            print("Dependencies installed successfully")
        else:
            print("Failed to install dependencies. Please install them manually:")
            print(f"pip install {' '.join(missing_packages)}")
            sys.exit(1)

def get_user_input():
    """Get Jira issue numbers and Confluence links from user input"""
    print("\n=== PLM Writing Assistant ===\n")
    
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

def create_test_config(jira_issues, confluence_urls):
    """Create a test configuration file for the PLM Writing Assistant agent"""
    # Create a temporary YAML file
    config_path = Path("test_plm_config.yaml")
    
    # First, copy the existing configuration file
    source_config_path = Path("product_manager_plugin/configs/agents/plm_writing_assistant.yaml")
    with open(source_config_path, "r") as src_file:
        config_content = src_file.read()
    
    # Modify the configuration to use dev mode
    config_content = config_content.replace(
        "dev_mode: ${SOLACE_DEV_MODE, false}",
        "dev_mode: true"
    )
    
    # Write the modified configuration to the test config file
    with open(config_path, "w") as f:
        f.write(config_content)
    
    return config_path

def run_sam_command(config_path):
    """Run the Solace Agent Mesh command with the given configuration"""
    print(f"\nRunning Solace Agent Mesh with configuration: {config_path}")
    print("\nAfter the agent starts, open a new terminal and run:")
    print("\033[1m    solace-agent-mesh chat\033[0m")
    print("\nThis will open the SAM chat interface where you can interact with your agent.")
    print("Press Ctrl+C to stop the agent when done")
    
    try:
        # Use Python3 to run the SAM CLI module directly
        # This still uses the full Solace Agent Mesh framework
        process = subprocess.Popen(
            ["python3", "-m", "cli.main", "run", str(config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end="")
            
            # If we see a response from the agent, highlight it
            if "PLM Writing Assistant Response:" in line:
                print("\n" + "=" * 80)
                print("RESPONSE RECEIVED! See above for the generated content.")
                print("=" * 80)
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        process.terminate()
    except Exception as e:
        print(f"\nError running solace-agent-mesh: {e}")
    
    return

def main():
    # Check for required dependencies
    check_dependencies()
    
    # Get user input
    jira_issues, confluence_urls = get_user_input()
    
    # Display request summary
    print("\nTest Configuration:")
    print(f"- Jira Issues: {', '.join(jira_issues)}")
    print(f"- Confluence URLs: {', '.join(confluence_urls) if confluence_urls else 'None'}")
    
    # Create test configuration
    config_path = create_test_config(jira_issues, confluence_urls)
    
    # Run the SAM command
    run_sam_command(config_path)
    
    # Clean up
    print(f"\nRemoving test config: {config_path}")
    try:
        os.remove(config_path)
    except:
        pass

if __name__ == "__main__":
    main()