import requests
import json

from .base import BaseRepoProvider
from .config import Config

class GitlabRepoProvider(BaseRepoProvider):
    provider_name = "gitlab"

    def __init__(self, config: Config):
        self.config = config
        self.api_url = "https://gitlab.com/api/v4"

    def _auth_header_for_token(self, token):
        """Get authentication headers for GitLab with token type detection."""
        if not token:
            return {"Content-Type": "application/json"}

        # Preserve GitLab's token detection logic
        if token.startswith('glpat-') or token.startswith('glpst-'):
            return {
                "Content-Type": "application/json",
                "PRIVATE-TOKEN": token
            }
        else:
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }

    def request(self, endpoint: str, params=None, method='GET', data=None, retry_on_auth=True):
        """
        Make a request to the GitLab API with automatic token refresh.

        Args:
            endpoint (str): The endpoint to request.
            params (dict): The parameters to pass to the request.
            method (str): The HTTP method to use.
            data (dict): The data to pass to the request.
            retry_on_auth (bool): Whether to retry once on auth failure with fresh token.
        """
        headers = self._auth_header_for_token(self.config.get_gitlab_token())
        url = f'{self.api_url}{endpoint}'
        response = requests.request(method, url, headers=headers, params=params, json=data)

        # Retry once on auth failure with fresh token
        if retry_on_auth and response.status_code in (401, 403):
            resolver = self.config.get_token_resolver()
            if resolver:
                fresh_token = resolver(self.provider_name)
                if fresh_token:
                    headers = self._auth_header_for_token(fresh_token)
                    response = requests.request(method, url, headers=headers, params=params, json=data)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            # if the response is json, print the error message
            print(f"Error with request to GitLab API: {err}")
            try:
                if response.json():
                    print(response.json())
            except json.JSONDecodeError:
                print(response.text)
            raise

        if (method == "DELETE"):
            return None

        return response.json()

    def _get_project_id(self, owner=None, repo=None):
        """
        Get GitLab project ID from owner/repo or parse from config.
        GitLab uses project IDs or URL-encoded paths in API calls.
        """
        if owner is None:
            owner = self.config.get_gitlab_repository_owner(raise_error_if_not_found=True)

        if repo is None:
            repo = self.config.get_gitlab_repository_name(raise_error_if_not_found=True)

        # Create URL-encoded project path
        project_path = f"{owner}/{repo}"
        # URL encode the path (replace / with %2F)
        return project_path.replace('/', '%2F')

    def get_gitlab_repository_owner(self, raise_error_if_not_found=False):
        """
        Get the GitLab repository owner (e.g. adbabble1)
        """
        # Try parsing from generic repo_url
        if self.config.repo_url:
            owner, _ = self.config.parse_owner_repo_from_url(self.config.repo_url)
            if owner:
                return owner

        if raise_error_if_not_found:
            raise ValueError("GitLab Repo class: 'owner' argument is required")
        return None

    def get_gitlab_repository_name(self, raise_error_if_not_found=False):
        """
        Get the GitLab repository name (e.g. adbabble)
        """
        # Try parsing from generic repo_url
        if self.config.repo_url:
            _, repo = self.config.parse_owner_repo_from_url(self.config.repo_url)
            if repo:
                return repo

        if raise_error_if_not_found:
            raise ValueError("GitLab Repo class: 'repo' argument is required")
        return None

    def update_pull_request(
        self,
        pull_request_number = None,
        title = None,
        body = None,
        assignees = None,
        labels = None,
        state = None,
        maintainer_can_modify = None,
        target_branch = None,
        owner = None,
        repo = None
    ):
        """
        Update a merge request in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/merge_requests.html#update-mr

        Args:
            pull_request_number (int): The number of the merge request to update. (required)
            title (str): The title of the merge request. (optional)
            body (str): The description of the merge request. (optional)
            state (str): The state of the merge request (close, reopen). (optional)
            target_branch (str): The target branch of the merge request. (optional)
            labels (list): List of label names to set. (optional)
            assignees (list): List of user IDs to assign. (optional)

        Raises:
            ValueError: If the pull_request_number is not provided.
        """

        if pull_request_number is None:
            raise ValueError("update_pull_request: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        payload = {}

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["description"] = body

        if assignees is not None:
            # GitLab uses assignee_ids for merge requests
            # You would need to convert usernames to IDs here
            # For simplicity, assuming assignees are already IDs
            payload["assignee_ids"] = assignees

        if labels is not None:
            # Join labels with comma for GitLab
            payload["labels"] = ','.join(labels) if isinstance(labels, list) else labels

        if state is not None:
            # GitLab uses state_event for state changes
            state_map = {
                'closed': 'close',
                'close': 'close',
                'open': 'reopen',
                'reopen': 'reopen'
            }
            if state.lower() in state_map:
                payload["state_event"] = state_map[state.lower()]

        if target_branch is not None:
            payload["target_branch"] = target_branch

        if maintainer_can_modify is not None:
            payload["allow_collaboration"] = maintainer_can_modify

        return self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}", method="PUT", data=payload)

    def update_issue(
            self,
            issue_number = None,
            title = None,
            body = None,
            assignees = None,
            labels = None,
            state = None,
            state_reason = None,
            milestone = None,
            owner = None,
            repo = None
    ):
        """
        Update an issue in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/issues.html#edit-an-issue

        Args:
            issue_number (int): The number of the issue to update. (required)
            title (str): The title of the issue. (optional)
            body (str): The description of the issue. (optional)
            assignees (list): A list of assignee IDs to assign to the issue. (optional)
            labels (list): A list of labels to add to the issue. (optional)
            state (str): The state of the issue (close, reopen). (optional)
            milestone (int): The ID of the milestone. (optional)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If the issue_number is not provided.
        """
        if issue_number is None:
            raise ValueError("update_issue: issue_number is required")

        project_id = self._get_project_id(owner, repo)

        payload = {}

        if assignees is not None:
            # GitLab uses assignee_ids for issues
            payload["assignee_ids"] = assignees

        if labels is not None:
            # Join labels with comma for GitLab
            payload["labels"] = ','.join(labels) if isinstance(labels, list) else labels

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["description"] = body

        if milestone is not None:
            payload["milestone_id"] = milestone

        if state is not None:
            # GitLab uses state_event for state changes
            state_map = {
                'closed': 'close',
                'close': 'close',
                'open': 'reopen',
                'reopen': 'reopen'
            }
            if state.lower() in state_map:
                payload["state_event"] = state_map[state.lower()]

        return self.request(f"/projects/{project_id}/issues/{issue_number}", method="PUT", data=payload)

    def create_issue(
            self,
            title = None,
            body = None,
            milestone = None,
            assignees = None,
            labels = None,
            owner = None,
            repo = None
    ):
        """
        Create an issue in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/issues.html#new-issue

        Args:
            title (str): The title of the issue. (required)
            body (str): The description of the issue. (optional)
            assignees (list): A list of assignee IDs to assign to the issue. (optional)
            labels (list): A list of labels to add to the issue. (optional)
            milestone (int): The ID of the milestone. (optional)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If the title is not provided.
        """
        if title is None:
            raise ValueError("create_issue: title is required")

        project_id = self._get_project_id(owner, repo)

        payload = {
            "title": title,
        }

        if body is not None:
            payload["description"] = body

        if assignees is not None:
            # GitLab uses assignee_ids for issues
            payload["assignee_ids"] = assignees

        if labels is not None:
            # Join labels with comma for GitLab
            payload["labels"] = ','.join(labels) if isinstance(labels, list) else labels

        if milestone is not None:
            payload["milestone_id"] = milestone

        return self.request(f"/projects/{project_id}/issues", method="POST", data=payload)

    def create_pull_request(
            self,
            source_branch = None,
            target_branch = None,
            title = None,
            body = None,
            draft = False,
            issue_number = None,
            owner = None,
            repo = None
    ):
        """
        Create a merge request in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/merge_requests.html#create-mr

        Args:
            source_branch (str): The source branch to create the merge request from. (required)
            target_branch (str): The target branch to create the merge request to. (required)
            title (str): The title of the merge request. (required)
            body (str): The description of the merge request. (optional)
            draft (bool): Whether the merge request is a draft. (optional) [default: False]
            issue_number (int): The issue IID to close when the MR is merged. (optional)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """
        if source_branch is None:
            raise ValueError("create_pull_request: source_branch is required")

        if target_branch is None:
            raise ValueError("create_pull_request: target_branch is required")

        if title is None:
            raise ValueError("create_pull_request: title is required")

        project_id = self._get_project_id(owner, repo)

        payload = {
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
        }

        # In GitLab, drafts are marked with "Draft:" prefix in title
        if draft:
            if not title.startswith("Draft:") and not title.startswith("WIP:"):
                payload["title"] = f"Draft: {title}"

        if body is not None:
            payload["description"] = body

        if issue_number is not None:
            # GitLab can close issues when MR is merged
            if body:
                payload["description"] = f"{body}\\n\\nCloses #{issue_number}"
            else:
                payload["description"] = f"Closes #{issue_number}"

        response = self.request(f"/projects/{project_id}/merge_requests", method="POST", data=payload)
        # Normalize response to match GitHub structure
        if response and "web_url" in response:
            response["html_url"] = response["web_url"]
        return response

    def delete_pull_request_comment(
            self,
            comment_id = None,
            owner = None,
            repo = None
    ):
        """
        Delete a merge request note (comment) in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#delete-a-merge-request-note

        Args:
            comment_id (int): The ID of the note to delete. (required)

        Raises:
            ValueError: If the comment_id is not provided.
        """
        if comment_id is None:
            raise ValueError("delete_pull_request_comment: comment_id is required")

        project_id = self._get_project_id(owner, repo)

        # Note: This requires knowing the MR IID, which we don't have here
        # For a complete implementation, you'd need to track MR IID with comment
        # or make an additional API call to find it
        # This is a limitation of the current interface
        raise NotImplementedError("GitLab delete_pull_request_comment requires MR IID tracking")

    def update_pull_request_comment(
            self,
            comment_id = None,
            body = None,
            owner = None,
            repo = None
    ):
        """
        Update a merge request note (comment) in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#modify-existing-merge-request-note

        Args:
            comment_id (int): The ID of the note to update. (required)
            body (str): The body of the note. (required)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """
        if comment_id is None:
            raise ValueError("update_pull_request_comment: comment_id is required")

        if body is None:
            raise ValueError("update_pull_request_comment: body is required")

        project_id = self._get_project_id(owner, repo)

        # Note: This requires knowing the MR IID, which we don't have here
        # For a complete implementation, you'd need to track MR IID with comment
        # or make an additional API call to find it
        # This is a limitation of the current interface
        raise NotImplementedError("GitLab update_pull_request_comment requires MR IID tracking")

    def comment_on_pull_request(
            self,
            pull_request_number = None,
            body = None,
            owner = None,
            repo = None
    ):
        """
        Comment on a merge request in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#create-new-merge-request-note

        Args:
            pull_request_number (int): The IID of the merge request to comment on. (required)
            body (str): The body of the comment. (required)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """

        if body is None:
            raise ValueError("comment_on_pull_request: body is required")

        if pull_request_number is None:
            raise ValueError("comment_on_pull_request: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        payload = {
            "body": body,
        }

        return self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}/notes", method="POST", data=payload)

    def comment_on_pull_request_file(
            self,
            commit_id = None,
            file_path = None,
            pull_request_number = None,
            body = None,
            line = None,
            side = "RIGHT",
            reply_to_id = None,
            subject_type = "file",
            owner = None,
            repo = None
    ):
        """
        Comment on a file in a merge request in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/discussions.html#create-new-merge-request-thread
        - https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr

        Args:
            commit_id (str): The SHA of the commit to comment on. (required)
            file_path (str): The path of the file to comment on. (required)
            pull_request_number (int): The IID of the merge request to comment on. (required)
            body (str): The body of the comment. (required)
            line (int): The line number to comment on. (optional)
            side (str): The side of the diff to comment on. (optional) [LEFT, RIGHT] (default: "RIGHT")
            reply_to_id (int): The ID of the discussion to reply to. (optional)
            subject_type (str): The type of subject to comment on. (optional) ["line", "file"] (default: "file")
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """
        if body is None:
            raise ValueError("comment_on_pull_request_file: body is required")

        if file_path is None:
            raise ValueError("comment_on_pull_request_file: file_path is required")

        if pull_request_number is None:
            raise ValueError("comment_on_pull_request_file: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        # Always fetch the actual diff refs from the merge request
        # GitLab requires the proper base_sha, start_sha, and head_sha from the MR's diff_refs
        # for line-specific comments to work correctly
        mr_details = self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}", method="GET")
        base_sha = mr_details.get("diff_refs", {}).get("base_sha")
        start_sha = mr_details.get("diff_refs", {}).get("start_sha")
        head_sha = mr_details.get("diff_refs", {}).get("head_sha")

        if not all([base_sha, start_sha, head_sha]):
            raise ValueError("Failed to fetch merge request diff references")

        # Note: commit_id parameter can be used for validation if needed,
        # but should not be used to construct the position object

        # If replying to an existing discussion
        if reply_to_id is not None:
            # For replies, use the notes endpoint instead
            return self.request(
                f"/projects/{project_id}/merge_requests/{pull_request_number}/discussions/{reply_to_id}/notes",
                method="POST",
                data={"body": body}
            )

        # For file-level comments (no specific line)
        if subject_type == "file" or line is None:
            # Create a simple note on the merge request instead of a discussion
            # GitLab's discussion API requires line-specific information for file comments
            return self.request(
                f"/projects/{project_id}/merge_requests/{pull_request_number}/notes",
                method="POST",
                data={"body": f"**File:** `{file_path}`\n\n{body}"}
            )

        # For line-specific comments
        # GitLab uses a different approach with discussions
        # Create a new discussion thread on the merge request diff
        payload = {
            "body": body,
            "position": {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": file_path,
                "old_path": file_path,
            }
        }

        # Add line information for line-specific comments
        if line is not None:
            # Generate line_code (required for GitLab discussions)
            # Format: <SHA>_<old_line>_<new_line>
            if side == "RIGHT":
                payload["position"]["new_line"] = line
                line_code = f"{head_sha}_{line}_{line}"
            else:
                payload["position"]["old_line"] = line
                line_code = f"{head_sha}_{line}_"

            payload["position"]["line_code"] = line_code

        return self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}/discussions", method="POST", data=payload)

    def comment_on_pull_request_lines(
            self,
            commit_id = None,
            file_path = None,
            pull_request_number = None,
            body = None,
            start_line = None,
            end_line = None,
            side = "RIGHT",
            owner = None,
            repo = None
    ):
        """
        Comment on a range of lines in a merge request file.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/discussions.html#create-new-merge-request-thread
        - https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr

        Args:
            commit_id (str): The SHA of the commit to comment on. (required)
            file_path (str): The path of the file to comment on. (required)
            pull_request_number (int): The IID of the merge request to comment on. (required)
            body (str): The body of the comment. (required)
            start_line (int): The starting line number to comment on. (required)
            end_line (int): The ending line number to comment on. (optional)
            side (str): The side of the diff to comment on. (optional) [LEFT, RIGHT] (default: "RIGHT")
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """
        if start_line is None:
            raise ValueError("comment_on_pull_request_lines: start_line is required")

        if body is None:
            raise ValueError("comment_on_pull_request_lines: body is required")

        if file_path is None:
            raise ValueError("comment_on_pull_request_lines: file_path is required")

        if pull_request_number is None:
            raise ValueError("comment_on_pull_request_lines: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        # Fetch the actual diff refs from the merge request
        # GitLab needs the proper base_sha, start_sha, and head_sha from the MR's diff_refs
        mr_details = self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}", method="GET")
        base_sha = mr_details.get("diff_refs", {}).get("base_sha")
        start_sha = mr_details.get("diff_refs", {}).get("start_sha")
        head_sha = mr_details.get("diff_refs", {}).get("head_sha")

        if not all([base_sha, start_sha, head_sha]):
            raise ValueError("Failed to fetch merge request diff references")

        # GitLab uses discussions for line comments
        payload = {
            "body": body,
            "position": {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": file_path,
                "old_path": file_path,
            }
        }

        # Handle line ranges
        # For multi-line comments, include line range in the body
        if end_line and end_line != start_line:
            payload["body"] = f"{body}\n\n*(Lines {start_line}-{end_line})*"

        # Add line information based on the side of the diff
        if side == "RIGHT":
            payload["position"]["new_line"] = start_line
        else:
            payload["position"]["old_line"] = start_line

        return self.request(f"/projects/{project_id}/merge_requests/{pull_request_number}/discussions", method="POST", data=payload)

    def update_issue_comment(
            self,
            comment_id = None,
            body = None,
            owner = None,
            repo = None
    ):
        """
        Update an issue note (comment) in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#modify-existing-issue-note

        Args:
            comment_id (int): The ID of the note to update. (required)
            body (str): The body of the note. (required)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """
        if comment_id is None:
            raise ValueError("update_issue_comment: comment_id is required")

        if body is None:
            raise ValueError("update_issue_comment: body is required")

        project_id = self._get_project_id(owner, repo)

        # Note: This requires knowing the issue IID, which we don't have here
        # For a complete implementation, you'd need to track issue IID with comment
        # or make an additional API call to find it
        # This is a limitation of the current interface
        raise NotImplementedError("GitLab update_issue_comment requires issue IID tracking")

    def delete_issue_comment(
            self,
            comment_id = None,
            owner = None,
            repo = None
    ):
        """
        Delete an issue note (comment) in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#delete-an-issue-note

        Args:
            comment_id (int): The ID of the note to delete. (required)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If the comment_id is not provided.
        """

        if comment_id is None:
            raise ValueError("delete_issue_comment: comment_id is required")

        project_id = self._get_project_id(owner, repo)

        # Note: This requires knowing the issue IID, which we don't have here
        # For a complete implementation, you'd need to track issue IID with comment
        # or make an additional API call to find it
        # This is a limitation of the current interface
        raise NotImplementedError("GitLab delete_issue_comment requires issue IID tracking")

    def comment_on_issue(
            self,
            issue_number = None,
            body = None,
            owner = None,
            repo = None
    ):
        """
        Comment on an issue in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/notes.html#create-new-issue-note

        Args:
            issue_number (int): The IID of the issue to comment on. (required)
            body (str): The body of the comment. (required)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """

        if body is None:
            raise ValueError("comment_on_issue: body is required")

        if issue_number is None:
            raise ValueError("comment_on_issue: issue_number is required")

        project_id = self._get_project_id(owner, repo)

        payload = {
            "body": body,
        }

        return self.request(f"/projects/{project_id}/issues/{issue_number}/notes", method="POST", data=payload)

    def reply_to_pull_request_comment(
            self,
            reply_to_id = None,
            pull_request_number = None,
            body = None,
            owner = None,
            repo = None
    ):
        """
        Reply to a merge request discussion in GitLab.

        Uses the following endpoints:
        - https://docs.gitlab.com/ee/api/discussions.html#add-note-to-existing-merge-request-discussion

        Args:
            reply_to_id (str): The ID of the discussion to reply to. (required)
            pull_request_number (int): The IID of the merge request. (required)
            body (str): The body of the reply. (required)
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """

        if body is None:
            raise ValueError("reply_to_pull_request_comment: body is required")

        if reply_to_id is None:
            raise ValueError("reply_to_pull_request_comment: reply_to_id is required")

        if pull_request_number is None:
            raise ValueError("reply_to_pull_request_comment: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        payload = {
            "body": body,
        }

        return self.request(
            f"/projects/{project_id}/merge_requests/{pull_request_number}/discussions/{reply_to_id}/notes",
            method="POST",
            data=payload
        )

    def review_pull_request(
            self,
            pull_request_number = None,
            body = None,
            commit_id = None,
            comments = None,
            event = "COMMENT",
            owner = None,
            repo = None
    ):
        """
        Review a merge request in GitLab.

        Note: GitLab doesn't have the same review concept as GitHub.
        We'll simulate it by creating a discussion or approving the MR.

        Args:
            pull_request_number (int): The IID of the merge request to review. (required)
            body (str): The body of the review. (optional)
            commit_id (str): The SHA of the commit to review. (optional)
            comments (list): A list of comments to add to the review. (optional)
            event (str): The event to trigger on the review. (optional) [COMMENT, APPROVE]
            owner (str): The owner of the repository. (optional)
            repo (str): The name of the repository. (optional)

        Raises:
            ValueError: If any of the required arguments are not provided.
        """

        if body is None and comments is None:
            raise ValueError("review_pull_request: body or comments is required")

        if pull_request_number is None:
            raise ValueError("review_pull_request: pull_request_number is required")

        project_id = self._get_project_id(owner, repo)

        # GitLab doesn't have a direct equivalent to GitHub's review API
        # We can simulate it with approvals and comments

        if event == "APPROVE":
            # Approve the merge request
            approval_response = self.request(
                f"/projects/{project_id}/merge_requests/{pull_request_number}/approve",
                method="POST"
            )

            # Also add the review body as a comment if provided
            if body:
                self.comment_on_pull_request(pull_request_number, body, owner, repo)

            return approval_response

        elif event == "COMMENT" or event == "REQUEST_CHANGES":
            # Add review body as a comment
            if body:
                return self.comment_on_pull_request(pull_request_number, body, owner, repo)

            # Add individual comments if provided
            if comments:
                responses = []
                for comment in comments:
                    if 'path' in comment and 'line' in comment:
                        # File/line comment
                        response = self.comment_on_pull_request_file(
                            commit_id=commit_id or comment.get('commit_id'),
                            file_path=comment['path'],
                            pull_request_number=pull_request_number,
                            body=comment.get('body', ''),
                            line=comment['line'],
                            side=comment.get('side', 'RIGHT'),
                            owner=owner,
                            repo=repo
                        )
                        responses.append(response)
                    else:
                        # General comment
                        response = self.comment_on_pull_request(
                            pull_request_number=pull_request_number,
                            body=comment.get('body', ''),
                            owner=owner,
                            repo=repo
                        )
                        responses.append(response)
                return responses

        else:
            raise ValueError(f"review_pull_request: unsupported event type '{event}'")