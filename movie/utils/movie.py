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

from movie.utils import constants

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)  # DEBUG INFO ERROR CRITICAL


class Movie(object):
    # __init__
    def __init__(self):
        self.__filename_prefix_generator__()
        pass


    # __verification_movies_path__
    def __verification_movies_path__(self):
        LOG.debug(f'{self.movies_path = }')
        if os.path.isdir(self.movies_path):
            LOG.info(f'MOVIES_PATH: "{self.movies_path}" {constants.CHECK}')
            return True
        else:
            LOG.error(f'MOVIES_PATH: "{self.movies_path}" {constants.CROSS}')
            return False


    # __verification_ffmpeg__
    def __verification_ffmpeg__(self):
        LOG.debug(f'{self.ffmpeg = }')
        cmd_exec = [self.ffmpeg, '-version']
        try:
            stdout = self.__command_execution__(cmd_exec)
        except Exception as e:
            LOG.error(f'"{self.ffmpeg}" not valid: {str(e)}')
            return False

        if stdout.returncode != 0:
            LOG.error(f'FFMPEG: "{self.ffmpeg}" {constants.CROSS}')
            return False
        if "ffmpeg" in stdout.stdout:
            LOG.info(f'FFMPEG: "{self.ffmpeg}" {constants.CHECK}')
        else:
            LOG.error(f'FFMPEG: "{self.ffmpeg}" {constants.CROSS}')
            return False

        return True


    # __verification_base_template__
    def __verification_base_template__(self):
        LOG.debug(f'{self.base_template = }')
        if re.match(r"^[^\/\\\:\*\?\"\<\>\|]+$", self.base_template) is not None:
            LOG.info(f'BASE_TEMPLATE: "{self.base_template}" {constants.CHECK}')
            return True
        else:
            LOG.error(f'BASE_TEMPLATE: "{self.base_template}" {constants.CROSS}')
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
                self.streams_pattern = constants.MKV_STREAMS
                first_video = f
                break
            if file_extension == ".mp4":
                self.streams_pattern = constants.MP4_STREAMS
                first_video = f
                break

        LOG.debug(f'{ first_video = }')
        video_path_source = os.path.join(self.movies_path, first_video)
        LOG.info(f'{ video_path_source = }')
        dt_string = datetime.now().strftime('%Y.%m.%d - %H.%M.%S')
        LOG.debug(f'{ dt_string = }')

        cmd_exec = [self.ffmpeg, '-i', video_path_source]
        stdout = self.__command_execution__(command=cmd_exec)
        log_data = stdout.stderr

        logs_folder = "logs"
        isExist = os.path.exists(logs_folder)
        if not isExist:
            os.makedirs(logs_folder)

        log_file = f'{dt_string}-{first_video}.log'
        log_stderr = stdout.stderr.split('\n')
        log_path = os.path.join(logs_folder, log_file)

        with open(log_path, "w", encoding='utf-8') as fp:
            for item in log_stderr:
                fp.write("%s\n" % item)
        LOG.info(f' info in: {log_path}')

        stream_pattern = re.compile(self.streams_pattern)
        streams = [
            {
                'stream': int(stream),
                'language': stream_lang,
                'type': stream_type
            }
            for stream, stream_lang, stream_type in stream_pattern.findall(log_data)
        ]
        for stream in streams:
            stream['language'] = stream['language'][1:-1]
            LOG.debug(f'{ stream = }')

        stream_title_pattern = re.compile(constants.TITLE_STREAMS)
        extended_streams = [
            {
                'stream': int(stream),
                'language': stream_lang,
                'type': stream_type,
                'title': stream_title
            }
            for stream, stream_lang, stream_type, stream_title in stream_title_pattern.findall(log_data)
        ]
        for extended_stream in extended_streams:
            LOG.debug(f'{ extended_stream = }')       

        media_streams = [stream for stream in streams if stream['type'] != 'Attachment']
        for media_stream in media_streams:
            LOG.debug(f'{ media_stream = }')

        for idx in range(len(media_streams)):
            for extended_stream in extended_streams:
                if ('stream', idx) in extended_stream.items():
                    media_streams[idx]['title'] = extended_stream['title']

        for media_stream in media_streams:
            LOG.info(f'{ media_stream = }')
        self.streams = media_streams


    # remove_video
    def remove_video(self, do_remove: bool):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                if self.filename_prefix in f:
                    LOG.debug(f'     {self.filename_prefix} video: {f}')
                else:
                    LOG.debug(f' non {self.filename_prefix} video: {f}')
                    non_template_video_path = os.path.join(self.movies_path, f)
                    LOG.info(f' removing: {non_template_video_path}')
                    if do_remove:
                        os.remove(non_template_video_path)


    # __filename_prefix_generator__
    def __filename_prefix_generator__(self, size=10, chars=string.ascii_uppercase + string.digits):
        self.filename_prefix = "".join(random.choice(chars) for _ in range(size))


    # __get_first_subtitle_type_stream__
    def __get_first_subtitle_type_stream__(self, selected_streams: list[str]):
        for i in range(len(selected_streams)):
            for stream in self.streams:
                if ('stream', selected_streams[i]) in stream.items():
                    LOG.debug(f'{ stream = }')
                    if stream['type'] == constants.SUBTITLE_TYPE:
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
                            f'-disposition:{i}', 'default',
                        ]
                    else:
                        stream_metadata = [
                            '-map', f'0:{stream["stream"]}',
                        ]
                    LOG.debug(f'{ stream_metadata = }')
                    for elem in stream_metadata:
                        streams_metadata.append(elem)
        LOG.debug(f'{ streams_metadata = }')

        self.__run_ffmpeg__(streams_metadata)


    # set_default_and_language_streams
    def set_default_and_language_streams(self, streams_languages: dict):
        streams_metadata = []
        for i, key in enumerate(streams_languages):
            LOG.debug(f'{ i = }')
            LOG.debug(f'{ key = }')
            LOG.debug(f'{ streams_languages[key] = }')

            stream_metadata = [
                '-map', f'0:{key}',
                f'-metadata:s:{i}', f'language={streams_languages[key]}',
                f'-disposition:{i}', 'default'
            ]
            LOG.debug(f'{ stream_metadata = }')
            for elem in stream_metadata:
                streams_metadata.append(elem)
        LOG.debug(f'{ streams_metadata = }')

        self.__run_ffmpeg__(streams_metadata)


    # __run_ffmpeg__
    def __run_ffmpeg__(self, streams: list[str]):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                video_path_result = os.path.join(self.movies_path, f'{self.filename_prefix}-{f}')

                LOG.info(f'{ video_path_source = }')
                LOG.debug(f'{ video_path_result = }')

                cmd_exec = [
                    self.ffmpeg,
                    '-i', video_path_source,
                    '-c', 'copy',
                    *streams,
                    video_path_result
                ]
                LOG.debug(f'{ cmd_exec = }')
                self.__command_execution__(command=cmd_exec)


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
        new_file_name = template.format(episode_idx=idx)
        LOG.debug(f' old_file: {file_name}{file_extension}')
        LOG.info(f'  new_file: {new_file_name}{file_extension}')
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
                LOG.info(f'{filename} -> .ass')

                sub_path_source = os.path.join(self.movies_path, f)
                sub_path_target = os.path.join(self.movies_path, f'{filename}.ass')

                subs = pysubs2.load(sub_path_source, encoding=self.__get_file_encoding__(sub_path_source))
                subs.save(sub_path_target, encoding='utf-8')
                srt_subtitle = os.path.join(self.movies_path, filename + file_extension)
                LOG.debug(f' removing: {srt_subtitle}')
                os.remove(srt_subtitle)


    def __get_styles__(self, file: str) -> dict:
        sub_path_source = os.path.join(self.movies_path, file)
        sub_styles = []
        style_regex = re.compile(constants.STYLE_SUB)
        with codecs.open(sub_path_source, "r", encoding=self.__get_file_encoding__(sub_path_source)) as file_sub:
            LOG.info(f' Sub: {sub_path_source}')
            for line in file_sub:
                if style_regex.match(line):
                    style_setting = line[7:].split(",")
                    sub_styles.append(style_setting[0])
        file_sub.close()
        LOG.debug(f'{ sub_styles = }')

        sub_file = codecs.open(sub_path_source, "r", encoding=self.__get_file_encoding__(sub_path_source))
        sub_data = sub_file.read()
        sub_file.close()

        style_occurrences = {}
        for style in sub_styles:
            occurrences = sub_data.count(style)
            style_occurrences[style] = occurrences
        sorted_style_occurrences = dict(sorted(style_occurrences.items(), key=lambda x: x[1], reverse=True))
        LOG.debug(f'{ sorted_style_occurrences = }')

        for key in sorted_style_occurrences:
            LOG.info(f' {key}: {sorted_style_occurrences[key]}')

        return sorted_style_occurrences


    # __get_max_occurrences_styles__
    def __get_max_occurrences_styles__(self, dict_styles: dict, max_styles=3) -> list[str]:
        styles_with_max_occurrences = heapq.nlargest(max_styles, dict_styles, key=dict_styles.get)
        LOG.debug(f'{ styles_with_max_occurrences = }')
        return styles_with_max_occurrences


    # get_sub_info
    def get_sub_info(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".ass":
                first_subtitle = f
                LOG.debug(f'{ first_subtitle = }')
                self._style_occurrences = self.__get_styles__(file=f)
                return
        LOG.info('There is no .ass subtitles in folder ')


    # extract_subtitle
    def extract_subtitle(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            filename, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                subtitle_path_result = os.path.join(self.movies_path, filename + ".srt")
                LOG.debug(f'{ video_path_source = }')
                LOG.info(f'{ subtitle_path_result = }')
                cmd_exec = [
                    self.ffmpeg,
                    '-i', video_path_source,
                    '-map', '0:s:0',
                    subtitle_path_result
                ]
                self.__command_execution__(command=cmd_exec)


    # change_subs_styles_ass
    def change_subs_styles_ass(self, max_styles: int):
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
            StyleFormat.Fontsize: "20",
            StyleFormat.PrimaryColour: "&H00FFFFFF",
            StyleFormat.SecondaryColour: "&H00000000",
            StyleFormat.OutlineColour: "&H00000000",
            StyleFormat.BackColour: "&H00000000",
            StyleFormat.Bold: "-1",
            StyleFormat.Italic: "0",
            StyleFormat.Underline: "0",
            StyleFormat.Outline: "1",
            StyleFormat.Shadow: "0",
        }

        LOG.info("Sub template ")
        LOG.info([f'{k.name}: {dialogue_style[k]}' for k in dialogue_style])

        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".ass":
                styles_with_max_occurrences = self.__get_max_occurrences_styles__(
                    dict_styles=self._style_occurrences, max_styles=max_styles)

                style_regex = re.compile(constants.STYLE_SUB)
                sub_path_source = os.path.join(self.movies_path, f)
                with codecs.open(sub_path_source, mode="r", encoding=self.__get_file_encoding__(sub_path_source)) as file_sub:
                    new_sub_lines = []
                    for line in file_sub:
                        if style_regex.match(line):
                            style_setting = line[7:].split(",")
                            if style_setting[0] in styles_with_max_occurrences:
                                for key in dialogue_style:
                                    style_setting[key.value] = dialogue_style[key]
                                line = "Style: " + ",".join(style_setting)
                                LOG.debug(f'{line}')
                        new_sub_lines.append(line)
                file_sub.close()

                with codecs.open(sub_path_source, mode="w", encoding=self.__get_file_encoding__(sub_path_source)) as file_sub:
                    file_sub.writelines(new_sub_lines)
                file_sub.close()


    # __command_execution__
    def __command_execution__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        LOG.debug("__command_execution__")
        LOG.debug(f'{ command = }')
        stdout = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        LOG.debug(f'{ stdout.args = }')
        LOG.debug(f'{ stdout.returncode = }')
        LOG.debug(f'{ stdout.stderr = }')
        LOG.debug(f'{ stdout.stdout = }')
        return stdout


    def __get_file_encoding__(self, file: str) -> str:
        with open(file, 'rb') as f:
            result = chardet.detect(f.read())
        f.close()
        return result["encoding"]
