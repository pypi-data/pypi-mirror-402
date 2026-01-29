#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["aiohttp", "pydantic", "pyyaml", "rich"]
# ///

# ruff: noqa: B019 `functools.lru_cache` on methods can lead to memory leaks
# ruff: noqa: D411 doc
# ruff: noqa: D417 doc

import asyncio
import base64
import json
import logging
import netrc
from collections.abc import AsyncIterable, Iterable, Mapping, MutableMapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import quote, urljoin, urlparse

# from aiohttp.http_exceptions import HttpBadRequest
import aiohttp
from aiohttp import ClientResponse
from pydantic import BaseModel, ConfigDict, Field, Json
from rich import print


def log() -> logging.Logger:
    """Returns the logger instance to use here"""
    return logging.getLogger("trickkiste.gerrit")


class GerritBase(BaseModel):
    # model_config = ConfigDict(extra="ignore")
    model_config = ConfigDict(extra="forbid")


class GerritAccountAvatar(GerritBase):
    url: str
    height: int


class GerritAccount(GerritBase):
    account_id: int = Field(..., alias="_account_id")
    name: str
    username: str
    avatars: list[GerritAccountAvatar]
    email: None | str = None
    display_name: None | str = None


class GerritReviewer(GerritAccount):
    approvals: dict[str, str]  #': {'Code-Review': ' 0', 'Verified': ' 0'},
    tags: None | list[Literal["SERVICE_USER"]] = None
    status: None | str = None  # "Developer"


class GerritUser(GerritBase):
    account_id: int = Field(..., alias="_account_id")


class GerritAttentionSet(GerritBase):
    account: GerritUser
    last_update: datetime
    reason: str
    reason_account: None | GerritUser = None


class GerritSubmitRecordLabel(GerritBase):
    label: str
    status: str
    applied_by: None | GerritUser = None


class GerritSubmitRecord(GerritBase):
    rule_name: None | str = None
    status: Literal["NOT_READY", "OK", "CLOSED"]
    labels: None | list[GerritSubmitRecordLabel] = None
    requirements: None | list[Mapping[str, str]] = None


class GerritChange(GerritBase):
    number: int = Field(..., alias="_number")
    change_id: str
    owner: GerritUser
    subject: str
    project: str
    branch: str

    status: Literal["NEW", "MERGED", "ABANDONED"]
    created: datetime
    updated: datetime
    submitted: None | datetime = None
    id: str  # unique id := <project>~<number>
    virtual_id_number: int  # same as number
    triplet_id: str
    hashtags: list[str]
    submit_type: None | Literal["REBASE_IF_NECESSARY", "MERGE_IF_NECESSARY"] = None
    insertions: int
    deletions: int
    total_comment_count: int
    unresolved_comment_count: int
    has_review_started: bool
    meta_rev_id: str
    current_revision_number: int
    requirements: list[Mapping[str, str]]
    submit_records: list[GerritSubmitRecord]
    removed_from_attention_set: None | dict[str, GerritAttentionSet] = None
    attention_set: None | dict[str, GerritAttentionSet] = None
    work_in_progress: None | bool = None
    submission_id: None | str = None
    submitter: None | GerritUser = None
    topic: None | str = None
    more_changes: None | bool = Field(default=None, alias="_more_changes")
    revert_of: None | int = None
    cherry_pick_of_patch_set: None | int = None
    cherry_pick_of_change: None | int = None
    is_private: None | bool = None


class GerritClient:
    def __init__(self, url: str, username: str, password: str) -> None:
        self.url = url
        self._auth = aiohttp.BasicAuth(username, password)
        self._session: None | aiohttp.ClientSession = None
        self._accounts: MutableMapping[int, GerritAccount] = {}

    async def __aenter__(self) -> "GerritClient":
        self._session = aiohttp.ClientSession(auth=self._auth)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session:
            await self._session.close()

    async def repo_file_content(self, file_path: str, project: str, branch: str) -> str:
        """Get the content of a file from Gerrit.

        Args:
            file_path: Path to the file in the repository
            branch: Branch name

        Returns:
            File content as string
        """
        endpoint = (
            f"a/projects/{quote(project, safe='')}"
            f"/branches/{quote(branch, safe='')}"
            f"/files/{quote(file_path.lstrip('/'), safe='')}/content"
        )
        try:
            raw_response = cast(str, await self._get(endpoint))
        except aiohttp.ClientResponseError as exc:
            if exc.status == 404:
                raise FileNotFoundError(
                    f"{file_path}: {exc.message} ({exc.status}), url={exc.request_info.real_url}"
                ) from exc
            raise

        return base64.b64decode(raw_response).decode("utf-8")

    async def change_reviewers(self, change: GerritChange) -> Iterable[GerritReviewer]:
        raw_reviewers: Json[dict[str, Any]] = await self._get(
            f"a/changes/{change.number}/reviewers"
        )
        return [GerritReviewer.model_validate(raw) for raw in raw_reviewers]

    async def fetch_changes(self, query: Mapping[str, str]) -> AsyncIterable[GerritChange]:
        start_index = 0
        while True:
            if not (
                changes := [
                    GerritChange.model_validate(raw)
                    for raw in cast(
                        list[Mapping[str, str]],
                        await self._get(
                            "a/changes/",
                            params={
                                "q": "+".join(f"{key}:{value}" for key, value in query.items()),
                                "start": f"{start_index}",
                            },
                        ),
                    )
                ]
            ):
                return
            for change in changes:
                yield change
                continue
            start_index += len(changes)

    async def get_account(self, user_or_id: GerritUser | int) -> GerritAccount:
        account_id = user_or_id.account_id if isinstance(user_or_id, GerritUser) else user_or_id
        if account_id not in self._accounts:
            self._accounts[account_id] = GerritAccount.model_validate(
                await self._get(f"a/accounts/{account_id}")
            )
        return self._accounts[account_id]

    async def _get[T](self, request: str, params: None | Mapping[str, str] = None) -> T:
        assert self._session
        # fixme: check for Authentication required
        url = f"{urljoin(self.url, request)}?{'&'.join(f'{key}={value}' for key, value in (params or {}).items())}"
        log().debug("GET %s", url)
        async with self._session.get(url, raise_for_status=True) as response:
            return await self._parse_response(response)

    async def _post[T](self, request: str, params: None | Mapping[str, str] = None) -> T:
        assert self._session
        # fixme: check for Authentication required
        url = f"{urljoin(self.url, request)}?{'&'.join(f'{key}={value}' for key, value in (params or {}).items())}"
        async with self._session.post(url, json={}, raise_for_status=True) as response:
            return await self._parse_response(response)

    async def _parse_response[T](self, response: ClientResponse) -> T:
        # fixme: response.raise_for_status()
        if (raw_response := await response.text()).startswith(")]}'\n"):
            try:
                # first 5 bytes are a XSSI protection prefix we have to get rid of
                return cast(T, json.loads(raw_response[5:]))
            except json.decoder.JSONDecodeError:
                print(raw_response)
                raise
        return cast(T, raw_response)


class CodeOwnersClient:
    """Client for interacting with Gerrit Code Owners plugin.
    https://android-review.googlesource.com/plugins/code-owners/Documentation/rest-api.html
    - [x] POST /projects/{project-name}/code_owners.check_config
    - [ ] GET  /projects/{project-name}/code_owners.project_config
    - [x] GET  /projects/{project-name}/branches/{branch-id}/code_owners.config_files/
    - [x] GET  /projects/{project-name}/branches/{branch-id}/code_owners/{path}
    - [ ] GET  /projects/{project-name}/branches/{branch-id}/code_owners.branch_config
    - [ ] GET  /projects/{project-name}/branches/{branch-id}/code_owners.check/
    - [ ] GET  /projects/{project-name}/branches/{branch-id}/code_owners.config/{path}
    - [ ] GET  /changes/{change-id}/code_owners.status
    - [ ] GET  /changes/{change-id}/revisions/{revison-id}/code_owners/{path}
    - [ ] GET  /changes/{change-id}/revisions/{revison-id}/owned_paths
    - [ ] POST /changes/{change-id}/revisions/{revison-id}/code_owners.check_config
    """

    def __init__(self, gerrit_client: GerritClient, project: str) -> None:
        """Initialize the Gerrit Code Owners client.

        Args:
            gerrit_url: Base URL of the Gerrit instance (e.g., "http://localhost:8080")
            username: Username for authentication
            password: Password for authentication
        """
        self.gerrit_client = gerrit_client
        self.project = project
        self.component_root_directory = "component_owners/"
        self._cached_config_files: MutableMapping[str, Sequence[str]] = {}

    async def check_config(self) -> None:
        """Runs the code_owners.check_config endpoint and complains about all findings"""
        check_config_result = cast(
            Mapping[str, Mapping[str, Sequence[Mapping[str, str]]]],
            await self.gerrit_client._post(  # noqa: SLF001
                f"a/projects/{quote(self.project, safe='')}/code_owners.check_config"
            ),
        )
        fatal_errors = [
            f"{branch}:{file_path} - {issue.get('message', 'Unknown error')}"
            for branch, files in check_config_result.items()
            for file_path, issues in files.items()
            for issue in issues
            if issue.get("status") == "FATAL"
        ]
        if fatal_errors:
            print("\n".join(fatal_errors))
            raise ValueError(
                "Fatal errors detected in Gerrit Code Owners configuration. "
                "Please resolve these issues before using the client."
            )

    async def project_config(self) -> Mapping[str, Any]:
        return await self.gerrit_client._get(  # noqa: SLF001
            f"a/projects/{quote(self.project, safe='')}/code_owners.project_config"
        )

    async def all_code_owners_config_files(self, branch: str) -> Sequence[str]:
        """Get list of code owners configuration files using the official endpoint.
        Args:
            branch: Branch name
        Returns:
            List of file paths that are code owners configuration files
        """
        if branch not in self._cached_config_files:
            self._cached_config_files[branch] = await self.gerrit_client._get(  # noqa: SLF001
                f"a/projects/{quote(self.project, safe='')}"
                f"/branches/{quote(branch, safe='')}"
                f"/code_owners.config_files/"
            )
        return self._cached_config_files[branch]

    def _component_names_from(self, config_files: Iterable[str]) -> Sequence[str]:
        """Parse component names from the list of code owners config files.
        Args:
            config_files: List of file paths from code owners config
        Returns:
            List of component names extracted from self.component_root_directory paths
        """
        return sorted(
            {
                component_path
                for file_path in config_files
                for normalized_path in (file_path.lstrip("/"),)
                if normalized_path.startswith(self.component_root_directory)
                and normalized_path.endswith("/OWNERS_DEFINITION")
                # Extract component name from path like "self.component_root_directory/core_component/OWNERS_DEFINITION"
                for component_path in (
                    normalized_path[
                        len(self.component_root_directory) : -len("/OWNERS_DEFINITION")
                    ],
                )
                # Only direct subdirectories
                if component_path and "/" not in component_path
            }
        )

    def _parse_component_meta_info(self, content: str) -> dict[str, Any]:
        """Parse meta information from comments at the beginning of an OWNERS_DEFINITION file.
        Args:
            content: Content of the OWNERS_DEFINITION file
        Returns:
            Dictionary with parsed meta information including 'description' and 'raw_comments'
        """
        if not content:
            return {"description": "", "raw_comments": []}

        lines = content.split("\n")
        comments = []

        # Extract all comments from the beginning of the file
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                # Remove the # and any leading/trailing whitespace
                comment_text = stripped_line[1:].strip()
                if comment_text:  # Only add non-empty comments
                    comments.append(comment_text)
            elif stripped_line:  # Stop at first non-empty, non-comment line
                break

        # Create a description from all comments
        description = " ".join(comments) if comments else ""

        return {"description": description, "raw_comments": comments}

    async def component_owners_and_members(
        self, component_name: str, branch: str
    ) -> dict[str, Any]:
        """Get owners and members for a specific component by parsing its OWNERS_DEFINITION file.
        Args:
            component_name: Name of the component
            branch: Branch name
        Returns:
            Dictionary with 'owners', 'members', and 'meta_info' keys
        """
        file_path = f"{self.component_root_directory}{component_name}/OWNERS_DEFINITION"
        content = await self.gerrit_client.repo_file_content(file_path, self.project, branch)

        if not content:
            return {
                "owners": [],
                "members": [],
                "meta_info": {"description": "", "raw_comments": []},
            }

        # Parse the content to extract email addresses
        emails = []
        for content_line in content.split("\n"):
            content_line_stripped = content_line.strip()
            # Skip comments and empty lines
            if (
                content_line_stripped
                and not content_line_stripped.startswith("#")
                and "@" in content_line_stripped
            ):
                emails.append(content_line_stripped)

        owners = []
        members = []

        # Treat first email as owner
        owners.append(emails[0])
        members = emails[1:]

        # Parse meta information from comments
        meta_info = self._parse_component_meta_info(content)

        return {"owners": owners, "members": members, "meta_info": meta_info}

    async def all_components_data(self, branch: str) -> dict[str, dict[str, Any]]:
        """Get comprehensive component data using the code_owners.config_files endpoint.

        This method:
        1. Uses the official endpoint to get all config files
        2. Parses component names from self.component_root_directory paths
        3. Retrieves owner and member information for each component
        4. Extracts meta information from comments in OWNERS_DEFINITION files
        5. Returns a cohesive data structure

        Args:
            branch: Branch name

        Returns:
            Dictionary with component names as keys and component data as values.
            Each component data includes 'owners', 'members', 'definition_file', 'all_emails',
            and 'meta_info' keys. The 'meta_info' contains 'description' and 'raw_comments'
            parsed from the beginning comments of the OWNERS_DEFINITION file.
        """
        config_files = await self.all_code_owners_config_files(branch)

        return {
            component_name: {
                "owners": ownership_data["owners"],
                "members": ownership_data["members"],
                "definition_file": f"{self.component_root_directory}{component_name}/OWNERS_DEFINITION",
                "all_emails": ownership_data["owners"] + ownership_data["members"],
                "meta_info": ownership_data["meta_info"],
            }
            for component_name in self._component_names_from(config_files)
            for ownership_data in (await self.component_owners_and_members(component_name, branch),)
        }

    async def owners_for(self, file_path: str, branch: str) -> Sequence[Mapping[str, Any]]:
        """Get owners for a specific file path with resolved email addresses.

        Args:
            file_path: Path to the file
            branch: Branch name

        Returns:
            Dictionary with code owners information including resolved email addresses
        """

        async def augmented_owner(owner: Mapping[str, Any]) -> Mapping[str, Any]:
            account = owner["account"]
            if "email" in account:
                return {**owner, "email": account["email"]}
            if "_account_id" in account:
                # Resolve account ID to email
                return {
                    **owner,
                    "email": (await self.gerrit_client.get_account(account["_account_id"])).email,
                    "account_id": account["_account_id"],
                }
            return owner

        # fixme: create BaseModel
        raw_data: Mapping[str, Any] = await self.gerrit_client._get(  # noqa: SLF001
            f"a/projects/{quote(self.project, safe='')}"
            f"/branches/{quote(branch, safe='')}"
            f"/code_owners/{quote(file_path, safe='')}"
        )

        return [await augmented_owner(owner) for owner in raw_data["code_owners"]]

    async def component_paths(self, component_name: str, branch: str) -> list[str]:
        """List all paths that belong to a specific component.

        This method scans the repository for OWNERS files that reference the component,
        taking into account that OWNERS files in subdirectories override parent ownership.

        Args:
            component_name: Name of the component
            branch: Branch name
        Returns:
            List of directory paths that belong to the component
        """
        owners_files = [
            file_path
            for file_path in await self.all_code_owners_config_files(branch)
            if file_path.endswith("/OWNERS")
        ]
        expected_reference = (
            f"file:/{self.component_root_directory}{component_name}/OWNERS_DEFINITION"
        )
        component_paths = [
            directory_path.lstrip("/")
            for owners_file in owners_files
            if (
                content := (
                    await self.gerrit_client.repo_file_content(owners_file, self.project, branch)
                )
            )
            if expected_reference in content  # fixme: allow for file-only syntax
            # Extract the directory path (remove /OWNERS from the end)
            if (directory_path := owners_file.rstrip("/OWNERS"))
        ]

        return sorted(component_paths)

    async def component_for_path(self, file_path: str, branch: str) -> str | None:
        """Get the component that owns a specific file path.

        This method finds the most specific OWNERS file that applies to the given path
        and extracts the component name from its content.

        Args:
            file_path: Path to the file (e.g., "core_component/core_file.py")
            branch: Branch name
        Returns:
            Component name if found, None if no component owns the path
        """
        normalized_path = file_path.strip("/")

        owners_files = [
            file_path
            for file_path in await self.all_code_owners_config_files(branch)
            if file_path.endswith("/OWNERS")
        ]

        # Find the most specific OWNERS file that applies to this path
        applicable_owners_files = []

        for owners_file in owners_files:
            # Get the directory path of the OWNERS file
            owners_dir = owners_file.rstrip("/OWNERS").lstrip("/")

            # Check if the file path is within this directory
            if not owners_dir:  # Root OWNERS file
                applicable_owners_files.append((owners_file, ""))
            elif normalized_path.startswith(owners_dir + "/") or normalized_path == owners_dir:
                applicable_owners_files.append((owners_file, owners_dir))

        # Sort by specificity (longest path first) due to "set noparent"
        applicable_owners_files.sort(key=lambda x: len(x[1]), reverse=True)

        # Check each applicable OWNERS file for component reference
        for owners_file, _ in applicable_owners_files:
            owners_content = await self.gerrit_client.repo_file_content(
                owners_file.lstrip("/"), self.project, branch
            )
            if owners_content:
                # Extract component reference from content
                component_name = self._component_from(owners_content)
                if component_name:
                    return component_name

        return None

    def _component_from(self, owners_content: str) -> str | None:
        """Extract component name from OWNERS file content.
        Args:
            owners_content: Content of the OWNERS file
        Returns:
            Component name if found, None otherwise
        """
        # fixme: add doctest
        for content_line in owners_content.split("\n"):
            content_line_stripped = content_line.strip()
            if content_line_stripped.startswith(
                f"file:/{self.component_root_directory}"
            ) and content_line_stripped.endswith("/OWNERS_DEFINITION"):
                # Extract component name from "file:/{self.component_root_directory}{component}/OWNERS_DEFINITION"
                component_part = content_line_stripped[
                    len(f"file:/{self.component_root_directory}") : -len("/OWNERS_DEFINITION")
                ]
                if component_part and "/" not in component_part:
                    return component_part
        return None


def netrc_credentials(base_url: str) -> tuple[str, str]:
    """Read credentials from ~/.netrc"""
    hostname = urlparse(base_url).netloc
    if not (
        credentials := netrc.netrc((Path.home() / ".netrc").as_posix()).authenticators(hostname)
    ):
        raise ValueError(f"No credentials for {hostname} found in .netrc")
    return str(credentials[0]), str(credentials[2])


async def fetch_open_reviews() -> None:
    """Example: list all own open reviews"""
    query = {
        # "reviewer": "self",
        # "-owner": "self",
        "owner": "self",
        "status": "open",
        # "status": "closed",
    }

    # query for open reviews
    query = {"reviewer": "self", "-owner": "self", "status": "open"}
    # accounts = {}

    username, password = netrc_credentials(GERRIT_URL)

    async with GerritClient(url=GERRIT_URL, username=username, password=password) as gerrit_client:
        async for change in gerrit_client.fetch_changes(query):
            owner = await gerrit_client.get_account(change.owner)
            reviewers = await gerrit_client.change_reviewers(change)
            print(
                f"[link ={GERRIT_URL}/c/{change.project}/+/{change.number}]{change.project}/{change.branch} {change.change_id[:10]}/{change.number}[/link]"
                f" - O: {owner.name}"
                f" - [bold red]{change.subject}[/]"
                f" - R: {', '.join(f'{r.name}' for r in reviewers)}"
            )
            # print(yaml.dump(change))


async def show_code_ownwers_info() -> None:
    """Example: use some of the Gerrit API wrappers"""
    username, password = netrc_credentials(GERRIT_URL)

    async with GerritClient(GERRIT_URL, username, password) as gerrit_client:
        owners_client = CodeOwnersClient(gerrit_client, DEFAULT_PROJECT_NAME)
        # await owners_client.check_config()
        for owners_file in await owners_client.all_code_owners_config_files(DEFAULT_BRANCH):
            owners_file_content = await gerrit_client.repo_file_content(
                owners_file, DEFAULT_PROJECT_NAME, DEFAULT_BRANCH
            )
            print(owners_file, len(owners_file_content))

        # print(await owners_client.all_components_data(DEFAULT_BRANCH))
        # print(await owners_client.component_for_path("mixed_component/core_part", DEFAULT_BRANCH))
        # print(await owners_client.component_paths("core_component", DEFAULT_BRANCH))
        # print(await owners_client.owners_for("mixed_component/core_part", DEFAULT_BRANCH))
        print(await owners_client.component_owners_and_members("core_component", DEFAULT_BRANCH))


if __name__ == "__main__":
    GERRIT_URL = "https://review.lan.tribe29.com"
    # GERRIT_URL = "http://localhost:8080"

    DEFAULT_BRANCH = "master"

    DEFAULT_PROJECT_NAME = "check_mk"
    # DEFAULT_PROJECT_NAME = "test-project"

    asyncio.run(show_code_ownwers_info())
    asyncio.run(fetch_open_reviews())
