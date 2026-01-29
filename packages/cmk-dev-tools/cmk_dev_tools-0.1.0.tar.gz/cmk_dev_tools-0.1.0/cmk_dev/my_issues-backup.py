#!/usr/bin/env python3

import os
import sys
from jira import JIRA
import json
from datetime import datetime
from contextlib import suppress
from requests import ReadTimeout

EXPORT_FILE = "jira_issues.json"
FIELDS = [
    # 'comment',
    'summary',
    'description',
    'issuetype',
    'created',
    'status',
    'creator',
    'versions',
    'reporter',
    'assignee',
    'fixVersions',
    'components',
    'votes',
    'priority',
]

def extract(issue, extract_comments=False):
    fields = issue.raw["fields"]

    if extract_comments:
        comments = fields['comment']['comments']
        import yaml
        for c in comments:
            if c['author']['name'] == "frans.fuerst":
                print(issue.raw["id"], issue.raw["key"])
                print(c['body'])

    return {
        "id": issue.raw["id"],
        "key": issue.raw["key"],
        "summary": fields['summary'],
        "description": fields['description'],
        "creator": (fields.get('creator') or {'displayName': 'None'})['displayName'],
        "reporter": (fields.get('reporter') or {'displayName': 'None'})['displayName'],
        "assignee": (fields.get('assignee') or {'displayName': 'None'})['displayName'],
        "created": fields['created'],
        "status": fields['status']['name'],
        "versions": [v['name'] for v in fields['versions']],
        "fixVersions": [v['name'] for v in fields['fixVersions']],
        "components": [c['name'] for c in fields['components']],
        "priority": fields['priority']['name'],
        "votes": fields['votes']['votes'],
        "issuetype": fields['issuetype']['name'],
    }


def load_issues(filename):
    with suppress(FileNotFoundError):
        return json.load(open(filename))
    return {}


def fetch_issues(jira, proj, issues):
    while True:
        issues_chunk = [
            extract(issue)
            for issue in jira.search_issues(
                jql_str=f'project={proj} and assignee = currentUser()',
                # jql_str=f'project={proj}',
                startAt=len(issues),
                maxResults=100,
                fields=','.join(FIELDS),
            )]
        if not issues_chunk:
            break
        issues.extend(issues_chunk)
        print(len(issues), issues_chunk[-1]['id'], issues_chunk[-1]['key'], issues_chunk[-1]['created'])


def main():
    jira = JIRA(
        server="https://jira.lan.tribe29.com",
        basic_auth=open(os.path.expanduser("~/.cmk-credentials-me")).readline().strip("\n").split(":"),
        validate=True,
        #timeout=1,
    )

    #jira.issue('CMK-6944').update(reporter={'name': 'Administrator'})

    print("Read issues from file..")
    projects = load_issues(EXPORT_FILE)

    try:
        for proj in {'CMK', 'SUP', 'FEED', 'ERP', 'AQ'}:
            print(f"Fetch issues for project {proj!r}")
            fetch_issues(jira, proj, projects.setdefault(proj, []))
    finally:
        print("Dump issues to file..")
        json.dump(projects, open(EXPORT_FILE, "w"), indent=2)

    for p, issues in projects.items():
        for i in issues:
            print(
                f"{i['key']:10} "
                f"r={str(i['reporter']):22} "
                f"s={i['status']:24} "
                f"a={str(i['assignee']):22} "
                f"f={str(i['fixVersions'] and i['fixVersions'][0]):10} "
                f"|{i['summary']} "
            )
        print(max(len(str(i['status'])) for i in issues))


if __name__ == "__main__":
    main()
