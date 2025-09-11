import re
from typing import List

from movie.utils import constants

class Stream:
    def __init__(self, stream_data):
        self.index = None
        self._codec_type = None
        self.tags = {}
        self.codec_name = None

        for line in stream_data.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key == 'index':
                    self.index = int(value)
                elif key == 'codec_type':
                    self._codec_type = str(value)
                elif key.startswith('TAG:'):
                    tag_key = key[4:]
                    self.tags[tag_key] = value
                elif key == 'codec_name':
                    self.codec_name = value

    def __repr__(self):
        title = self.tags.get('title', f'Track {self.index}')
        return f'{self.index}: ({self.tags.get("language")}) {title}'

    @property
    def stream_type(self):
        return self._codec_type


def parse_ffprobe_output(output: str) -> List[Stream]:
    stream_blocks = re.findall(constants.STREAM, output, re.DOTALL)

    streams = []
    for block in stream_blocks:
        streams.append(Stream(block))

    return streams


def filter_media_streams(streams: List[Stream]) -> List[Stream]:
    return [stream for stream in streams if stream.stream_type in ['video', 'audio', 'subtitle']]
