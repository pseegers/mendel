import requests

from mendel.util.colors import cyan
from mendel.util.colors import red
from mendel.util.colors import yellow


def track_event_api(*, track_event_endpoint: str,
                    event: str,
                    service_name: str,
                    deployment_user: str,
                    deployment_host: str):
    """
    Track who deployed what service and what the release dir is to an external REST API
    """
    if not track_event_endpoint:
        print(red('Unable to track deployment event in custom api, no api endpoint configured in config'))
        return

    data = {
        'service': service_name,
        'host': deployment_host,
        'deployer': deployment_user,
        'event': event
    }

    url = 'http://%s' % track_event_endpoint

    try:
        r = requests.post(url=url, data=data, timeout=5)
    except Exception as e:
        print(yellow(f"Could not track event api with url {url} got error {str(e)}"))
        return

    if r.ok:
        print(cyan(f'Tracked deploy to external_api {track_event_endpoint}: (data={data}'))
    else:
        print(
            yellow(f'Unable to track deployment event to the external API (HTTP {r.status_code} content {r.content})'))
