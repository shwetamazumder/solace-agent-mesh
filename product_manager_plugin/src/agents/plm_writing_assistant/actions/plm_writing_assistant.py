"""Simplified action to fetch Confluence pages, Jira issues, or GitHub files and summarize them using LLM."""

import os
import re
import requests
import getpass
import base64
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
                "description": "Fetches Confluence pages, Jira issues, or GitHub files and summarizes them into blog posts or slide content.",
                "prompt_directive": (
                    "Provide a Confluence page URL, Jira issue key/URL, or GitHub file URL to fetch its content and generate a summarized blog post or slide content."
                ),
                "params": [
                    {
                        "name": "confluence_url",
                        "desc": "URL of the Confluence page to summarize (provide one of confluence_url, jira_issue, or github_url)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "jira_issue",
                        "desc": "Jira issue key (e.g., 'PROJECT-123') or URL to summarize (provide one of confluence_url, jira_issue, or github_url)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "github_url",
                        "desc": "URL of GitHub file to summarize (provide one of confluence_url, jira_issue, or github_url)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "output_type",
                        "desc": "Type of output to generate (blog_post, slide_content, or release_notifications)",
                        "type": "string",
                        "default": "blog_post",
                        "required": False,
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
                    },
                    {
                        "name": "github_token",
                        "desc": "GitHub Personal Access Token (optional, uses environment variable if not provided)",
                        "type": "string",
                        "required": False,
                    },
                    {
                        "name": "github_content",
                        "desc": "Type of content to fetch from GitHub repository (readme, files, commits, issues, releases, all)",
                        "type": "string",
                        "default": "readme",
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
        github_url = params.get("github_url")
        github_content = params.get("github_content")  # Default is set in parameter definition
        output_type = params.get("output_type")  # Default is set in parameter definition
        
        # Check if at least one source URL is provided
        if not confluence_url and not jira_issue and not github_url:
            return ActionResponse(message="Error: Please provide either a Confluence URL, Jira issue key/URL, or GitHub file URL")
        
        # Determine which source we're using (prioritize in order: Confluence, Jira, GitHub)
        using_confluence = confluence_url is not None
        using_jira = jira_issue is not None and not using_confluence
        using_github = github_url is not None and not using_confluence and not using_jira
        
        if sum([using_confluence, using_jira, using_github]) > 1:
            log.info("Multiple sources provided, prioritizing Confluence > Jira > GitHub")
        
        # Get credentials (from params or environment or prompt)
        confluence_base_url = params.get("confluence_base_url") or os.getenv("CONFLUENCE_BASE_URL")
        jira_base_url = params.get("jira_base_url") or os.getenv("JIRA_BASE_URL")
        atlassian_email = params.get("atlassian_email") or os.getenv("ATLASSIAN_EMAIL")
        atlassian_api_token = params.get("atlassian_api_token") or os.getenv("ATLASSIAN_API_TOKEN")
        github_token = params.get("github_token") or os.getenv("GITHUB_TOKEN")
        
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
        
        if using_github:
            # Always prompt for GitHub token to avoid rate limiting and access issues
            if not github_token:
                print("\n" + "="*80)
                print("GitHub Access Token Configuration")
                print("="*80)
                print("No GitHub token found in environment variables or parameters.")
                print("A GitHub token is recommended to avoid rate limiting and access private repositories.")
                print("You can generate a token at: https://github.com/settings/tokens")
                print("1. Go to https://github.com/settings/tokens")
                print("2. Click 'Generate new token'")
                print("3. Give it a name and select 'repo' scope for private repos or 'public_repo' for public repos")
                print("4. Copy the generated token")
                print("-"*80)
                github_token = getpass.getpass("Please enter your GitHub token (input will be hidden, press Enter to skip): ")
                if github_token:
                    set_key(dotenv_file, "GITHUB_TOKEN", github_token)
                    os.environ["GITHUB_TOKEN"] = github_token
                    print("✓ GitHub token saved to environment variables.")
                else:
                    print("⚠️ No token provided. Proceeding without authentication (may fail for private repos or due to rate limits).")
            else:
                print("✓ Using GitHub token from environment variables or parameters.")
        
        # Check if all required credentials are provided after prompting
        missing_credentials = []
        if using_confluence and not confluence_base_url:
            missing_credentials.append("Confluence base URL")
        if using_jira and not jira_base_url:
            missing_credentials.append("Jira base URL")
        if (using_confluence or using_jira) and not atlassian_email:
            missing_credentials.append("Atlassian email")
        if (using_confluence or using_jira) and not atlassian_api_token:
            missing_credentials.append("Atlassian API token")
        # GitHub token handling is done in the fetch_github_content method
            
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
            
        elif using_github:
            # Log credentials (not the token)
            log.info("Using GitHub credentials:")
            log.info("GITHUB_TOKEN: %s", "Present" if github_token else "Missing")
            
            # Fetch the GitHub content
            log.info(f"Fetching GitHub content ({github_content}): {github_url}")
            content = self.fetch_github_content(github_url, github_token, github_content)
            source_name = "GitHub content"
        
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
        elif output_type == "release_notifications":
            result = self.generate_release_notifications(content, source_name)
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
    
    def prompt_for_github_token(self, dotenv_file):
        """Prompt user for GitHub token when needed"""
        print("\n" + "="*80)
        print("GitHub Access Token Required")
        print("="*80)
        print("This appears to be a private repository or you've hit a rate limit.")
        print("You need a GitHub token to access this content.")
        print("You can generate a token at: https://github.com/settings/tokens")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Click 'Generate new token'")
        print("3. Give it a name and select 'repo' scope for private repos")
        print("4. Copy the generated token")
        print("-"*80)
        github_token = getpass.getpass("Please enter your GitHub token (input will be hidden): ")
        if github_token:
            set_key(dotenv_file, "GITHUB_TOKEN", github_token)
            os.environ["GITHUB_TOKEN"] = github_token
            print("✓ GitHub token saved to environment variables.")
            return github_token
        else:
            print("⚠️ No token provided. Cannot access private repository.")
            return None
    
    def fetch_github_content(self, url, token=None, content_type="readme"):
        """
        Fetch content from GitHub URLs - repositories, releases, or files
        
        content_type options:
        - readme: Repository README (default)
        - files: List of files in the repository
        - commits: Recent commits
        - issues: Open issues
        - releases: Release information
        - all: Comprehensive repository information
        """
        try:
            # Extract the organization and repository name
            if 'github.com/' not in url:
                return f"⚠️ Invalid GitHub URL format: {url}"
                
            parts = url.split('github.com/')[1].split('/')
            if len(parts) < 2:
                return f"⚠️ Invalid GitHub URL format: {url}"
                
            org_repo = '/'.join(parts[:2])
            headers = {"Authorization": f"token {token}"} if token else {}
            log.info(f"Processing GitHub URL for repository: {org_repo}")
            
            # Case 1: Release page URL
            if '/releases/tag/' in url:
                tag = url.split('/releases/tag/')[1]
                log.info(f"Detected release page URL for tag: {tag}")
                
                # Fetch release information
                api_url = f"https://api.github.com/repos/{org_repo}/releases/tags/{tag}"
                log.info("Making GitHub API request to: %s", api_url)
                
                # First attempt - with existing token if any
                resp = requests.get(api_url, headers=headers)
                
                # If we get a 404 or 403, it might be a private repo requiring auth
                if not resp.ok and resp.status_code in [403, 404]:
                    log.info(f"Release access failed with status {resp.status_code}. This may be a private repository.")
                    
                    # Only prompt for token if we don't already have one
                    if not token:
                        dotenv_file = find_dotenv()
                        if not dotenv_file:
                            dotenv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
                        
                        # Prompt for token
                        token = self.prompt_for_github_token(dotenv_file)
                        
                        # Retry with token if provided
                        if token:
                            headers = {"Authorization": f"token {token}"}
                            log.info("Retrying with authentication token")
                            resp = requests.get(api_url, headers=headers)
                
                if resp.ok:
                    release_data = resp.json()
                    name = release_data.get("name", tag)
                    body = release_data.get("body", "")
                    published_at = release_data.get("published_at", "")
                    author = release_data.get("author", {}).get("login", "Unknown")
                    
                    # Format the content
                    content = f"# Release: {name}\n\n"
                    content += f"**Repository:** {org_repo}\n"
                    content += f"**Tag:** {tag}\n"
                    content += f"**Published:** {published_at}\n"
                    content += f"**Author:** {author}\n\n"
                    content += f"## Release Notes\n\n{body}\n\n"
                    
                    # Add assets information if available
                    assets = release_data.get("assets", [])
                    if assets:
                        content += "## Assets\n\n"
                        for asset in assets:
                            asset_name = asset.get("name", "")
                            download_count = asset.get("download_count", 0)
                            content += f"- {asset_name} (Downloads: {download_count})\n"
                    
                    log.info(f"Successfully fetched GitHub release: {tag}")
                    return content
                else:
                    error_message = f"⚠️ Failed to fetch GitHub release: Status {resp.status_code}"
                    log.error("%s\nResponse: %s", error_message, resp.text[:500])
                    return error_message
                    
            # Case 2: File URL
            elif '/blob/' in url:
                # Find the path after 'blob/branch/'
                path_start = url.find('blob/')
                if path_start == -1:
                    return f"⚠️ Could not find file path in GitHub URL: {url}"
                    
                path_start = url.find('/', path_start + 5)  # Skip 'blob/branch'
                if path_start == -1:
                    return f"⚠️ Could not find file path in GitHub URL: {url}"
                    
                file_path = url[path_start+1:]
                
                # Make API request
                api_url = f"https://api.github.com/repos/{org_repo}/contents/{file_path}"
                
                log.info("Making GitHub API request to: %s", api_url)
                # First attempt - with existing token if any
                resp = requests.get(api_url, headers=headers)
                
                # If we get a 404 or 403, it might be a private repo requiring auth
                if not resp.ok and resp.status_code in [403, 404]:
                    log.info(f"File access failed with status {resp.status_code}. This may be a private repository.")
                    
                    # Only prompt for token if we don't already have one
                    if not token:
                        dotenv_file = find_dotenv()
                        if not dotenv_file:
                            dotenv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
                        
                        # Prompt for token
                        token = self.prompt_for_github_token(dotenv_file)
                        
                        # Retry with token if provided
                        if token:
                            headers = {"Authorization": f"token {token}"}
                            log.info("Retrying with authentication token")
                            resp = requests.get(api_url, headers=headers)
                
                if resp.ok:
                    content_data = resp.json()
                    if content_data.get("type") == "file":
                        # Content is base64 encoded
                        content = base64.b64decode(content_data["content"]).decode("utf-8")
                        file_name = content_data.get("name", "")
                        log.info("Successfully fetched GitHub file: %s", file_name)
                        return f"# GitHub: {org_repo}/{file_name}\n\n{content}"
                    else:
                        error_message = f"⚠️ Path is not a file: {file_path}"
                        log.error(error_message)
                        return error_message
                else:
                    error_message = f"⚠️ Failed to fetch GitHub file: Status {resp.status_code}"
                    log.error("%s\nResponse: %s", error_message, resp.text[:500])
                    return error_message
            
            # Case 3: Repository URL
            else:
                # Fetch repository information
                repo_api_url = f"https://api.github.com/repos/{org_repo}"
                log.info("Making GitHub API request to: %s", repo_api_url)
                
                # First attempt - with existing token if any
                repo_resp = requests.get(repo_api_url, headers=headers)
                
                # If we get a 404 or 403, it might be a private repo requiring auth
                if not repo_resp.ok and repo_resp.status_code in [403, 404]:
                    log.info(f"Repository access failed with status {repo_resp.status_code}. This may be a private repository.")
                    
                    # Only prompt for token if we don't already have one
                    if not token:
                        dotenv_file = find_dotenv()
                        if not dotenv_file:
                            dotenv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
                        
                        # Prompt for token
                        token = self.prompt_for_github_token(dotenv_file)
                        
                        # Retry with token if provided
                        if token:
                            headers = {"Authorization": f"token {token}"}
                            log.info("Retrying with authentication token")
                            repo_resp = requests.get(repo_api_url, headers=headers)
                
                # Final check if request succeeded
                if not repo_resp.ok:
                    status_code = repo_resp.status_code
                    if status_code == 404:
                        error_message = (
                            f"⚠️ Repository not found: {org_repo} (Status 404)\n\n"
                            f"This could be due to:\n"
                            f"1. The repository doesn't exist or has been renamed\n"
                            f"2. The repository is private and requires authentication\n"
                            f"3. You don't have access to this repository\n\n"
                            f"Please verify the repository URL and try again with a valid GitHub token."
                        )
                    elif status_code == 403:
                        error_message = (
                            f"⚠️ Access forbidden to repository: {org_repo} (Status 403)\n\n"
                            f"This is likely due to GitHub API rate limiting. Please provide a GitHub token to increase your rate limit."
                        )
                    else:
                        error_message = f"⚠️ Failed to fetch GitHub repository: Status {status_code}"
                    
                    log.error("%s\nResponse: %s", error_message, repo_resp.text[:500])
                    return error_message
                
                repo_data = repo_resp.json()
                
                # Basic repository information
                name = repo_data.get("name", "")
                description = repo_data.get("description", "")
                stars = repo_data.get("stargazers_count", 0)
                forks = repo_data.get("forks_count", 0)
                language = repo_data.get("language", "")
                owner = repo_data.get("owner", {}).get("login", "")
                
                # Start building the content with repo info
                content = f"# Repository: {name}\n\n"
                content += f"**Owner:** {owner}\n"
                content += f"**Description:** {description}\n"
                content += f"**Primary Language:** {language}\n"
                content += f"**Stars:** {stars}\n"
                content += f"**Forks:** {forks}\n\n"
                
                # Fetch different types of content based on content_type
                if content_type == "readme" or content_type == "all":
                    # Fetch README content
                    readme_api_url = f"https://api.github.com/repos/{org_repo}/readme"
                    log.info("Fetching README from: %s", readme_api_url)
                    
                    readme_resp = requests.get(readme_api_url, headers=headers)
                    if readme_resp.ok:
                        readme_data = readme_resp.json()
                        if "content" in readme_data:
                            readme_content = base64.b64decode(readme_data["content"]).decode("utf-8")
                            log.info("Successfully fetched README")
                            content += "## README\n\n"
                            content += readme_content + "\n\n"
                
                if content_type == "files" or content_type == "all":
                    # Fetch repository contents (files and directories)
                    contents_api_url = f"https://api.github.com/repos/{org_repo}/contents"
                    log.info("Fetching repository contents from: %s", contents_api_url)
                    
                    contents_resp = requests.get(contents_api_url, headers=headers)
                    if contents_resp.ok:
                        contents_data = contents_resp.json()
                        content += "## Repository Contents\n\n"
                        
                        for item in contents_data:
                            item_type = item.get("type", "")
                            item_name = item.get("name", "")
                            item_path = item.get("path", "")
                            
                            if item_type == "dir":
                                content += f"📁 **{item_name}/** (Directory)\n"
                            elif item_type == "file":
                                content += f"📄 **{item_name}**\n"
                        
                        log.info("Successfully fetched repository contents")
                
                if content_type == "commits" or content_type == "all":
                    # Fetch recent commits
                    commits_api_url = f"https://api.github.com/repos/{org_repo}/commits"
                    log.info("Fetching recent commits from: %s", commits_api_url)
                    
                    commits_resp = requests.get(commits_api_url, headers=headers, params={"per_page": 10})
                    if commits_resp.ok:
                        commits_data = commits_resp.json()
                        content += "## Recent Commits\n\n"
                        
                        for commit in commits_data:
                            commit_sha = commit.get("sha", "")[:7]  # Short SHA
                            commit_msg = commit.get("commit", {}).get("message", "").split("\n")[0]  # First line only
                            author_name = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                            commit_date = commit.get("commit", {}).get("author", {}).get("date", "")
                            
                            content += f"- **{commit_sha}** ({author_name}, {commit_date}): {commit_msg}\n"
                        
                        log.info("Successfully fetched recent commits")
                
                if content_type == "issues" or content_type == "all":
                    # Fetch open issues
                    issues_api_url = f"https://api.github.com/repos/{org_repo}/issues"
                    log.info("Fetching open issues from: %s", issues_api_url)
                    
                    issues_resp = requests.get(issues_api_url, headers=headers, params={"state": "open", "per_page": 10})
                    if issues_resp.ok:
                        issues_data = issues_resp.json()
                        content += "## Open Issues\n\n"
                        
                        for issue in issues_data:
                            # Skip pull requests (they're also returned by the issues API)
                            if "pull_request" in issue:
                                continue
                                
                            issue_number = issue.get("number", "")
                            issue_title = issue.get("title", "")
                            issue_user = issue.get("user", {}).get("login", "Unknown")
                            issue_date = issue.get("created_at", "")
                            
                            content += f"- **#{issue_number}** ({issue_user}, {issue_date}): {issue_title}\n"
                        
                        log.info("Successfully fetched open issues")
                
                if content_type == "releases" or content_type == "all":
                    # Fetch releases
                    releases_api_url = f"https://api.github.com/repos/{org_repo}/releases"
                    log.info("Fetching releases from: %s", releases_api_url)
                    
                    releases_resp = requests.get(releases_api_url, headers=headers, params={"per_page": 5})
                    if releases_resp.ok:
                        releases_data = releases_resp.json()
                        content += "## Recent Releases\n\n"
                        
                        for release in releases_data:
                            release_name = release.get("name", "")
                            release_tag = release.get("tag_name", "")
                            release_date = release.get("published_at", "")
                            
                            content += f"- **{release_name}** (Tag: {release_tag}, Date: {release_date})\n"
                        
                        log.info("Successfully fetched releases")
                
                log.info(f"Successfully fetched GitHub repository content: {org_repo}")
                return content
                
        except Exception as e:
            error_message = f"⚠️ Error fetching GitHub content: {str(e)}"
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
                    f.write("# API credentials (Confluence, Jira, and GitHub)\n")
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
            
    def generate_release_notifications(self, content, source_name):
        """Generate release notifications using the LLM service"""
        if self.agent and hasattr(self.agent, "do_llm_service_request"):
            messages = [
                {
                    "role": "system",
                    "content": """You are a product manager responsible for communicating software releases to stakeholders.
                    Your task is to convert technical release notes into clear, well-structured release notifications
                    for different audiences. Create the following notifications:
                    
                    1. Customer-facing Release Announcement
                       - Highlight benefits and new features in customer-friendly language
                       - Avoid technical jargon
                       - Focus on value proposition
                       
                    2. Internal Team Notification
                       - Include technical details relevant for internal teams
                       - Highlight changes that affect different departments
                       - Include deployment notes if available
                       
                    3. Executive Summary
                       - Brief overview for executives (1-2 paragraphs)
                       - Focus on business impact and strategic value
                       - Include any notable metrics or KPIs
                       
                    Format each section with clear headings and concise content.
                    """
                },
                {
                    "role": "user",
                    "content": f"Generate release notifications for the following {source_name}:\n\n{content}"
                }
            ]
            
            try:
                log.info("Sending content to LLM service for release notification generation")
                response = self.agent.do_llm_service_request(messages)
                notifications = response.get("content", "")
                log.info("Successfully generated release notifications")
                return notifications
            except Exception as e:
                error_message = f"Error calling LLM service for release notifications: {str(e)}"
                log.error(error_message)
                return error_message
        else:
            return "Error: LLM service not available"
