from .const import ASSISTANT_API_ENDPOINT, DOMAIN, DATA_CREDENTIALS

import logging
import json
import uuid

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

_LOGGER = logging.getLogger(__name__)

def register_device_model(
    session,
    project_id: str,
    name: str = "Home Assistant",
    desc: str = "Home Assistant Embedded Google Assistant Integration",
    icon: str = "action.devices.types.COMPUTER"
) -> str:
    device_model_base_url = (
        'https://%s/v1alpha2/projects/%s/deviceModels/' % (ASSISTANT_API_ENDPOINT,
                                                    project_id)
    )

    model_id = "%s-home-assistant" % project_id

    model_payload = {
        "project_id": project_id,
        "device_model_id": model_id,
        "manifest": {
            "manufacturer": "Home Assistant",
            "product_name": name,
            "device_description": desc, 
        },
        "device_type": icon,
    }

    r = session.post(device_model_base_url, data=json.dumps(model_payload))
    if r.status_code != 200:
        _LOGGER.error('Failed to register device model: %', r.text)
        raise Exception('register_device_model failed', r.status_code, r.text)
    else:
        _LOGGER.info('New device model %s created', model_id)
        return model_id

def register_device(
    session,
    project_id: str,
    model_id: str,
    device_id: str=None,
) -> str:
    if device_id is None:
        device_id = str(uuid.uuid1())
    
    device_base_url = (
        'https://%s/v1alpha2/projects/%s/devices/' % (ASSISTANT_API_ENDPOINT,
                                                    project_id)
    )

    device_payload = {
        'id': device_id,
        'model_id': model_id,
        'client_type': 'SDK_SERVICE'
    }
    
    r = session.post(device_base_url, data=json.dumps(device_payload))
    if r.status_code != 200:
        _LOGGER.error('Failed to register device: %', r.text)
        raise Exception("register_device failed", r.status_code, r.text)
    else:
        _LOGGER.info('New device %s created', device_id)
        return device_id
            
def get_devices(
    session,
    project_id: str,
):
    device_base_url = (
        'https://%s/v1alpha2/projects/%s/devices/' % (ASSISTANT_API_ENDPOINT,
                                                    project_id)
    )

    r = session.get(device_base_url)
    if r.status_code != 200:
        _LOGGER.error('Failed to get devices: %s', r.text)
        raise Exception("get_devices failed", r.status_code, r.text)
    else:
        # {
        #   "devices": [
        #     {
        #       "id": "d717be74-f5d4-11e9-8d51-6e7b7d93a058",
        #       "nickname": "Home Assistant",
        #       "name": "projects/piassistent-2dde9/devices/d717be74-f5d4-11e9-8d51-6e7b7d93a058",
        #       "modelId": "piassistent-2dde9-home-assistant",
        #       "clientType": "SDK_LIBRARY"
        #     }
        #   ]
        # }
        return r.json()['devices']

def delete_device_model(
    session,
    project_id: str,
    model_id: str,
):
    device_model_url = (
        'https://%s/v1alpha2/projects/%s/deviceModels/%s' % (ASSISTANT_API_ENDPOINT,
                                                    project_id, model_id)
    )

    r = session.delete(device_model_url)
    if r.status_code != 200:
        _LOGGER.error('Failed to delete device model: %s', r.text)
        raise Exception("delete_device_model failed", r.status_code, r.text)

def delete_device(
    session,
    project_id: str,
    device_id: str,
):
    device_url = (
        'https://%s/v1alpha2/projects/%s/devices/%s' % (ASSISTANT_API_ENDPOINT,
                                                    project_id, device_id)
    )

    r = session.delete(device_url)
    if r.status_code != 200:
        _LOGGER.error('Failed to delete device: %s', r.text)
        raise Exception("delete_device failed", r.status_code, r.text)

def get_creds(hass, assistant_id: str):
    http_request = Request()

    if DATA_CREDENTIALS not in hass.data[DOMAIN]:
        hass.data[DOMAIN][DATA_CREDENTIALS] = {}
    if assistant_id not in hass.data[DOMAIN][DATA_CREDENTIALS]:
        credentials = Credentials(**hass.data[DOMAIN][assistant_id][DATA_CREDENTIALS])
        credentials.refresh(http_request)
        hass.data[DOMAIN][DATA_CREDENTIALS][assistant_id] = credentials

    credentials = hass.data[DOMAIN][DATA_CREDENTIALS][assistant_id]
    if credentials.expired:
        credentials.refresh(http_request)

    return credentials
    
