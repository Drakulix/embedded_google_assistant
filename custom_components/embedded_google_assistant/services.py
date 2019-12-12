from homeassistant.components.tts import CONF_LANG
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    MEDIA_TYPE_MUSIC,
    SERVICE_PLAY_MEDIA,
)
from homeassistant.components.media_player.const import DOMAIN as DOMAIN_MP
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, CONF_PLATFORM
from homeassistant.helpers.event import track_state_change
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from google.auth.transport.requests import Request

from .assistant import Assistant
from .const import (
    DOMAIN,
    ATTR_BASE_URL,
    ATTR_CONTINUATION,
    ATTR_DEVICE_ID,
    ATTR_LANG,
    ATTR_MESSAGE,
    ATTR_HTML_OUT,
    ATTR_PATH,
    ATTR_SILENCE,
    DATA_ASSISTANT,
    DATA_CREDENTIALS,
    EVENT_NAME,
    EVENT_TEXT_RECOGNITION,
    EVENT_TEXT,
    EVENT_AUDIO,
    EVENT_HTML,
    EVENT_DEVICE,
    EVENT_DEVICE_ID,
    EVENT_CONTINUATION,
    EVENT_LANGUAGE,
)
from .stream import SocketSource, WaveSource

SCHEMA_SERVICE_TEXT = vol.Schema(
    {
        vol.Optional(ATTR_BASE_URL): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_LANG): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_HTML_OUT, default=False): cv.boolean,
        vol.Optional(ATTR_CONTINUATION, default=False): cv.boolean,
        vol.Optional(ATTR_SILENCE, default=0): cv.positive_int,
    }
)

SCHEMA_SERVICE_RECORD = vol.Schema(
    {
        vol.Optional(ATTR_BASE_URL): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_LANG): cv.string,
        vol.Required(ATTR_PATH): cv.string,
        vol.Optional(ATTR_HTML_OUT, default=False): cv.boolean,
        vol.Optional(ATTR_CONTINUATION, default=False): cv.boolean,
        vol.Optional(ATTR_SILENCE, default=0): cv.positive_int,
    }
)

def assistant_handle(hass, name, func):
    return lambda call: func(hass, name, call)

async def async_setup_entry(hass, entry):
    hass.data[DOMAIN][entry.title] = entry.data

    safe_name = entry.title.replace('.', '_').replace('@', '_').replace(' ', '_')
    hass.services.async_register(
        DOMAIN, '%s_record_stream' % safe_name,
        assistant_handle(hass, entry.title, handle_record_stream),
        schema=SCHEMA_SERVICE_RECORD)
    hass.services.async_register(
        DOMAIN, '%s_record_file' % safe_name,
        assistant_handle(hass, entry.title, handle_record_file),
        schema=SCHEMA_SERVICE_RECORD)
    hass.services.async_register(
        DOMAIN, '%s_text' % safe_name,
        assistant_handle(hass, entry.title, handle_text),
        schema=SCHEMA_SERVICE_TEXT)
    return True

def handle_record_stream(hass, name, call):
    source = SocketSource(call.data[ATTR_PATH])
    return _handle_input(hass, name, call, audio_in=source)

def handle_record_file(hass, name, call):
    source = WaveSource(call.data[ATTR_PATH])
    return _handle_input(hass, name, call, audio_in=source)

def handle_text(hass, name, call):
   return _handle_input(hass, name, call, message=call.data[ATTR_MESSAGE])

def _handle_input(hass, name, call, audio_in=None, message=None):
    assistant = hass.data[DOMAIN][DATA_ASSISTANT]
    base_url = call.data.get(ATTR_BASE_URL, hass.config.api.base_url)
    silence = call.data[ATTR_SILENCE]

    for resp in assistant.assist(
        hass, name,
        device_id=call.data.get(ATTR_DEVICE_ID),
        lang=call.data.get(ATTR_LANG),
        audio_in=audio_in,
        message=message,
        html_out=call.data.get(ATTR_HTML_OUT),
        is_new_conversation=not call.data.get(ATTR_CONTINUATION, False),
        silence=silence,
    ):
        if not resp['done']:
            hass.bus.fire('%s_text_recognition' % DOMAIN, {
                EVENT_NAME: name,
                EVENT_LANGUAGE: resp.get('language'),
                EVENT_TEXT_RECOGNITION: resp['text_recognition_data'],
            })
        else:
            url = base_url + '/api/embedded_assistant/response/' + resp['resp_id']
            event = {
                EVENT_NAME: name,
                EVENT_TEXT_RECOGNITION: resp.get('text_recognition_data'),
                EVENT_TEXT: resp.get('text_data'),
                EVENT_AUDIO: url + '.ogg',
                EVENT_DEVICE: resp.get('device_data'),
                EVENT_DEVICE_ID: resp.get('device_id'),
                EVENT_LANGUAGE: resp.get('language'),
                EVENT_CONTINUATION: resp.get('should_continue')
            }
            if call.data.get(ATTR_HTML_OUT):
                event[EVENT_HTML] = url + '/html'
            hass.bus.fire('%s_done' % DOMAIN, event)
