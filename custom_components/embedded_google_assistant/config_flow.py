import logging
from collections import OrderedDict
import voluptuous as vol

from homeassistant import config_entries

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import AuthorizedSession

from .const import (
    DOMAIN,
    
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_CODE,
    CONF_DEVICE_MODEL_ID,
    CONF_NAME,
    CONF_PROJECT_ID,

    DATA_CREDENTIALS,
    DATA_DEVICE,
    DATA_PROJECT_ID,
    
    AUTH_URI,
    AUTH_PROVIDER_X509_CERT_URL,
    ASSISTANT_API_ENDPOINT,
    TOKEN_URI,
    OAUTH_REDIRECT,
    SCOPES
)
from .device_helper import register_device, register_device_model, delete_device, delete_device_model, get_creds, get_devices

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class GoogleAssistantDeviceFlowHandler(config_entries.ConfigFlow):
    VERSION = 1

    flow = None
    tokens = None
    device = None
    project_id = None

    async def async_step_user(self, user_input):
        errors = {}
        if user_input is not None:
            if DOMAIN not in self.hass.data:
                self.hass.data[DOMAIN] = {}    
            if user_input[CONF_NAME] not in self.hass.data[DOMAIN]:
                return await self.async_step_auth(user_input)
            
            errors[CONF_NAME] = "not_unique"

        # Use OrderedDict to guarantee order of the form shown to the user
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_NAME)] = str
        data_schema[vol.Required(CONF_CLIENT_ID)] = str
        data_schema[vol.Required(CONF_CLIENT_SECRET)] = str
        data_schema[vol.Required(CONF_PROJECT_ID)] = str

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema(data_schema),
            errors=errors
        )

    async def async_step_auth(self, user_input):
        errors = {}
        if user_input.get(CONF_CODE):
            auth_url, state = self.flow.authorization_url(flow_id=self.flow_id)
            data_schema = OrderedDict()
            data_schema[vol.Required(CONF_CODE)] = str

            try:
                self.flow.fetch_token(code=user_input[CONF_CODE])
                credentials = self.flow.credentials
                self.tokens = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'id_token': credentials.id_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': SCOPES
                }
            except ValueError:
                errors[CONF_TOKEN] = "invalid_token"
                return self.async_show_form(
                    step_id='auth',
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"url": auth_url},
                    errors=errors
                )
            
            session = AuthorizedSession(credentials)
            try:
                model_id = register_device_model(session, self.project_id)
            except:
                errors['base'] = "register_device_model"
                return self.async_show_form(
                    step_id='auth',
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"url": auth_url},
                    errors=errors
                )

            device_id = None
            try:
                device_id = register_device(session, self.project_id, model_id)
            except:
                errors['base'] = "register_device"
                return self.async_show_form(
                    step_id='auth',
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"url": auth_url},
                    errors=errors
                )

            self.device = {
                'device_id': device_id,
                'device_model_id': "%s-home-assistant" % self.project_id,
            }
            return await self.async_step_finish()

        # Create the flow using the client secrets file from the Google API
        # Console.
        flow = Flow.from_client_config(
            {
                "installed": {
                    "auth_uri": AUTH_URI,
                    "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
                    "client_id": user_input[CONF_CLIENT_ID],
                    "client_secret": user_input[CONF_CLIENT_SECRET],
                    "token_uri": TOKEN_URI,
                    "project_id": user_input[CONF_PROJECT_ID],
                }
            },
            scopes=SCOPES,
            redirect_uri=OAUTH_REDIRECT)
        
        # Tell the user to go to the authorization URL.
        auth_url, state = flow.authorization_url(flow_id=self.flow_id)

        self.title = user_input[CONF_NAME]
        self.flow = flow
        self.project_id = user_input[CONF_PROJECT_ID]

        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_CODE)] = str

        return self.async_show_form(
            step_id='auth',
            data_schema=vol.Schema(data_schema),
            description_placeholders={"url": auth_url},
            errors=errors
        )
    
    async def async_step_finish(self, user_input=None):
        return self.async_create_entry(
            title=self.title,
            data={
                DATA_CREDENTIALS: self.tokens,
                DATA_DEVICE: self.device,
                DATA_PROJECT_ID: self.project_id,
            }
        )

async def async_step_remove(hass, entry):
    config = entry.data
    credentials = get_creds(hass, entry.title)
    project_id = config[DATA_PROJECT_ID]    

    session = AuthorizedSession(credentials)

    try:
        for device in get_devices(session, project_id):
            if device['modelId'] == config[DATA_DEVICE]['device_model_id']:
                delete_device(session, project_id, device['id'])
        delete_device_model(session, project_id, config[DATA_DEVICE]['device_model_id'])
    except e:
        pass

    del hass.data[DOMAIN][entry.title]




