DOMAIN = 'embedded_google_assistant'

CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'
CONF_CODE = 'oauth_code'
CONF_DEVICE_MODEL_ID = 'device_model_id'
CONF_NAME = 'assistant_name'
CONF_PROJECT_ID = 'project_id'

DATA_ASSISTANT = 'assistant'
DATA_CREDENTIALS = 'credentials'
DATA_DEVICE = 'device'
DATA_PROJECT_ID = 'project_id'

ATTR_BASE_URL = 'base_url'
ATTR_DEVICE_ID = 'device_id'
ATTR_LANG = 'language'
ATTR_MESSAGE = 'message'
ATTR_PATH = 'file_path'
ATTR_HTML_OUT = 'html_out'
ATTR_CONTINUATION = 'continue'

EVENT_NAME = 'assistant_name'
EVENT_TEXT_RECOGNITION = 'text_recognition'
EVENT_TEXT = 'text'
EVENT_AUDIO = 'audio_url'
EVENT_HTML = 'html_url'
EVENT_DEVICE = 'device_data'
EVENT_DEVICE_ID = 'device_id'
EVENT_LANGUAGE = 'language'
EVENT_CONTINUATION = 'should_continue'

AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
AUTH_PROVIDER_X509_CERT_URL = 'https://www.googleapis.com/oauth2/v1/certs'
OAUTH_REDIRECT = 'urn:ietf:wg:oauth:2.0:oob'
SCOPES = ['https://www.googleapis.com/auth/assistant-sdk-prototype']

SUPPORT_LANGUAGES = [
    "de-DE",
    "en-AU",
    "en-CA",
    "en-GB",
    "en-IN",
    "en-US",
    "fr-CA",
    "fr-FR",
    "it-IT",
    "ja-JP",
    "es-ES",
    "es-MX",
    "ko-KR",
    "pt-BR",
]
DEFAULT_LANG = "en-US"