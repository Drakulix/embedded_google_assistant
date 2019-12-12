from homeassistant.components.conversation.agent import AbstractConversationAgent
from homeassistant.helpers import intent

from .assistant import Assistant

class GAAgent(AbstractConversationAgent):
    def __init__(self, hass, assistant):
        self._hass = hass
        self._assistant = assistant
    
    @property
    def attribution(self):
        """Return the attribution."""
        return return {"name": "Powered by Google Assistant SDK", "url": "https://developers.google.com/assistant/sdk/"}

    @abstractmethod
    async def async_process(
        self, text: str, conversation_id: Optional[str] = None
    ) -> intent.IntentResponse:
        self._assistant.assist(hass, )