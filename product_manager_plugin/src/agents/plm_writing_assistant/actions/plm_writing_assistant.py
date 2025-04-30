"""Simplified action to fetch Confluence pages or Jira issues and summarize them using LLM."""

import os
import re
import requests
import getpass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, find_dotenv, set_key

from solace_ai_connector.common.log import log
from solace_agent_mesh.common.action import Action
from solace_agent_mesh.common.action_response import ActionResponse

# Load environment variables
load_dotenv()

class PlmWritingAssistant(Action):
    def __init__(self, **kwargs):
        # Ensure .env file exists
        self.ensure_env_file()
        
        super().__init__(
            {
                "name": "plm_writing_assistant",
                "description": "Fetches Confluence pages or Jira issues and summarizes them into blog posts or slide content.",
                "prompt_directive": (
                    "Provide a Confluence page URL or Jira issue key/URL to fetch its content and generate a summarized blog post or slide content."
                ),
                "params": [
                    {
                        "name": "confluence_url",
                        "desc": "URL of the Confluence page to summarize (provide either this or jira_issue)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "jira_issue",
                        "desc": "Jira issue key (e.g., 'PROJECT-123') or URL to summarize (provide either this or confluence_url)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "output_type",
                        "desc": "Type of output to generate (blog_post or slide_content)",
                        "type": "string",
                        "default": "blog_post"
                    },
                    {
                        "name": "confluence_base_url",
                        "desc": "Base URL for Confluence instance (optional, uses environment variable if not provided)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "jira_base_url",
                        "desc": "Base URL for Jira instance (optional, uses environment variable if not provided)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "atlassian_email",
                        "desc": "Atlassian account email (optional, uses environment variable if not provided)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "atlassian_api_token",
                        "desc": "Atlassian API token (optional, uses environment variable if not provided)",
                        "type": "string",
                        "required": False,
                    }
                ],
                "required_scopes": ["plm_writing_assistant:generate_content:read"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        # Get input parameters
        confluence_url = params.get("confluence_url")
        jira_issue = params.get("jira_issue")
        output_type = params.get("output_type", "blog_post")
        
        # Check if either Confluence URL or Jira issue is provided
        if not confluence_url and not jira_issue:
            return ActionResponse(message="Error: Please provide either a Confluence URL or Jira issue key/URL")
        
        # Determine which source we're using
        using_confluence = confluence_url is not None
        using_jira = jira_issue is not None
        
        if using_confluence and using_jira:
            log.info("Both Confluence URL and Jira issue provided, using Confluence URL")
            using_jira = False
        
        # Get Atlassian credentials (from params or environment or prompt)
        confluence_base_url = params.get("confluence_base_url") or os.getenv("CONFLUENCE_BASE_URL")
        jira_base_url = params.get("jira_base_url") or os.getenv("JIRA_BASE_URL")
        atlassian_email = params.get("atlassian_email") or os.getenv("ATLASSIAN_EMAIL")
        atlassian_api_token = params.get("atlassian_api_token") or os.getenv("ATLASSIAN_API_TOKEN")
        
        # Get the dotenv file path for saving credentials
        dotenv_file = find_dotenv()
        if not dotenv_file:
            dotenv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            self.ensure_env_file()
        
        # Prompt for missing credentials and save them
        if using_confluence and not confluence_base_url:
            print("\n" + "="*80)
            print("Confluence Base URL Configuration")
            print("="*80)
            print("No Confluence base URL found in environment variables or parameters.")
            print("This is the base URL of your Atlassian Confluence instance.")
            print("Example: https://your-company.atlassian.net")
            print("-"*80)
            confluence_base_url = input("Please enter your Confluence base URL: ")
            if confluence_base_url:
                set_key(dotenv_file, "CONFLUENCE_BASE_URL", confluence_base_url)
                os.environ["CONFLUENCE_BASE_URL"] = confluence_base_url
                print("✓ Confluence base URL saved to environment variables.")
            else:
                print("⚠️ No base URL provided.")
        
        if using_jira and not jira_base_url:
            print("\n" + "="*80)
            print("Jira Base URL Configuration")
            print("="*80)
            print("No Jira base URL found in environment variables or parameters.")
            print("This is the base URL of your Atlassian Jira instance.")
            print("Example: https://your-company.atlassian.net")
            print("-"*80)
            jira_base_url = input("Please enter your Jira base URL: ")
            if jira_base_url:
                set_key(dotenv_file, "JIRA_BASE_URL", jira_base_url)
                os.environ["JIRA_BASE_URL"] = jira_base_url
                print("✓ Jira base URL saved to environment variables.")
            else:
                print("⚠️ No base URL provided.")
        
        if not atlassian_email:
            print("\n" + "="*80)
            print("Atlassian Account Email Configuration")
            print("="*80)
            print("No Atlassian email found in environment variables or parameters.")
            print("This is the email address associated with your Atlassian account.")
            print("-"*80)
            atlassian_email = input("Please enter your Atlassian email: ")
            if atlassian_email:
                set_key(dotenv_file, "ATLASSIAN_EMAIL", atlassian_email)
                os.environ["ATLASSIAN_EMAIL"] = atlassian_email
                print("✓ Atlassian email saved to environment variables.")
            else:
                print("⚠️ No email provided.")
        
        if not atlassian_api_token:
            print("\n" + "="*80)
            print("Atlassian API Token Configuration")
            print("="*80)
            print("No Atlassian API token found in environment variables or parameters.")
            print("You can generate a token at: https://id.atlassian.com/manage-profile/security/api-tokens")
            print("1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens")
            print("2. Click 'Create API token'")
            print("3. Enter a label for your token (e.g., 'PLM Writing Assistant')")
            print("4. Copy the generated token")
            print("-"*80)
            atlassian_api_token = getpass.getpass("Please enter your Atlassian API token (input will be hidden): ")
            if atlassian_api_token:
                set_key(dotenv_file, "ATLASSIAN_API_TOKEN", atlassian_api_token)
                os.environ["ATLASSIAN_API_TOKEN"] = atlassian_api_token
                print("✓ Atlassian API token saved to environment variables.")
            else:
                print("⚠️ No API token provided.")
        
        # Check if all required credentials are provided after prompting
        missing_credentials = []
        if using_confluence and not confluence_base_url:
            missing_credentials.append("Confluence base URL")
        if using_jira and not jira_base_url:
            missing_credentials.append("Jira base URL")
        if not atlassian_email:
            missing_credentials.append("Atlassian email")
        if not atlassian_api_token:
            missing_credentials.append("Atlassian API token")
            
        if missing_credentials:
            return ActionResponse(
                message=f"Error: Missing required credentials: {', '.join(missing_credentials)}.\n\n"
                        f"Please provide them as parameters or when prompted."
            )
        
        # Verify credentials and fetch content based on the source
        content = None
        source_name = None
        
        if using_confluence:
            # Verify Confluence credentials
            log.info("Verifying Confluence credentials...")
            print("\nVerifying Confluence credentials... ", end="")
            if not self.verify_credentials(confluence_base_url, atlassian_email, atlassian_api_token):
                print("❌ Failed!")
                return ActionResponse(
                    message="Error: Invalid Confluence credentials. Please check your base URL, email, and API token."
                )
            print("✓ Success!")
            
            # Log credentials (not the token)
            log.info("Using Confluence credentials:")
            log.info("CONFLUENCE_BASE_URL: %s", confluence_base_url)
            log.info("ATLASSIAN_EMAIL: %s", atlassian_email)
            log.info("ATLASSIAN_API_TOKEN: %s", "Present" if atlassian_api_token else "Missing")
            
            # Fetch the Confluence page content
            log.info("Fetching Confluence page: %s", confluence_url)
            content = self.fetch_confluence_page(confluence_url, confluence_base_url, atlassian_email, atlassian_api_token)
            source_name = "Confluence page"
            
        elif using_jira:
            # Verify Jira credentials
            log.info("Verifying Jira credentials...")
            print("\nVerifying Jira credentials... ", end="")
            if not self.verify_credentials(jira_base_url, atlassian_email, atlassian_api_token, is_jira=True):
                print("❌ Failed!")
                return ActionResponse(
                    message="Error: Invalid Jira credentials. Please check your base URL, email, and API token."
                )
            print("✓ Success!")
            
            # Log credentials (not the token)
            log.info("Using Jira credentials:")
            log.info("JIRA_BASE_URL: %s", jira_base_url)
            log.info("ATLASSIAN_EMAIL: %s", atlassian_email)
            log.info("ATLASSIAN_API_TOKEN: %s", "Present" if atlassian_api_token else "Missing")
            
            # Fetch the Jira issue content
            log.info("Fetching Jira issue: %s", jira_issue)
            content = self.fetch_jira_issue(jira_issue, jira_base_url, atlassian_email, atlassian_api_token)
            source_name = "Jira issue"
        
        # If fetching failed, return the error message
        if content.startswith("⚠️"):
            return ActionResponse(message=content)
        
        # Generate content based on the requested output type
        if output_type == "slide_content":
            result = self.generate_slide_content(content, source_name)
            # Include content type and URL in the message instead of using data parameter
            return ActionResponse(
                message=result
            )
        else:
            # Default to blog post
            result = self.summarize_content(content, source_name)
            # Include content type and URL in the message instead of using data parameter
            return ActionResponse(
                message=result
            )

    
    def verify_credentials(self, base_url, email, token, is_jira=False):
        """Verify Atlassian API credentials by making a test request"""
        auth = (email, token)
        try:
            if is_jira:
                # For Jira, we'll test by getting a list of projects
                test_url = f"{base_url}/rest/api/2/project"
                log.info("Verifying Jira credentials with request to: %s", test_url)
            else:
                # For Confluence, we'll test by getting a list of spaces
                test_url = f"{base_url}/rest/api/space"
                log.info("Verifying Confluence credentials with request to: %s", test_url)
                
            resp = requests.get(test_url, auth=auth)
            
            if resp.ok:
                log.info("Credentials verification successful")
                return True
            else:
                log.error("Credentials verification failed: Status %s", resp.status_code)
                return False
        except Exception as e:
            log.error("Error verifying credentials: %s", str(e))
            return False
    
    def fetch_confluence_page(self, url, base_url, email, token):
        """Fetch content from a Confluence page"""
        auth = (email, token)
        
        try:
            # Extract page ID from URL - it's the numeric part before the page title
            # URL format: .../spaces/SPACE/pages/PAGE_ID/PAGE_TITLE
            parts = url.strip("/").split("/")
            # Find "pages" in the URL and take the next part as the page ID
            for i, part in enumerate(parts):
                if part == "pages" and i + 1 < len(parts):
                    page_id = parts[i + 1]
                    break
            else:
                return f"⚠️ Could not extract page ID from URL: {url}"
                
            log.info("Extracted page ID: %s", page_id)
            api_url = f"{base_url}/rest/api/content/{page_id}?expand=body.storage"
            
            log.info("Making API request to: %s", api_url)
            resp = requests.get(api_url, auth=auth)
            
            if resp.ok:
                data = resp.json()
                title = data["title"]
                body = data["body"]["storage"]["value"]
                log.info("Successfully fetched page: %s", title)
                return f"# {title}\n\n{body}"
            else:
                error_message = f"⚠️ Failed to fetch Confluence page: Status {resp.status_code}"
                log.error("%s\nResponse: %s", error_message, resp.text[:500])
                return error_message
        except Exception as e:
            error_message = f"⚠️ Error fetching Confluence page: {str(e)}"
            log.error(error_message)
            return error_message

    def fetch_jira_issue(self, issue_key_or_url, base_url, email, token):
        """Fetch content from a Jira issue"""
        auth = (email, token)
        
        try:
            # Extract issue key from URL if a URL was provided
            # URL format: .../browse/PROJECT-123
            issue_key = issue_key_or_url
            if '/' in issue_key_or_url:
                parts = issue_key_or_url.strip('/').split('/')
                for i, part in enumerate(parts):
                    if part == "browse" and i + 1 < len(parts):
                        issue_key = parts[i + 1]
                        break
                else:
                    # Try to find the issue key using regex (format: PROJECT-123)
                    match = re.search(r'[A-Z]+-\d+', issue_key_or_url)
                    if match:
                        issue_key = match.group(0)
                    else:
                        return f"⚠️ Could not extract issue key from URL: {issue_key_or_url}"
            
            log.info("Using Jira issue key: %s", issue_key)
            api_url = f"{base_url}/rest/api/2/issue/{issue_key}"
            
            log.info("Making API request to: %s", api_url)
            resp = requests.get(api_url, auth=auth)
            
            if resp.ok:
                data = resp.json()
                issue_key = data["key"]
                summary = data["fields"]["summary"]
                description = data["fields"]["description"] or ""
                status = data["fields"]["status"]["name"]
                issue_type = data["fields"]["issuetype"]["name"]
                priority = data["fields"].get("priority", {}).get("name", "N/A")
                
                # Format the content
                content = f"# {issue_key}: {summary}\n\n"
                content += f"**Type:** {issue_type}\n"
                content += f"**Status:** {status}\n"
                content += f"**Priority:** {priority}\n\n"
                content += f"## Description\n\n{description}\n\n"
                
                # Add comments if available
                comments_url = f"{base_url}/rest/api/2/issue/{issue_key}/comment"
                comments_resp = requests.get(comments_url, auth=auth)
                if comments_resp.ok:
                    comments_data = comments_resp.json()
                    if comments_data["comments"]:
                        content += "## Comments\n\n"
                        for comment in comments_data["comments"]:
                            author = comment["author"]["displayName"]
                            body = comment["body"]
                            content += f"**{author}:**\n{body}\n\n"
                
                log.info("Successfully fetched Jira issue: %s", issue_key)
                return content
            else:
                error_message = f"⚠️ Failed to fetch Jira issue: Status {resp.status_code}"
                log.error("%s\nResponse: %s", error_message, resp.text[:500])
                return error_message
        except Exception as e:
            error_message = f"⚠️ Error fetching Jira issue: {str(e)}"
            log.error(error_message)
            return error_message
    
    def summarize_content(self, content, source_name):
        """Summarize content using the LLM service"""
        if self.agent and hasattr(self.agent, "do_llm_service_request"):
            messages = [
                {
                    "role": "system",
                    "content": "You are a product manager (PLM). Your task is to convert technical documentation into a clear, engaging blog post."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following {source_name} content into a well-structured blog post:\n\n{content}"
                }
            ]
            
            try:
                log.info("Sending content to LLM service for summarization")
                response = self.agent.do_llm_service_request(messages)
                summary = response.get("content", "")
                log.info("Successfully generated summary")
                return summary
            except Exception as e:
                error_message = f"Error calling LLM service: {str(e)}"
                log.error(error_message)
                return error_message
        else:
            return "Error: LLM service not available"
            
    def ensure_env_file(self):
        """Ensure the .env file exists for storing credentials"""
        dotenv_file = find_dotenv()
        if not dotenv_file:
            # Create .env file in the same directory as this script
            dotenv_dir = os.path.dirname(os.path.abspath(__file__))
            dotenv_file = os.path.join(dotenv_dir, ".env")
            
            # Create directory if it doesn't exist
            if not os.path.exists(dotenv_dir):
                os.makedirs(dotenv_dir)
                
            # Create empty .env file with header comment
            if not os.path.exists(dotenv_file):
                with open(dotenv_file, "w") as f:
                    f.write("# Atlassian API credentials (Confluence and Jira)\n")
                log.info("Created new .env file at %s", dotenv_file)
            
    def generate_slide_content(self, content, source_name):
        """Generate presentation slide content using the LLM service"""
        if self.agent and hasattr(self.agent, "do_llm_service_request"):
            messages = [
                {
                    "role": "system",
                    "content": """You are a professional presentation designer. Your task is to convert technical documentation
                    into clear, concise slide content suitable for a presentation. Create content for 5-7 slides that effectively
                    communicate the key points. Format your response as follows:

                    # Slide 1: Title Slide
                    [Title of the presentation]
                    [Subtitle or tagline]

                    # Slide 2: [Topic]
                    - Key point 1
                    - Key point 2
                    - Key point 3
                    
                    Speaker notes: [Additional context or talking points for the presenter]

                    # Slide 3: [Topic]
                    ...and so on.

                    Focus on clarity, brevity, and visual impact. Use bullet points for most content slides.
                    Include speaker notes with additional context that shouldn't appear on slides but would be helpful for the presenter.
                    """
                },
                {
                    "role": "user",
                    "content": f"Convert the following {source_name} content into presentation slide content:\n\n{content}"
                }
            ]
            
            try:
                log.info("Sending content to LLM service for slide content generation")
                response = self.agent.do_llm_service_request(messages)
                slide_content = response.get("content", "")
                log.info("Successfully generated slide content")
                return slide_content
            except Exception as e:
                error_message = f"Error calling LLM service for slide content: {str(e)}"
                log.error(error_message)
                return error_message
        else:
            return "Error: LLM service not available"
