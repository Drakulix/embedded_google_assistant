from google.auth.transport.grpc import secure_authorized_channel
from google.auth.transport.requests import Request, AuthorizedSession
from google.oauth2.credentials import Credentials

from google.assistant.embedded.v1alpha2.embedded_assistant_pb2 import (
    AssistConfig,
    AssistRequest,
    AssistResponse,
    AudioInConfig,
    AudioOutConfig,
    DeviceConfig,
    DialogStateIn,
    DialogStateOut,
    ScreenOutConfig,
)
from google.assistant.embedded.v1alpha2.embedded_assistant_pb2_grpc import EmbeddedAssistantStub

import logging
import time
import uuid
import json
import mutagen
from pydub import AudioSegment
import io

from .const import DOMAIN, ASSISTANT_API_ENDPOINT, DEFAULT_LANG, DATA_CREDENTIALS, DATA_DEVICE, DATA_PROJECT_ID
from .device_helper import get_creds, get_devices, register_device

_LOGGER = logging.getLogger(__name__)

class Assistant(object):
    def __init__(self):
        self.known_devices = None
        self.conversation_states = {}
        self.responses = {}

    def get_resp(self, resp_id):
        to_delete = []
        for (resp_id, data) in self.responses.items():
            # clear what is older then 10 minutes
            if time.time() - data['_timestamp'] > 600.0:
                to_delete.append(resp_id)
        for resp_id in to_delete:
            del self.responses[resp_id]
        
        return self.responses.get(resp_id)

    def assist(self, hass, assistant_id, device_id=None, lang=DEFAULT_LANG, html_out=False, message=None, audio_in=None, is_new_conversation=True, silence):
        # setup state

        credentials = get_creds(hass, assistant_id)
        config = hass.data[DOMAIN].get(assistant_id)
        if assistant_id not in self.conversation_states:
            self.conversation_states[assistant_id] = None
        
        # check and setup device_id

        if not self.known_devices or (device_id and device_id not in self.known_devices):
            session = AuthorizedSession(credentials)
            self.known_devices = [x['id'] for x in get_devices(session, config[DATA_PROJECT_ID]) if x['modelId'] == config[DATA_DEVICE]['device_model_id']]
            if config[DATA_DEVICE]['device_id'] not in self.known_devices:
                try:
                    register_device(session, config[DATA_PROJECT_ID], config[DATA_DEVICE]['device_model_id'], config[DATA_DEVICE]['device_id'])
                except e:
                    if not device_id:
                        _LOGGER.error('Default device_id is no longer valid and could not be registered. Try again or re-setup the integration.')
                    else:
                        _LOGGER.warn('Default device_id is no longer valid. Only requests with an explicit id will succeed.')

        if device_id and device_id not in self.known_devices:
            session = AuthorizedSession(credentials)
            try:
                register_device(session, config[DATA_PROJECT_ID], config[DATA_DEVICE]['device_model_id'], device_id)
            except e:
                _LOGGER.error("Cannot make assistant requests for unregistered device")
                return

        # check arguments

        if not message and not audio_in:
            _LOGGER.error("You need to provide either a textual or audio input to the assistant")
            return       

        # establish connection

        http_request = Request()
        channel = secure_authorized_channel(
            credentials, http_request, ASSISTANT_API_ENDPOINT)
        assistant = EmbeddedAssistantStub(channel)

        recording = True

        # Send requests
        
        device_id = device_id if device_id else config[DATA_DEVICE]['device_id']

        def iter_requests():
            conf = {
                'audio_out_config': AudioOutConfig(
                    encoding='MP3',
                    sample_rate_hertz=24000,
                    volume_percentage=100,
                ),
                'dialog_state_in': DialogStateIn(
                    language_code=lang,
                    conversation_state=self.conversation_states[assistant_id],
                    is_new_conversation=is_new_conversation,
                ),
                'device_config': DeviceConfig(
                    device_id=device_id,
                    device_model_id=config[DATA_DEVICE]['device_model_id'],
                ),
                'screen_out_config': ScreenOutConfig(
                    screen_mode=ScreenOutConfig.PLAYING if html_out else ScreenOutConfig.OFF,
                )
            }
            if message:
                conf['text_query'] = message
            elif audio_in:
                conf['audio_in_config'] = AudioInConfig(
                    encoding='LINEAR16',
                    sample_rate_hertz=16000,
                )
                audio_in.open()
            assist_config = AssistConfig(**conf)
        
            yield AssistRequest(config=assist_config)

            if audio_in:
                while recording:
                    # Subsequent requests need audio data, but not config.
                    yield AssistRequest(audio_in=audio_in.read(3200))
                audio_in.close()

        audio_data = b''
        html_data = None
        text_data = None
        device_data = None
        text_recognition_data = None
        should_continue = False

        # handle responses

        resp_id = str(uuid.uuid4())
        for resp in assistant.Assist(iter_requests()):
            if resp.dialog_state_out.conversation_state:
                self.conversation_states[assistant_id] = resp.dialog_state_out.conversation_state
            if resp.event_type == AssistResponse.END_OF_UTTERANCE:
                recording = False
            if resp.speech_results:
                text_recognition_data = ' '.join(r.transcript for r in resp.speech_results)
            if resp.dialog_state_out.supplemental_display_text:
                text_data = resp.dialog_state_out.supplemental_display_text
            if len(resp.audio_out.audio_data) > 0:
                audio_data += resp.audio_out.audio_data
            if resp.screen_out.data:
                html_data = resp.screen_out.data
            if resp.device_action.device_request_json:
                device_data = json.loads(
                    resp.device_action.device_request_json
                )
            if resp.dialog_state_out.microphone_mode == DialogStateOut.DIALOG_FOLLOW_ON:
                should_continue = True

            if not message: 
                yield {
                    'resp_id': resp_id,
                    'done': False,
                    'language': lang,
                    'text_recognition_data': text_recognition_data,
                }
        
        # save result

        def write_tags(filename, data, provider, message, language):
            """Write ID3 tags to file.
            Async friendly.
            """

            data_bytes = io.BytesIO(data)
            data_bytes.name = filename
            data_bytes.seek(0)

            album = provider
            artist = language

            try:
                tts_file = mutagen.File(data_bytes, easy=True)
                if tts_file is not None:
                    tts_file["artist"] = artist
                    tts_file["album"] = album
                    tts_file["title"] = message
                    tts_file.save(data_bytes)
            except mutagen.MutagenError as err:
                _LOGGER.error("ID3 tag error: %s", err)

            if silence > 0:
                audio = AudioSegment.from_file(data_bytes, format='mp3')
                silence = AudioSegment.silence(duration=1000 * silence)
                final = silence + audio
                data_bytes = final.export(io.BytesIO())

            return data_bytes.getvalue()

        self.responses[resp_id] = {
            '_timestamp': time.time(),
            'text_data': text_data,
            'audio_data': write_tags(resp_id+'.mp3', audio_data, 'Google Assistant',
                message if message else text_recognition_data, lang),
            'html_data': html_data,
        }

        yield {
            'resp_id': resp_id,
            'done': True,
            'text_recognition_data': message if message else text_recognition_data,
            'text_data': text_data,
            'device_data': device_data,
            'device_id': device_id,
            'language': lang,
            'should_continue': should_continue
        }