"""Platform for sensor integration."""
from homeassistant.helpers.entity import Entity
from homeassistant.const import DEVICE_CLASS_TIMESTAMP

from .const import DOMAIN, DATA_ASSISTANT, EVENT_NAME

async def async_setup_entry(hass, entry, add_entities):
    """Set up the sensor platform."""
    assistant = hass.data[DOMAIN][DATA_ASSISTANT]
    add_entities([AssistantSensor(hass, assistant, entry.title)])

class AssistantSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, hass, assistant, assistant_name):
        """Initialize the sensor."""
        self._state = None
        self._attributes = None
        self._assistant = assistant
        self._id = assistant_name

        async def handle_event_start(event):
            await handle_event('running', event)

        async def handle_event_done(event):
            await handle_event('done', event)

        # Listener to handle google assistant events
        async def handle_event(name, event):
            if event.data[EVENT_NAME] == self._id:
                data = dict(event.data)
                del data[EVENT_NAME]
                self._attributes = data
                self._state = name
                self.async_schedule_update_ha_state()

        # Listen for when example_component_my_cool_event is fired
        self._listener = hass.bus.async_listen('%s_done' % DOMAIN, handle_event_done)
        self._listener = hass.bus.async_listen('%s_starting' % DOMAIN, handle_event_start)

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def available(self):
        return self._state is not None

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Google Assistant (%s)' % self._id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self):
        return self._id