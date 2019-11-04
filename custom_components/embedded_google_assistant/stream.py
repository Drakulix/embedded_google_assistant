import logging
import wave

# import sounddevice as sd

_LOGGER = logging.getLogger(__name__)

DEFAULT_AUDIO_SAMPLE_RATE = 16000
DEFAULT_AUDIO_SAMPLE_WIDTH = 2
DEFAULT_AUDIO_ITER_SIZE = 3200
DEFAULT_AUDIO_DEVICE_BLOCK_SIZE = 6400
DEFAULT_AUDIO_DEVICE_FLUSH_SIZE = 25600

class WaveSource(object):
    """Audio source that reads audio data from a WAV file.
    Reads are throttled to emulate the given sample rate and silence
    is returned when the end of the file is reached.
    Args:
      fp: file-like stream object to read from.
      sample_rate: sample rate in hertz.
      sample_width: size of a single sample in bytes.
    """
    def __init__(self, path, sample_rate, sample_width):
        self._path = path
        self._sample_rate = sample_rate
        self._sample_width = sample_width
        self._sleep_until = 0

    def open(self):
        self._fp = open(self._path, 'r+b')
        try:
            self._wavep = wave.open(self._fp, 'r')
        except wave.Error as e:
            _LOGGER.warning('error opening WAV file: %s, '
                            'falling back to RAW format', e)
            self._fp.seek(0)
            self._wavep = None
        

    def read(self, size):
        """Read bytes from the stream and block until sample rate is achieved.
        Args:
          size: number of bytes to read from the stream.
        """
        now = time.time()
        missing_dt = self._sleep_until - now
        if missing_dt > 0:
            time.sleep(missing_dt)
        self._sleep_until = time.time() + self._sleep_time(size)
        data = (self._wavep.readframes(size)
                if self._wavep
                else self._fp.read(size))
        #  When reach end of audio stream, pad remainder with silence (zeros).
        if not data:
            return b'\x00' * size
        return data

    def close(self):
        """Close the underlying stream."""
        if self._wavep:
            self._wavep.close()
        self._fp.close()

    def _sleep_time(self, size):
        sample_count = size / float(self._sample_width)
        sample_rate_dt = sample_count / float(self._sample_rate)
        return sample_rate_dt

    @property
    def sample_rate(self):
        return self._sample_rate

'''
class SoundDeviceSource(object):
    """Audio source based on an underlying sound device.
    It can be used as an audio source (read).
    Args:
      sample_rate: sample rate in hertz.
      sample_width: size of a single sample in bytes.
      block_size: size in bytes of each read and write operation.
      flush_size: size in bytes of silence data written during flush operation.
    """
    def __init__(self, sample_rate, sample_width, block_size, flush_size):
        if sample_width == 2:
            audio_format = 'int16'
        else:
            raise Exception('unsupported sample width:', sample_width)
        self._audio_stream = sd.RawInputStream(
            samplerate=sample_rate, dtype=audio_format, channels=1,
            blocksize=int(block_size/2),  # blocksize is in number of frames.
        )
        self._block_size = block_size
        self._flush_size = flush_size
        self._sample_rate = sample_rate

    def read(self, size):
        """Read bytes from the stream."""
        buf, overflow = self._audio_stream.read(size)
        if overflow:
            _LOGGER.warning('SoundDeviceStream read overflow (%d, %d)',
                            size, len(buf))
        return bytes(buf)

    def close(self):
        """Close the underlying stream and audio interface."""
        if self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None

    @property
    def sample_rate(self):
        return self._sample_rate
'''

class SocketSource(object):
    """Audio source based on an underlying stream.
    It can be used as an audio source (read).
    Args:
      fp: file-like stream object to read from.
    """    
    def __init__(self, path):
        self._path = path
    
    def open(self):
        import socket
        self._fp = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._fp.connect(self._path)
    
    def read(self, size):
        """Read bytes from the stream."""
        buf = self._fp.recv(size)
        return bytes(buf)

    def close(self):
        """Close the underlying stream."""
        self._fp.close()

