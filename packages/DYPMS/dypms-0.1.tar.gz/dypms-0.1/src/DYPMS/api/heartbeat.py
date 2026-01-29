import requests
from .util import get_response_json_with_check


def heartbeat(client):

    url = f"{client.base_url}/lib/monitor/v1/heartbeat"
    headers = client.get_headers()
    try:
        response = requests.get(url, headers=headers)
        get_response_json_with_check(response)
    except Exception as e:
        raise e
