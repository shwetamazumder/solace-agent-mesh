"""Simplified action to fetch Confluence pages and summarize them using LLM."""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

from solace_ai_connector.common.log import log
from solace_agent_mesh.common.action import Action
from solace_agent_mesh.common.action_response import ActionResponse

# Load environment variables
load_dotenv()

class PlmWritingAssistant(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "plm_writing_assistant",
                "description": "Fetches Confluence pages and summarizes them into blog posts.",
                "prompt_directive": (
                    "Provide a Confluence page URL to fetch its content and generate a summarized blog post."
                ),
                "params": [
                    {
                        "name": "confluence_url",
                        "desc": "URL of the Confluence page to summarize",
                        "type": "string",
                    }
                ],
                "required_scopes": ["plm_writing_assistant:generate_post:read"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        # Log environment variables
        log.info("Checking Atlassian credentials:")
        log.info("CONFLUENCE_BASE_URL: %s", os.getenv("CONFLUENCE_BASE_URL"))
        log.info("ATLASSIAN_EMAIL: %s", os.getenv("ATLASSIAN_EMAIL"))
        log.info("ATLASSIAN_API_TOKEN: %s", "Present" if os.getenv("ATLASSIAN_API_TOKEN") else "Missing")
        
        # Get the Confluence URL from parameters
        confluence_url = params.get("confluence_url")
        if not confluence_url:
            return ActionResponse(message="Error: No Confluence URL provided")
        
        # Fetch the Confluence page content
        log.info("Fetching Confluence page: %s", confluence_url)
        content = self.fetch_confluence_page(confluence_url)
        
        # If fetching failed, return the error message
        if content.startswith("⚠️"):
            return ActionResponse(message=content)
        
        # Generate a summary using the LLM service
        summary = self.summarize_content(content)
        
        return ActionResponse(message=summary)

    def fetch_confluence_page(self, url):
        """Fetch content from a Confluence page"""
        base_url = os.getenv("CONFLUENCE_BASE_URL")
        email = os.getenv("ATLASSIAN_EMAIL")
        token = os.getenv("ATLASSIAN_API_TOKEN")
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

    def summarize_content(self, content):
        """Summarize content using the LLM service"""
        if self.agent and hasattr(self.agent, "do_llm_service_request"):
            messages = [
                {
                    "role": "system",
                    "content": "You are a product marketing writer. Your task is to convert technical documentation into a clear, engaging blog post."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following Confluence page content into a well-structured blog post:\n\n{content}"
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
