CHECK = '\u2714'  # ✔ check mark
CROSS = '\u274c'  # ❌ cross mark
CONFIG_PATH = 'config.ini'

LOG_FILE = 'movie.log'

LOG_FUNCTION_START = '╔==================== {name} ====================╗'
LOG_FUNCTION_END =   '╚==================== {name} ====================╝'

MKV = '.mkv'
MP4 = '.mp4'
AVI = '.avi'
VIDEO = [MKV, MP4, AVI]

ASS = '.ass'
SRT = '.srt'
SUBTITLE = [ASS, SRT]

PNG = '.png'
JPG = '.jpg'
JPEG = '.jpeg'
IMAGE = [PNG, JPG, JPEG]

NAME_TEMPLATE_VERIFICATION_REGEX = r'^[^\/\\\:\*\?\"\<\>\|]+$'
STREAM = r'\[STREAM\](.*?)\[/STREAM\]'

STREAM_TYPE_VIDEO = 'video'
STREAM_TYPE_AUDIO = 'audio'
STREAM_TYPE_SUBTITLE = 'subtitle'

ERROR_MESSAGE_FILE_IN_USE = (
    'Error accessing file {file_path}: '
    'the file is using by another process. '
    'Please close the program that is using the file.'
)
