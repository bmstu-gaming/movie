CHECK = "\u2714"  # ✔ check mark
CROSS = "\u274c"  # ❌ cross mark
MKV_STREAMS = r"Stream #[0-9]*:([0-9]*)(\([a-z]*\))?: ([a-z,A-Z]*)"
MP4_STREAMS = r"Stream #[0-9]*:([0-9]*)\[[0-9]x[0-9]\](\([a-z]*\))?: ([a-z,A-Z]*)"
TITLE_STREAMS = r"Stream #[0-9]*:([0-9]*)(\([a-z]*\)): ([a-z,A-Z]*):(?<=[:]).*(?=[\n])\s+Metadata:\n\s+title\s+: (.*(?=[\n]))"
SUBTITLE_TYPE = "Subtitle"
STYLE_SUB = "Style: "
