#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   #"pydantic",
#   "rich",
#   "jira",
#   ]
# ///

"""Provide information about CI artifacts and make them available locally

Copyright (C) 2024 Checkmk GmbH - License: GNU General Public License v2
This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
conditions defined in the file COPYING, which is part of this source code package.
"""

import asyncio
from jira import JIRA
import os
import re
from rich import print


class JiraClient:
    def __init__(self, url: str) -> None:
        self.url = url

    async def __aenter__(self) -> "JiraClient":
        self._session = JIRA(
            server=self.url,
            basic_auth=open(os.path.expanduser("~/.cmk-credentials-me"))
            .readline()
            .strip("\n")
            .split(":"),
            validate=True,
            # timeout=1,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session:
            self._session.close()

    def extract(self, issue, extract_comments=False):
        fields = issue.raw["fields"]
        # print(fields)

        if extract_comments:
            comments = fields["comment"]["comments"]
            import yaml

            for c in comments:
                if c["author"]["name"] == "frans.fuerst":
                    print(issue.raw["id"], issue.raw["key"])
                    print(c["body"])

        sprints = [
            dict(
                raw_attrs.split("=")
                for raw_attrs in re.match(r"^com.*\[(.*)\]$", raw_sprint).group(1).split(",")
            )
            for raw_sprint in (fields["customfield_10104"] or [])
        ]

        return {
            "id": issue.raw["id"],
            "key": issue.raw["key"],
            "summary": fields["summary"],
            # "description": fields['description'],
            "creator": (fields.get("creator") or {"displayName": "None"})["displayName"],
            "reporter": (fields.get("reporter") or {"displayName": "None"})["displayName"],
            "assignee": (fields.get("assignee") or {"displayName": "None"})["displayName"],
            "created": fields["created"],
            "status": fields["status"]["name"],
            # "versions": [v['name'] for v in fields['versions']],
            # "fixVersions": [v['name'] for v in fields['fixVersions']],
            # "components": [c['name'] for c in fields['components']],
            "issuetype": fields["issuetype"]["name"],
            "sprints": sprints,
        }

    async def fetch_issues(self, query: str | None = None):
        issues = []

        FIELDS = [
            # key
            # id
            # 'comment',
            "summary",
            # 'description',
            "issuetype",
            "created",
            "status",
            "creator",
            # 'versions',
            "reporter",
            "assignee",
            # 'fixVersions',
            # 'components',
            "customfield_10104",
        ]
        while True:
            issues_chunk = [
                self.extract(issue)
                for issue in self._session.search_issues(
                    jql_str=query,
                    startAt=len(issues),
                    maxResults=100,
                    fields=",".join(FIELDS),
                )
            ]
            if not issues_chunk:
                break
            issues.extend(issues_chunk)
            print(
                len(issues),
                issues_chunk[-1]["id"],
                issues_chunk[-1]["key"],
                issues_chunk[-1]["created"],
            )
        return issues


async def list_issues():
    async with JiraClient("https://jira.lan.tribe29.com") as jira_session:
        issues = await jira_session.fetch_issues("status!=closed and assignee=currentUser()")
        for i in issues:
            print(
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
    #     print(max(len(str(i['status'])) for i in issues))
    print(len(issues))


if __name__ == "__main__":
    asyncio.run(list_issues())
