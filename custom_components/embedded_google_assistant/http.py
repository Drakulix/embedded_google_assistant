from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, DATA_ASSISTANT

async def async_setup(hass, config):
    assistant = hass.data[DOMAIN][DATA_ASSISTANT]
    hass.http.register_view(EmbeddedAssistantRespTextView(assistant))
    hass.http.register_view(EmbeddedAssistantRespAudioView(assistant))
    hass.http.register_view(EmbeddedAssistantRespHTMLView(assistant))
    return True

class EmbeddedAssistantRespTextView(HomeAssistantView):
    """Embedded Assistant view to serve a response text."""

    requires_auth = False
    url = "/api/embedded_assistant/response/{resp_id}/text"
    name = "api:embedded_assistant:response:text"

    def __init__(self, assistant):
        """Initialize a the view."""
        self.assistant = assistant

    async def get(self, request, resp_id):
        """Start a get request."""
        try:
            data = self.assistant.get_resp(resp_id)['text_data']
            return web.Response(body=data, content_type='text/plain')
        except (KeyError, TypeError):
            return web.Response(status=404)


class EmbeddedAssistantRespAudioView(HomeAssistantView):
    """Embedded Assistant view to serve a response audio."""

    requires_auth = False
    url = "/api/embedded_assistant/response/{resp_id}/audio"
    name = "api:embedded_assistant:response:audio"

    def __init__(self, assistant):
        """Initialize a the view."""
        self.assistant = assistant

    async def get(self, request, resp_id):
        """Start a get request."""
        try:
            data = self.assistant.get_resp(resp_id)['audio_data']

            return web.Response(body=data, context_type='audio/mpeg')
        except (KeyError, TypeError):
            return web.Response(status=404)


class EmbeddedAssistantRespHTMLView(HomeAssistantView):
    """Embedded Assistant view to serve a response html."""

    requires_auth = False
    url = "/api/embedded_assistant/response/{resp_id}/html"
    name = "api:embedded_assistant:response:html"

    def __init__(self, assistant):
        """Initialize a the view."""
        self.assistant = assistant

    async def get(self, request, resp_id):
        """Start a get request."""
        try:
            data = self.assistant.get_resp(resp_id)['html_data']
            return web.Response(body=data, content_type='text/html')
        except (KeyError, TypeError):
            return web.Response(status=404)

