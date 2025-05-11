CHECK = '\u2714'  # ✔ check mark
CROSS = '\u274c'  # ❌ cross mark
CONFIG_PATH = 'config.ini'

LOG_FILE = 'movie.log'

LOG_FUNCTION_START = '╔==================== {name} ====================╗'
LOG_FUNCTION_END =   '╚==================== {name} ====================╝'

MKV = '.mkv'
MP4 = '.mp4'
AVI = '.avi'
M4V = '.m4v'
VIDEO = [MKV, MP4, AVI, M4V]

ASS = '.ass'
SRT = '.srt'
SUBTITLE = [ASS, SRT]

PNG = '.png'
JPG = '.jpg'
JPEG = '.jpeg'
IMAGE = [PNG, JPG, JPEG]

AAC = '.aac'
FLAC = '.flac'
M4A = '.m4a'
MKA = '.mka'
MP3 = '.mp3'
OPUS = '.opus'
AUDIO = [AAC, FLAC, M4A, MKA, MP3, OPUS]

NAME_TEMPLATE_VERIFICATION_REGEX = r'^[^\/\\\:\*\?\"\<\>\|]+$'
STREAM = r'\[STREAM\](.*?)\[/STREAM\]'
SUBTITLE_GRAPHIC_REGEX = r'\{\\an\d*\}m'
SUBTITLE_TAGS_REGEX = r'{[^}]*}'

STREAM_TYPE_VIDEO = 'video'
STREAM_TYPE_AUDIO = 'audio'
STREAM_TYPE_SUBTITLE = 'subtitle'
