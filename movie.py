import codecs
from datetime import datetime
from enum import Enum
import heapq
import logging
import json
import os
import subprocess
import pysubs2
import chardet
import random
import re
import string


logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG) # DEBUG INFO ERROR CRITICAL


CHECK='\u2714'  # ✔ check mark
CROSS='\u274c'  # ❌ cross mark
MKV_STREAMS = r'Stream #[0-9]*:([0-9]*)(\([a-z]*\))?: ([a-z,A-Z]*)'
MP4_STREAMS = r'Stream #[0-9]*:([0-9]*)\[[0-9]x[0-9]\](\([a-z]*\))?: ([a-z,A-Z]*)'
TITLE_STREAMS = r'Stream #[0-9]*:([0-9]*)(\([a-z]*\))?: ([a-z,A-Z]*):\s[a-z,A-Z, \(,\),0-9]+\n\s+Metadata:\n\s+title\s+:([a-z,A-Z,а-я,А-Я, ,-]+)'
SUBTITLE_TYPE = 'Subtitle'


class Movie(object):
    # __init__
    def __init__(self):
        self.__filename_prefix_generator__()
        pass


    # __verification_movies_path__
    def __verification_movies_path__(self):
        LOG.debug(f'{self.movies_path = }')
        if os.path.isdir(self.movies_path):
            LOG.info(f'MOVIES_PATH: \"{self.movies_path}\" {CHECK}')
            return True
        else:
            LOG.error(f'MOVIES_PATH: \"{self.movies_path}\" {CROSS}')
            return False


    # __verification_ffmpeg__
    def __verification_ffmpeg__(self):
        LOG.debug(f'{self.ffmpeg = }')
        cmd_exec = [self.ffmpeg, '-version']
        try:
            stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
        except Exception as e:
            LOG.error(f'\"{self.ffmpeg}\" not valid: {str(e)}')
            return False

        LOG.debug(f"{ stdout.args = }")
        LOG.debug(f"{ stdout.returncode = }")
        LOG.debug(f"{ stdout.stderr = }")
        LOG.debug(f"{ stdout.stdout = }")

        if stdout.returncode != 0:
            LOG.error(f'FFMPEG: \"{self.ffmpeg}\" {CROSS}')
            return False
        if "ffmpeg" in stdout.stdout:
            LOG.info(f'FFMPEG: \"{self.ffmpeg}\" {CHECK}')
        else:
            LOG.error(f'FFMPEG: \"{self.ffmpeg}\" {CROSS}')
            return False

        return True


    # __verification_base_template__
    def __verification_base_template__(self):
        LOG.debug(f'{self.base_template = }')
        if re.match(r"^[^\/\\\:\*\?\"\<\>\|]+$", self.base_template) is not None:
            LOG.info(f'BASE_TEMPLATE: \"{self.base_template}\" {CHECK}')
            return True
        else:
            LOG.error(f'BASE_TEMPLATE: \"{self.base_template}\" {CROSS}')
            return False


    # config_verification
    def config_verification(self):
        status = True
        with open('config.json') as config_json_file:
            config = json.load(config_json_file)
            try:
                self.ffmpeg = config["FFMPEG"]
                self.movies_path = config["MOVIES_PATH"]
                self.base_template = config["BASE_TEMPLATE"]
            except Exception as e:
                LOG.error(f'the configuration file is set incorrectly: {str(e)}')
                return False
        status = self.__verification_movies_path__()
        status = self.__verification_ffmpeg__()
        status = self.__verification_base_template__()

        return status


    # get_streams_and_log_file
    def get_streams_and_log_file(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                self.streams_pattern = MKV_STREAMS
                first_video = f
                break
            if file_extension == ".mp4":
                self.streams_pattern = MP4_STREAMS
                first_video = f
                break
        
        LOG.debug(f"{ first_video = }")
        video_path_source = os.path.join(self.movies_path, first_video)
        LOG.info(f"{ video_path_source = }")
        dt_string = datetime.now().strftime("%Y.%m.%d - %H.%M.%S")
        LOG.debug(f'{ dt_string = }')

        cmd_exec = [self.ffmpeg, '-i', video_path_source]
        stdout = subprocess.run(cmd_exec, capture_output=True, text=True, encoding="utf-8")
        LOG.debug(f"{ stdout.args = }")
        LOG.debug(f"{ stdout.returncode = }")
        LOG.debug(f"{ stdout.stderr = }")
        LOG.debug(f"{ stdout.stdout = }")
        log_data = stdout.stderr
        LOG.debug(f'{ log_data = }')

        log_file = f"{dt_string}-{first_video}.log"
        log_stderr = stdout.stderr.split('\n')
        with open(log_file, 'w', encoding="utf-8") as fp:
            for item in log_stderr:
                fp.write("%s\n" % item)
        LOG.info(f' info in: {log_file}')

        stream_pattern = re.compile(self.streams_pattern)
        streams = [
            {
                'stream': int(stream),
                'language': stream_lang,
                'type': stream_type
            }
            for stream, stream_lang, stream_type in stream_pattern.findall(log_data)
        ]

        stream_title_pattern = re.compile(TITLE_STREAMS)
        streams_title = [
            {
                'stream': int(stream),
                'language': stream_lang,
                'type': stream_type,
                'title': stream_title
            }
            for stream, stream_lang, stream_type, stream_title in stream_title_pattern.findall(log_data)
        ]
        for stream_title in streams_title:
            LOG.debug(f'{ stream_title = }')

        for stream in streams:
            stream['language'] = stream['language'][1:-1]
            LOG.debug(f"{ stream = }")
        LOG.debug(f'{ streams = }')
        media_streams = [stream for stream in streams if stream['type'] != 'Attachment']
        LOG.debug(f'{ media_streams = }')

        for idx in range(len(media_streams)):
            for st in streams_title:
                if ('stream', idx) in st.items():
                    media_streams[idx]['title'] = st['title']

        for media_stream in media_streams:
            LOG.info(f'{ media_stream = }')
        self.streams = media_streams


    # remove_video
    def remove_video(self, do_remove: bool):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                if self.filename_prefix in f:
                    LOG.debug(f"     {self.filename_prefix} video: {f}")
                else:
                    LOG.debug(f" non {self.filename_prefix} video: {f}")
                    non_template_video_path = os.path.join(self.movies_path, f)
                    LOG.info(f" removing: {non_template_video_path}")
                    if do_remove:
                        os.remove(non_template_video_path)


    # __filename_prefix_generator__
    def __filename_prefix_generator__(self, size=10, chars=string.ascii_uppercase + string.digits):
        self.filename_prefix = ''.join(random.choice(chars) for _ in range(size))


    # __get_first_subtitle_type_stream__
    def __get_first_subtitle_type_stream__(self, selected_streams: list[str]):
        for i in range(len(selected_streams)):
            for stream in self.streams:
                if ('stream', selected_streams[i]) in stream.items():
                    LOG.debug(f'{ stream = }')
                    if stream['type'] == SUBTITLE_TYPE:
                        return stream['stream']


    # selected_streams
    def selected_streams(self, selected_streams: list[str]):
        default_sub_stream = self.__get_first_subtitle_type_stream__(selected_streams)
        LOG.debug(f'{ default_sub_stream = }')

        streams_metadata = []
        for i, selected_stream in enumerate(selected_streams):
            for stream in self.streams:
                if ('stream', selected_stream) in stream.items():
                    LOG.debug(f'{ stream = }')
                    if selected_stream == default_sub_stream:
                        stream_metadata = [
                            '-map', f'0:{stream["stream"]}',
                            f'-disposition:{i}', 'default'
                        ]
                    else:
                        stream_metadata = [
                            '-map', f'0:{stream["stream"]}',
                        ]
                    LOG.debug(f'{ stream_metadata = }')
                    for elem in stream_metadata:
                        streams_metadata.append(elem)
        LOG.debug(f"{ streams_metadata = }")

        self.__run_ffmpeg__(streams_metadata)


    # set_default_and_language_streams
    def set_default_and_language_streams(self, streams_languages: dict):
        streams_metadata = []
        for i, key in enumerate(streams_languages):
            LOG.debug(f"{ i = }")
            LOG.debug(f"{ key = }")
            LOG.debug(f"{ streams_languages[key] = }")

            stream_metadata = [
                '-map', f'0:{key}',
                f'-metadata:s:{i}', f'language={streams_languages[key]}',
                f'-disposition:{i}', 'default'
            ]
            LOG.debug(f"{ stream_metadata = }")
            for elem in stream_metadata:
                streams_metadata.append(elem)
        LOG.debug(f"{ streams_metadata = }")

        self.__run_ffmpeg__(streams_metadata)


    # __run_ffmpeg__
    def __run_ffmpeg__(self, streams: list[str]):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                video_path_result = os.path.join(self.movies_path, f"{self.filename_prefix}-{f}")

                LOG.info(f"{ video_path_source = }")
                LOG.debug(f"{ video_path_result = }")

                cmd_exec = [self.ffmpeg,
                            '-i', video_path_source,
                            '-c', 'copy',
                            *streams,
                            video_path_result]
                LOG.debug(f"{ cmd_exec = }")
                stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
                LOG.debug(f"{ stdout.args = }")
                LOG.debug(f"{ stdout.returncode = }")
                LOG.debug(f"{ stdout.stderr = }")
                LOG.debug(f"{ stdout.stdout = }")


    # __is_series__
    def __is_series__(self):
        video_count = 0
        for _, f in enumerate(os.listdir(self.movies_path)):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv" or file_extension == ".mp4":
                video_count += 1
        LOG.debug(f'{ video_count = }')
        return video_count


    # __rename__
    def __rename__(self, file: str, template: str, idx: int, do_rename: bool):
        file_name, file_extension = os.path.splitext(file)
        new_file_name = template.format(episode_idx = idx)
        LOG.debug(f" old_file: {file_name}{file_extension}")
        LOG.info(f"  new_file: {new_file_name}{file_extension}")
        old_file = os.path.join(self.movies_path, file)
        new_file = os.path.join(self.movies_path, new_file_name + file_extension)
        if do_rename:
            os.rename(old_file, new_file)


    # rename_files
    def rename_files(self, do_rename: bool):
        isSeries = True
        if self.__is_series__() == 1:
            isSeries = False
            template_video = self.base_template
            template_sub = self.base_template + ".RUS"
            template_img = self.base_template
        LOG.debug(f'{ isSeries = }')

        base_idx = 1
        subtitle_idx = base_idx
        video_idx = base_idx
        picture_idx = base_idx
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            
            if file_extension == ".mkv" or file_extension == ".mp4":
                if isSeries:
                    template_video = self.base_template + ".E{episode_idx:02d}"

                self.__rename__(file=f, template=template_video, idx=video_idx, do_rename=do_rename)
                video_idx += 1
            if file_extension == ".ass" or file_extension == ".srt":
                if isSeries:
                    template_sub = self.base_template + ".E{episode_idx:02d}.RUS"

                self.__rename__(file=f, template=template_sub, idx=subtitle_idx, do_rename=do_rename)
                subtitle_idx += 1
            if file_extension == ".png" or file_extension == ".jpg":
                if isSeries:
                    template_img = self.base_template + ".E{episode_idx:02d}"

                self.__rename__(file=f, template=template_img, idx=picture_idx, do_rename=do_rename)
                picture_idx += 1


    # subs_convert_srt_to_ass
    def subs_convert_srt_to_ass(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            filename, file_extension = os.path.splitext(f)
            if file_extension == ".srt":
                sub_path_source = os.path.join(self.movies_path, f)
                LOG.info(f"{filename} -> .ass")
                with open(sub_path_source, 'rb') as f:
                    result = chardet.detect(f.read())

                subs = pysubs2.load(sub_path_source, encoding=result["encoding"])
                sub_path_target = os.path.join(self.movies_path, f'{filename}.ass')
                subs.save(sub_path_target, encoding="utf-8")
                srt_subtitle = os.path.join(self.movies_path, filename+file_extension)
                LOG.debug(f" removing: {srt_subtitle}")
                os.remove(srt_subtitle)


    # __get_max_occur_styles__
    def __get_max_occur_styles__(self, file: str, max_styles=5, log_info=False):
        lines = []
        sub_path_source = os.path.join(self.movies_path, file)
        with codecs.open(sub_path_source, "r", "utf_8_sig") as file_sub:
            LOG.info(f" Sub: {sub_path_source}")
            lines = file_sub.readlines()

        words = []
        for _, line in enumerate(lines):
            if line.startswith("Style: "):
                styleSettingsList = line[7:].split(",")
                words.append(styleSettingsList[0])
        LOG.debug(f"{ words = }")

        sub_file = codecs.open(sub_path_source, "r", "utf_8_sig")
        sub_data = sub_file.read()
        occ = {}
        for style in words:
            occurrences = sub_data.count(style)
            occ[style] = occurrences
        LOG.debug(f"{ occ = }")

        styleWithMaxOccurrences = heapq.nlargest(max_styles, occ, key=occ.get)
        sorted_occ = sorted(occ.items(), key=lambda x:x[1], reverse=True)
        sorted_occ_dict = dict(sorted_occ)
        if log_info:
            for key in sorted_occ_dict:
                LOG.info(f" {key}: {sorted_occ_dict[key]}")
        LOG.debug(f"{ styleWithMaxOccurrences = }")
        return styleWithMaxOccurrences, lines


    # get_sub_info
    def get_sub_info(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".ass":
                first_subtitle = f
                LOG.debug(f"{ first_subtitle = }")
                self.__get_max_occur_styles__(file=f, log_info=True)
                return
        LOG.info(' There is no .ass subtitles in folder ')


    # extract_subtitle
    def extract_subtitle(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            filename, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                subtitle_path_result = os.path.join(self.movies_path, filename+".srt")
                LOG.debug(f"{ video_path_source = }")
                LOG.info(f"{ subtitle_path_result = }")
                cmd_exec = [self.ffmpeg,
                            '-i', video_path_source,
                            '-map', '0:s:0',
                            subtitle_path_result]
                LOG.debug(f"{ cmd_exec = }")
                stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
                LOG.debug(f"{ stdout.args = }")
                LOG.debug(f"{ stdout.returncode = }")
                LOG.debug(f"{ stdout.stderr = }")
                LOG.debug(f"{ stdout.stdout = }")


    # change_subs_styles_ass
    def change_subs_styles_ass(self, max_styles: int, do_change: bool):
        """
        the subtitles that occur most times are considered the main subtitles of the dialogue
        """
        class StyleFormat(Enum):
            Name = 0
            Fontname = 1
            Fontsize = 2
            PrimaryColour = 3
            SecondaryColour = 4
            OutlineColour = 5
            BackColour = 6
            Bold = 7
            Italic = 8
            Underline = 9
            StrikeOut = 10
            ScaleX = 11
            ScaleY = 12
            Spacing = 13
            Angle = 14
            BorderStyle = 15
            Outline = 16
            Shadow = 17
            Alignment = 18
            MarginL = 19
            MarginR = 20
            MarginV = 21
            Encoding = 22

        dialogue_style = {
            StyleFormat.Fontname: "Arial",
            StyleFormat.Fontsize: "14",
            StyleFormat.PrimaryColour: "&H00FFFFFF",
            StyleFormat.SecondaryColour: "&H00000000",
            StyleFormat.OutlineColour: "&H00000000",
            StyleFormat.BackColour: "&H00000000",
            StyleFormat.Bold: "-1",
            StyleFormat.Italic: "0",
            StyleFormat.Underline: "0",
            StyleFormat.Outline: "1",
            StyleFormat.Shadow: "0"
        }

        LOG.info(f"Sub template ")
        LOG.info([f"{k.name}: {dialogue_style[k]}" for k in dialogue_style])
        
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".ass":            
                styleWithMaxOccurrences, lines = self.__get_max_occur_styles__(file=f, max_styles=max_styles)
                sub_path_source = os.path.join(self.movies_path, f)
                if do_change:
                    with codecs.open(sub_path_source, "r+", "utf_8_sig") as file_sub:
                        for _, line in enumerate(lines):
                            if line.startswith("Style: "):
                                styleSettingsList = line[7:].split(",")
                                if styleSettingsList[0] in styleWithMaxOccurrences:
                                    for key in dialogue_style:
                                        styleSettingsList[key.value] = dialogue_style[key]
                                styleStr = f"Style: " + ','.join(styleSettingsList)
                                LOG.debug(f"{styleStr}")
                                file_sub.write(f"{styleStr}")
                            else:
                                file_sub.write(line)

########################

def run():
    movie = Movie()
    if movie.config_verification():
        LOG.info(f'config.json {CHECK}')
    else:
        LOG.error(f'config.json {CROSS}')
        return

    movie.get_streams_and_log_file()

    # first selected audio/subtitles - default
    # selected_streams = [0, 4, 8]
    # movie.selected_streams(selected_streams=selected_streams)
    # movie.remove_video(do_remove=True)

    # streams_languages = {0: 'eng', 4: 'eng', 8: 'eng'}
    # movie.set_default_and_language_streams(streams_languages=streams_languages)
    # movie.remove_video(do_remove=True)
    # movie.remove_video(do_remove=False)

    # movie.get_sub_info()
    # movie.extract_subtitle()
    # movie.subs_convert_srt_to_ass()
    # movie.change_subs_styles_ass(max_styles=3, do_change=True)

    # movie.rename_files(do_rename=False)


if __name__ == "__main__":
    run()

