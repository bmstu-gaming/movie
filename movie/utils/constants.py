CHECK = '\u2714'  # ✔ check mark
CROSS = '\u274c'  # ❌ cross mark

LOG_FILE = 'movie.log'
EQUALS = '===================='

MKV = '.mkv'
MP4 = '.mp4'
AVI = '.avi'
VIDEO = [MKV, MP4, AVI]

ASS = '.ass'
SRT = '.srt'
SUBTITLE = [ASS, SRT]

PNG = '.png'
JPG = '.jpg'
IMAGE = [PNG, JPG]

MKV_STREAMS = r'Stream #[0-9]*:([0-9]*)(\([a-z]*\))?: ([a-z,A-Z]*)'
MP4_STREAMS = r'Stream #[0-9]*:([0-9]*)\[[0-9]x[0-9]\](\([a-z]*\))?: ([a-z,A-Z]*)'
TITLE_STREAMS = r'Stream #[0-9]*:([0-9]*)(\([a-z]*\)): ([a-z,A-Z]*):(?<=[:]).*(?=[\n])\s+Metadata:\n\s+title\s+: (.*(?=[\n]))'

SUBTITLE_TYPE = 'Subtitle'
