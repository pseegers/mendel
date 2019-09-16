import json

import requests

from mendel.util.colors import cyan
from mendel.util.colors import red
from mendel.util.colors import yellow


def track_event_graphite(*, graphite_host: str,
                         event: str,
                         service_name: str,
                         deployment_user: str,
                         deployment_host: str,
                         project_version: str = None):
    """
    Track who deployed what service and what the release dir is to Graphite's events UI
    """
    if not graphite_host:
        print(red('unable to track deployment event in graphite, no graphite host configured in ~/.mendel.conf'))
        return

    url = 'http://%s/events/' % graphite_host

    user = deployment_user
    what = f'{user} {event} {service_name} version {project_version} on host {deployment_host}'
    tags = [str(s) for s in (service_name, event)]
    post_data = {'what': what, 'tags': tags, 'data': ''}
    try:
        r = requests.post(url=url, data=json.dumps(post_data).encode('utf-8'), timeout=5)
    except Exception as e:
        # try one more time
        try:
            r = requests.post(url=url, data=json.dumps(post_data).encode('utf-8'), timeout=5)
        except Exception as e:
            print(yellow('Error while tracking deployment event in graphite: %s' % str(e)))
            return

    if r.ok:
        print(cyan(f'Tracked deploy in graphite (data={json.dumps(post_data)}'))
    else:
        print(yellow(f'Unable to track deployment event in graphite: HTTP: {r.status_code} content: {r.content}'))
