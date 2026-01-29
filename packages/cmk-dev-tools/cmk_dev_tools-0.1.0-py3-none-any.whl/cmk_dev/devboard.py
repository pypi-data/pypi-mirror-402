#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["textual", "rich", "trickkiste", "cmk-devops-tools"]
# [tool.uv]
# sources = {cmk-devops-tools={path="../checkmk_dev_tools", editable=true}}
# ///

""" """

# ylint: disable=C0301 # Line too long
# ylint: disable=C0115,C0116 # docstring
# ylint: disable=R0912,R0914,R0915 # too many statements/variables/branches
# ylint: disable=W1514 # open without encoding
# ylint: disable=W0511 # todo
# ylint: disable=W0201 # Attribute defined outside __init__
# ylint: disable=too-many-locals
# ylint: disable=too-many-instance-attributes
# ylint: disable=too-many-branches
# ylint: disable=unnecessary-lambda

import argparse
import asyncio
import json
import logging
import time
import xml.etree.ElementTree as ET
from collections.abc import (
    Callable,
    Iterable,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import cast
import os
import sys
import json
from datetime import datetime
from contextlib import suppress
from requests import ReadTimeout
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.widgets import RichLog, Static, Tree
from textual.widgets.tree import TreeNode
from trickkiste.base_tui_app import TuiBaseApp
from gerrit_utils.client import GerritClient, netrc_credentials
from jira_utils.client import JiraClient
from aiohttp import ClientConnectorError

__version__ = "1.0"

GERRIT_URL = "https://review.lan.tribe29.com"


def log() -> logging.Logger:
    """Returns the logger instance to use here"""
    return logging.getLogger("trickkiste.devboard")


def show_notification(summary: str, message: str, icon: str) -> None:
    """Convenience wrapper for showing notifications"""
    # try:
    #    Notification(summary, message, f"/usr/share/icons/gnome/32x32/emotes/{icon}").show()
    # except DBusException as exc:
    #    log().error("Could not show notification: %s", exc)


class DevBoard(TuiBaseApp):
    """Dev dashboard TUI"""

    CSS = """
      Tree > .tree--guides {
        color: $success-darken-3;
      }
      Tree > .tree--guides-selected {
        text-style: none;
        color: $success-darken-1;
      }
      #app_log {
          height: 8;
      }
    """

    BINDINGS = [
        Binding("r", "update_reviews", "Update Reviews"),
        Binding("j", "update_tickets", "Update Tickets"),
    ]
    CONFIG_FILE = "sheriff-state.json"

    def __init__(self) -> None:
        super().__init__(logger_show_funcname=False, logger_show_tid=True, logger_show_name=True)
        cli_args = self.parse_arguments()
        self.set_log_levels(cli_args.log_level, ("trickkiste", "DEBUG"))

        self.main_tree_widget: Tree[None] = Tree("Devboard")
        self.main_tree_widget.show_root = False
        # chime.notify_exceptions()
        # chime.theme(cli_args.chime_theme)

        self.config: MutableMapping[
            str, Sequence[str] | MutableMapping[str, MutableMapping[str, int]]
        ] = {"bad-jobs": {}}

        # notify2_init("Test")

    def parse_arguments(self) -> argparse.Namespace:
        """parse command line arguments and return argument object"""
        parser = argparse.ArgumentParser(description=__doc__)
        self.add_default_arguments(parser)
        parser.add_argument(
            "--chime-theme",
            type=str.lower,
            # choices=chime.themes(),
            default="big-sur",
        )
        parser.add_argument("--json", action="store_true")
        parser.add_argument(
            "job_pattern", nargs="*", type=str, default=["checkmk", "maintenance", "werks"]
        )
        parser.add_argument("--no-monitoring", action="store_true")
        parser.add_argument("--no-build-node-visualization", action="store_true")

        return parser.parse_args()

    async def initialize(self) -> None:
        """UI entry point"""
        with suppress(FileNotFoundError):
            with open(self.CONFIG_FILE, encoding="utf-8") as config_file:
                self.config = json.load(config_file)

        self.review_tree_node = self.main_tree_widget.root.add(
            "[bold spring_green1]Reviews[/] [white](press 'r' to force update)[/]",
            expand=True,
            allow_expand=False,
        )
        self.ticket_tree_node = self.main_tree_widget.root.add(
            "[bold spring_green1]Tickets[/] [white](press 't' to force update)[/]",
            expand=True,
            allow_expand=False,
        )

        self.maintain_review_tree()
        self.maintain_ticket_tree()
        self.maintain_statusbar()

    def cleanup(self) -> None:
        """Executed on shutdown - write config file containing job states"""
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    async def action_review_tree(self) -> None:
        """Resets the update jobs 'fuse', i.e. does a forced update"""
        await self.log_event("update reviews")
        self.update_review_tree_fuse = 0

    async def action_ticket_tree(self) -> None:
        """Resets the update jobs 'fuse', i.e. does a forced update"""
        await self.log_event("update tickets")
        self.update_ticket_tree_fuse = 0

    def compose(self) -> ComposeResult:
        """Set up the UI"""
        yield self.main_tree_widget
        yield from super().compose()

    async def update_ticket_tree(self, jira_session) -> None:
        log().debug("update_ticket_tree")
        self.ticket_tree_node.remove_children()

        for i in await jira_session.fetch_issues("status!=closed and assignee=currentUser()"):
            self.ticket_tree_node.add_leaf(
                # f"{i['key']:10} "
                f"[link=https://jira.lan.tribe29.com/browse/{i['key']:10}]"
                f"{i['key']:10}"
                f" {i['summary']:100}"
                "[/link] ("
                f"{str(i['reporter']):22}, "
                f"{i['status']:24}, "
                f"{[s['name'] for s in i['sprints']]}, "
                ")"
                # f"a={str(i['assignee']):22}"
                # f"f={str(i['fixVersions'] and i['fixVersions'][0]):10}"
            )
            # print(max(len(str(i['status'])) for i in issues))

    async def update_review_tree(self, gerrit_session) -> None:
        """One tree building interation"""
        log().debug("update_review_tree")
        self.review_tree_node.remove_children()
        query = {
            # "reviewer": "self",
            # "-owner": "self",
            "owner": "self",
            "status": "open",
            # "status": "closed",
        }

        # query for open reviews
        query = {"reviewer": "self", "-owner": "self", "status": "open"}
        accounts = {}

        async for change in gerrit_session.fetch_changes(query):
            owner = await gerrit_session.get_account(change.owner)
            reviewers = await gerrit_session.change_reviewers(change)
            short_change = (
                f"{change.project}/{change.branch} {change.change_id[:10]}/{change.number}"
            )
            self.review_tree_node.add_leaf(
                f"[deep_sky_blue3 link ={gerrit_session.url}/c/{change.project}/+/{change.number}]{short_change:40}[/]"
                f" - O: {owner.name}"
                f" - [bold red]{change.subject}[/]"
                f" - R: {', '.join(f'{r.name}' for r in reviewers)}"
            )
        r"""
            job_node.set_label(
                Text.from_markup(
                    rf"[bold {'blink' if job.is_building else ''}]{status_icon}[/]"
                    rf" [bold deep_sky_blue1 link={job.url}]{job.name}[/]"
                    rf"{indentation * ' '}"
                    rf" [blue][link={job.url}/build]\[build][/link]"
                    f"{fail_str}"
                    # f"[rebuild]({url}{last_build}/rebuild)"
                )
            )
            job_node.add_leaf(rich_text_from(change))
                job_node.expand()
            else:
                job_node.collapse()
        """

    @work(exit_on_error=True)
    async def maintain_review_tree(self) -> None:
        """Busy worker task continuously updating the review tree"""
        username, password = netrc_credentials(GERRIT_URL)
        log().info("using username %s", username)
        while True:
            try:
                async with GerritClient(GERRIT_URL, username, password) as session:
                    while True:
                        await self.update_review_tree(session)

                        self.update_review_tree_fuse = cast(
                            int, self.config.get("review-update-interval") or 120
                        )
                        while self.update_review_tree_fuse > 0:
                            self.update_review_tree_fuse -= 1
                            await asyncio.sleep(1)

            except (TimeoutError, ClientConnectorError) as exc:
                log().error("%s - retry in a couple of seconds..", exc)
                await asyncio.sleep(20)

    @work(exit_on_error=True)
    async def maintain_ticket_tree(self) -> None:
        """Busy worker task continuously updating the review tree"""
        while True:
            try:
                async with JiraClient("https://jira.lan.tribe29.com") as jira_session:
                    while True:
                        await self.update_ticket_tree(jira_session)

                        self.update_ticket_tree_fuse = cast(
                            int, self.config.get("ticket-update-interval") or 120
                        )
                        while self.update_ticket_tree_fuse > 0:
                            self.update_ticket_tree_fuse -= 1
                            await asyncio.sleep(1)

            except TimeoutError as exc:
                log().error("%s - retry in a couple of seconds..", exc)
                await asyncio.sleep(20)

    @work(exit_on_error=True)
    async def maintain_statusbar(self) -> None:
        """Status bar stub (to avoid 'nonsense' status)"""
        while True:
            self.update_status_bar(
                f"{len(asyncio.all_tasks())} async tasks │ Devboard v{__version__}"
            )
            await asyncio.sleep(3)


def main() -> None:
    """The main function"""
    DevBoard().execute()


if __name__ == "__main__":
    main()
