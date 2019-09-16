import json

import requests

from mendel.util.colors import cyan
from mendel.util.colors import red
from mendel.util.colors import yellow


def track_event_slack(*, slack_url: str,
                      slack_emoji: str,
                      event: str,
                      service_name: str,
                      deployment_user: str,
                      deployment_host: str,
                      project_version: str = None,
                      commit_hash: str = None,
                      failure: bool = False):
    """
    Notify Slack that a mendel event has taken place
    """
    if not slack_url:
        print(yellow('No slack_url found; skipping slack notification'))
        return

    if failure:
        text = f"*DEPLOY FAILED FOR* {deployment_user} {service_name} @ {commit_hash}, version *{project_version}* to host(s) {deployment_host} with error {event} *ABORTING DEPLOY*"
    else:
        text = f"{deployment_user} *{event.upper()}* {service_name} @ {commit_hash}, version *{project_version}* to host(s) {deployment_host}"
    params = {
        'username': 'Mendel 3',
        'text': text,
        'icon_emoji': ":rotating_light:" if failure else slack_emoji
    }
    try:
        resp = requests.post(url=slack_url, data=json.dumps(params).encode('utf-8'), timeout=5)
    except Exception as e:
        print(red(f"Could not notify slack that a mendel event took place at url: {slack_url} with error {e}"))
        return
    if resp.ok:
        print(cyan('Tracked deploy in slack (data=%s' % json.dumps(params)))
    else:
        print(
            red(f"Could not notify slack that a mendel event took place at url: {slack_url} with error {resp.content}"))
