import codecs
import collections
from datetime import datetime
import os
import re
from typing import List
from typing import Tuple
from typing import Union

import ass
import chardet
import deep_translator
from PIL import Image, ImageDraw, ImageFont
import pysubs2

from movie.utils import command
from movie.utils import constants
from movie.utils import generator
from movie.utils import files
from movie.utils.logging_config import LOG
from movie.utils import stream


class Movie():
    ffmpeg_path: str
    ffprobe_path: str
    movies_folder: str
    name_template: str
    streams: List[stream.Stream]

    def __init__(self, ffmpeg_path: str, ffprobe_path: str, movies_folder: str, name_template: str) -> None:
        self._filename_prefix = generator.get_filename_prefix()
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.movies_folder = movies_folder
        self.name_template = name_template
        self.streams = None

    def __set_streams__(self, stdout: str) -> None:
        streams = stream.parse_ffprobe_output(stdout)
        media_streams = stream.filter_media_streams(streams)
        LOG.debug(f'{media_streams = }')
        self.streams = media_streams

    def __get_video_streams_and_log_file__(self, video: str):
        vid_path_source = os.path.join(self.movies_folder, video)
        LOG.debug(f'{vid_path_source = }')
        dt_string = datetime.now().strftime('%Y.%m.%d - %H.%M.%S')
        LOG.debug(f'{dt_string = }')

        cmd_exec = [self.ffprobe_path, '-show_streams', vid_path_source]
        stdout = command.execute(cmd_exec)
        log_data = str("")
        if stdout.stderr is not None:
            LOG.debug('stdout.stderr is not None')
            log_data = stdout.stderr
        elif stdout.stdout is not None:
            LOG.debug('stdout.stdout is not None')
            log_data = stdout.stdout

        logs_folder = 'logs'
        is_exist = os.path.exists(logs_folder)
        if not is_exist:
            os.makedirs(logs_folder)

        log_file = f'{dt_string}-{video}.log'
        log_info = log_data.split('\n')
        log_path_target = os.path.join(logs_folder, log_file)

        with open(log_path_target, 'w', encoding='utf-8') as fp:
            for item in log_info:
                fp.write(f'{item}\n')
        LOG.info(f'info in: {log_path_target}')

        self.__set_streams__(stdout.stdout)

        return log_path_target

    def __get_first_video_in_directory__(self) -> Union[str, None]:
        video_files = self.__get_video_files__()
        return video_files[0] if video_files else None

    def get_streams_and_log_file(self) -> str:
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'STREAMS AND LOG FILE'))
        first_video = self.__get_first_video_in_directory__()
        LOG.debug(f'{first_video = }')
        if first_video is None:
            return None
        return self.__get_video_streams_and_log_file__(first_video)

    def __get_first_stream_of_type__(self,  selected_streams: List[int], stream_type: str) -> int:
        stream_indices = {stream.index for stream in self.streams}
        LOG.debug(f'{stream_type = }')
        for selected_stream in selected_streams:
            if selected_stream in stream_indices:
                corresponding_stream = next(stream for stream in self.streams if stream.index == selected_stream)
                LOG.debug(f'{corresponding_stream} - {corresponding_stream.stream_type}')
                if corresponding_stream.stream_type == stream_type:
                    return selected_stream
        return None

    def __get_default_streams__(self, selected_streams: List[int]) -> List[int]:
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'GET DEFAULT SELECTED STREAMS'))

        LOG.debug(f'{selected_streams = }')
        default_streams = []
        default_stream_video = self.__get_first_stream_of_type__(selected_streams, constants.STREAM_TYPE_VIDEO)
        default_stream_audio = self.__get_first_stream_of_type__(selected_streams, constants.STREAM_TYPE_AUDIO)
        default_stream_subtitle = self.__get_first_stream_of_type__(selected_streams, constants.STREAM_TYPE_SUBTITLE)
        default_streams = [default_stream_video, default_stream_audio, default_stream_subtitle]

        LOG.debug(f'default stream {constants.STREAM_TYPE_VIDEO}: {default_stream_video}')
        LOG.debug(f'default stream {constants.STREAM_TYPE_AUDIO}: {default_stream_audio}')
        LOG.debug(f'default stream {constants.STREAM_TYPE_SUBTITLE}: {default_stream_subtitle}')
        LOG.debug(f'{default_streams = }')

        LOG.debug(constants.LOG_FUNCTION_END.format(name = 'GET DEFAULT SELECTED STREAMS'))
        return default_streams

    def process_streams(self, selected_streams: List[int]):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'PROCESS STREAMS'))
        LOG.debug(f'{selected_streams = }')

        default_streams = self.__get_default_streams__(selected_streams)
        streams_metadata = []
        stream_indices = {stream.index for stream in self.streams}
        for i, selected_stream in enumerate(selected_streams):
            LOG.debug(f'{selected_stream = }')
            if selected_stream in stream_indices:
                stream_metadata = [
                    '-map', f'0:{selected_stream}', f'-disposition:{i}'
                ]
                if selected_stream in default_streams:
                    stream_metadata.extend(
                        ['default']
                    )
                else:
                    stream_metadata.extend(
                        ['0']
                    )

                LOG.debug(f'{stream_metadata = }')
                streams_metadata.extend(stream_metadata)
        LOG.debug(f'{streams_metadata = }')

        video_files = self.__get_video_files__()
        LOG.debug(f'{video_files = }')

        self.exec_command_for_files(video_files, streams_metadata)

    def process_streams_with_language(self, streams_languages: dict):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'PROCESS STREAMS WITH LANGUAGE'))
        LOG.debug(f'{streams_languages = }')

        default_streams = self.__get_default_streams__(list(streams_languages.keys()))

        streams_metadata = []
        for i, key in enumerate(streams_languages):
            LOG.debug(f'{i = }')
            LOG.debug(f'{key = }')
            LOG.debug(f'{streams_languages[key] = }')
            stream_metadata = [
                '-map', f'0:{key}',
                f'-metadata:s:{i}', f'language={streams_languages[key]}',
            ]
            if key in default_streams:
                stream_metadata.extend(
                    [f'-disposition:{i}', 'default',]
                )

            LOG.debug(f'{stream_metadata = }')
            streams_metadata.extend(stream_metadata)

        LOG.debug(f'{streams_metadata = }')
        video_files = self.__get_video_files__()
        LOG.debug(f'{video_files = }')

        self.exec_command_for_files(video_files, streams_metadata)

    def _natural_sort_key(self, s: str) -> list:
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        return [convert(c) for c in re.split('([0-9]+)', s)]

    def __get_files_by_type__(self, files_type) -> List[str]:
        multimedia_files = []
        for _, f in enumerate(os.listdir(self.movies_folder), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension in files_type:
                multimedia_files.append(f)
        multimedia_files.sort(key=self._natural_sort_key)
        return multimedia_files

    def __get_audio_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.AUDIO)

    def __get_video_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.VIDEO)

    def __get_subtitle_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.SUBTITLE)

    def __get_srt_subtitle_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.SUBTITLE)

    def __get_ass_subtitle_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.SUBTITLE)

    def __get_image_files__(self) -> List[str]:
        return self.__get_files_by_type__(constants.IMAGE)

    def extract_audio_from_video_files(self) -> None:
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'Remove default settings in external audio'))

        video_files = self.__get_video_files__()
        for f in video_files:
            LOG.info(f'{f}')
            file_name, _ = os.path.splitext(f)
            path_source = os.path.join(self.movies_folder, f)
            path_target = os.path.join(self.movies_folder, f'{file_name}{constants.AAC}')
            cmd_exec = [
                self.ffmpeg_path,
                '-i', path_source,
                '-vn',  '-acodec', 'copy',
                path_target
            ]
            LOG.debug(f'{cmd_exec = }')
            command.execute(cmd_exec)

        LOG.debug(constants.LOG_FUNCTION_END.format(name = 'Remove default settings in external audio'))

    def set_external_audio_non_default(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'Remove default settings in external audio'))

        audio_files = self.__get_audio_files__()
        LOG.debug(f'{audio_files = }')
        cmd_exec = ['-disposition:a:0', '0']

        self.exec_command_for_files(audio_files, cmd_exec)

        LOG.debug(constants.LOG_FUNCTION_END.format(name = 'Remove default settings in external audio'))

    def __separate_media_streams__(self) -> Tuple[List[stream.Stream], List[stream.Stream], List[stream.Stream]]:
        vid_list = [d for d in self.streams if d.stream_type == constants.STREAM_TYPE_VIDEO]
        aud_list = [d for d in self.streams if d.stream_type == constants.STREAM_TYPE_AUDIO]
        sub_list = [d for d in self.streams if d.stream_type == constants.STREAM_TYPE_SUBTITLE]
        return vid_list, aud_list, sub_list

    def exec_command_for_files(self, multimedia_files: List[str], command_exec: List[str]):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'Execution command for files'))
        for _, f in enumerate(multimedia_files):
            _, file_extension = os.path.splitext(f)
            path_source = os.path.join(self.movies_folder, f)
            path_target = os.path.join(self.movies_folder, f'{self._filename_prefix}{file_extension}')
            LOG.info(f'{f}')
            LOG.debug(f'{path_target = }')
            cmd_exec = [
                self.ffmpeg_path,
                '-i', path_source,
                '-c', 'copy',
                *command_exec,
                path_target
            ]
            LOG.debug(f'{cmd_exec = }')

            command.execute(cmd_exec)
            files.restoring_target_filename_to_source(path_target, path_source)

        LOG.debug(constants.LOG_FUNCTION_END.format(name = 'Execution command for files'))

    def __is_series__(self) -> int:
        video_files = self.__get_video_files__()
        video_count = len(video_files)
        LOG.debug(f'{video_count = }')
        return video_count

    def __rename__(self, file: str, template: str, idx: int):
        file_name, file_extension = os.path.splitext(file)
        new_file_name = template.format(episode_idx=idx)
        LOG.debug(f'old_file: {file_name}{file_extension}')
        LOG.debug(f'new_file: {new_file_name}{file_extension}')
        old_path = os.path.join(self.movies_folder, file)
        new_path = os.path.join(self.movies_folder, new_file_name + file_extension)

        files.rename(old_path, new_path)

    def rename_files(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'RENAMING FILES'))
        if self.__is_series__() == 1:
            template_vid = self.name_template
            template_sub = self.name_template + '.RUS'
            template_img = self.name_template
            template_aud = self.name_template
        else:
            template_vid = self.name_template + '.E{episode_idx:02d}'
            template_sub = self.name_template + '.E{episode_idx:02d}.RUS'
            template_img = self.name_template + '.E{episode_idx:02d}'
            template_aud = self.name_template + '.E{episode_idx:02d}.RUS'

        for idx, f in enumerate(self.__get_video_files__(), start=1):
            self.__rename__(f, template_vid, idx)
        for idx, f in enumerate(self.__get_audio_files__(), start=1):
            self.__rename__(f, template_aud, idx)
        for idx, f in enumerate(self.__get_subtitle_files__(), start=1):
            self.__rename__(f, template_sub, idx)
        for idx, f in enumerate(self.__get_image_files__(), start=1):
            self.__rename__(f, template_img, idx)

    def subs_convert_srt_to_ass(self):
        LOG.debug(
            constants.LOG_FUNCTION_START.format(
                name = f'convert {constants.STREAM_TYPE_SUBTITLE} {constants.SRT} -> {constants.ASS}')
        )
        for f in self.__get_srt_subtitle_files__():
            filename, file_extension = os.path.splitext(f)

            LOG.debug(f'{filename} -> .ass ')

            sub_path_source = os.path.join(self.movies_folder, f)
            sub_path_target = os.path.join(self.movies_folder, f'{filename}.ass')

            subs = pysubs2.load(sub_path_source, encoding=self.__get_file_encoding__(sub_path_source))
            subs.save(sub_path_target, encoding='utf-8')
            sub_srt_path = os.path.join(self.movies_folder, filename + file_extension)

            files.remove(sub_srt_path)
        LOG.debug(
            constants.LOG_FUNCTION_END.format(
                name = f'convert {constants.STREAM_TYPE_SUBTITLE} {constants.SRT} -> {constants.ASS}')
        )

    def __get_styles__(self, file: str) -> dict:
        sub_path_source = os.path.join(self.movies_folder, file)
        with codecs.open(
            sub_path_source, mode='r', encoding=self.__get_file_encoding__(sub_path_source)
        ) as sub_file_source:
            doc = ass.parse(sub_file_source)
            style_occurrences = {}
            for event in doc.events:
                if event.style in style_occurrences:
                    style_occurrences[event.style] += 1
                else:
                    style_occurrences[event.style] = 1
        sub_file_source.close()

        sorted_style_occurrences = dict(sorted(style_occurrences.items(), key=lambda x: x[1], reverse=True))
        LOG.debug(f'{sorted_style_occurrences = }')

        LOG.info(f"{file}: {', '.join(f'{k}: {v}' for k, v in sorted_style_occurrences.items())}")

        return sorted_style_occurrences

    def get_sub_info(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = f'{constants.ASS}-SUBTITLE INFO'))
        ass_sub_files = self.__get_ass_subtitle_files__()

        if not ass_sub_files:
            LOG.warning('There is no .ass subtitles in folder')
            return

        first_subtitle = ass_sub_files[0]
        LOG.debug(f'{first_subtitle = }')
        self.__get_styles__(first_subtitle)

    def __extract_subtitle__(self, vid_path_source: str, sub_path_target: str):
        cmd_exec = [
            self.ffmpeg_path,
            '-i', vid_path_source,
            '-map', '0:s:0',
            sub_path_target
        ]
        command.execute(cmd_exec)

    def extract_subtitle(self, keep_subtitles=False):
        LOG.debug(
            constants.LOG_FUNCTION_START.format(
                name = (f'EXTRACT {constants.STREAM_TYPE_SUBTITLE} FROM {constants.STREAM_TYPE_VIDEO}')
            )
        )
        for f in self.__get_video_files__():
            filename, file_extension = os.path.splitext(f)

            vid_path_source = os.path.join(self.movies_folder, f)
            sub_path_target = os.path.join(self.movies_folder, filename + constants.SRT)
            LOG.info(f'{f}')
            LOG.debug(f'{sub_path_target = }')

            self.__extract_subtitle__(vid_path_source, sub_path_target)

            if not keep_subtitles:
                vid_path_target = os.path.join(
                    self.movies_folder, f'{self._filename_prefix}.no_subs{file_extension}')
                LOG.debug(f'{vid_path_target = }')
                cmd_exec = [
                    self.ffmpeg_path,
                    '-i', vid_path_source,
                    '-map', '0', '-c', 'copy', '-sn',
                    vid_path_target
                ]
                command.execute(cmd_exec)
                files.restoring_target_filename_to_source(vid_path_target, vid_path_source)

    def __get_file_encoding__(self, file: str) -> str:
        with open(file, 'rb') as f:
            result = chardet.detect(f.read())
        f.close()
        return result['encoding']

    def __get_resized_preview_image__(self, image: str):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_folder, image)
        img = Image.open(img_path)

        original_width, original_height = img.size
        LOG.debug(f'source: {original_height}x{original_width}')

        target_width = 380
        target_heigth = int(original_height * (target_width / original_width))
        LOG.debug(f'target: {target_heigth}x{target_width}')

        resized_img = img.resize((target_width, target_heigth))
        img_resized_filename = f'{f_name}.resized{f_ext}'

        img_resized_path = os.path.join(self.movies_folder, img_resized_filename)
        resized_img.save(img_resized_path)

        img.close()

        files.remove(img_path)

        return img_resized_filename

    def __get_background_image__(self):
        img_bg = Image.new('RGB', (400, 600), color=(16, 16, 16))
        img_bg_filename = 'bg.jpg'
        img_bg_file_source = os.path.join(self.movies_folder, img_bg_filename)
        img_bg.save(img_bg_file_source)
        return img_bg_filename

    def __get_preview_with_background__(self, preview_image, background_image):
        preview_image_path = os.path.join(self.movies_folder, preview_image)
        img_preview = Image.open(preview_image_path)

        bg_image_path = os.path.join(self.movies_folder, background_image)
        img_bg = Image.open(bg_image_path)

        result = self.__create_combined_image__(img_preview, img_bg)
        img_preview_filename = self.__save_combined_image__(preview_image, result)

        img_preview.close()
        img_bg.close()

        files.remove(preview_image_path)
        files.remove(bg_image_path)

        return img_preview_filename

    def __create_combined_image__(self, img_preview, img_bg):
        preview_width, preview_height = img_preview.size
        bg_width, bg_height = img_bg.size

        center_x = bg_width // 2 - preview_width // 2
        center_y = bg_height // 2 - preview_height // 2

        result = Image.new('RGB', (bg_width, bg_height), color=(0, 0, 0))
        result.paste(img_bg, (0, 0))
        result.paste(img_preview, (center_x, center_y))

        return result

    def __save_combined_image__(self, preview_image, result):
        f_name, f_ext = os.path.splitext(preview_image)
        img_preview_filename = f'{f_name}.preview{f_ext}'
        img_preview_path = os.path.join(self.movies_folder, img_preview_filename)
        result.save(img_preview_path)

        return img_preview_filename

    def __copy_preview_image__(self, image):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_folder, image)
        image = Image.open(img_path)

        for i in range(1, self.__is_series__()+1):
            template = f_name + '.copy.{idx:02d}' + f_ext
            copy_filename = template.format(idx=i)
            LOG.debug(f'{copy_filename = }')
            copy_path = os.path.join(self.movies_folder, copy_filename)
            image.save(copy_path)
        image.close()

        files.remove(img_path)

    def __write_number__(self, image, number):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_folder, image)
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('impact.ttf', size=50)
        draw.text((0, 0), str(number), fill='yellow', font=font)

        img_target_filename = f'{f_name}-{number}{f_ext}'
        img_target_path = os.path.join(self.movies_folder, img_target_filename)
        img.save(img_target_path)

        img.close()

        files.remove(img_path)

    def preview_generate(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = 'PREVIEW GENERATE'))
        for f in self.__get_image_files__():
            LOG.debug(f'{f = }')
            img_file_resized = self.__get_resized_preview_image__(f)
            LOG.debug(f'{img_file_resized = }')
            img_bg_file = self.__get_background_image__()
            LOG.debug(f'{img_bg_file = }')
            img_preview = self.__get_preview_with_background__(img_file_resized, img_bg_file)
            LOG.debug(f'{img_preview = }')
            self.__copy_preview_image__(img_preview)

        if self.__is_series__() == 1:
            # for one video (film) there is no need to indicate the number
            return

        preview_idx = 1
        for f in self.__get_image_files__():
            LOG.debug(f'{f = }')
            LOG.debug(f'{preview_idx = }')
            self.__write_number__(f, preview_idx)
            preview_idx += 1

    def __subtitle_purification__(self, sub_path_source: str, sub_path_target: str, style_occurrences: dict):
        with codecs.open(
            sub_path_source, mode='r', encoding=self.__get_file_encoding__(sub_path_source)
        ) as sub_file_source:
            doc = ass.parse(sub_file_source)

            script_info_dict = {
                'WrapStyle': '0',
                'ScaledBorderAndShadow': 'yes',
                'Collisions': 'Normal',
                'ScriptType': 'v4.00+',
            }
            doc.info = ass.ScriptInfoSection('Script Info', collections.OrderedDict(script_info_dict))
            LOG.debug(f'{doc.info = }')

            main_subtitle = ass.line.Style(
                name='Main',
                fontname='Arial',
                fontsize=20.0,
                primary_color=ass.data.Color(r=0xff, g=0xff, b=0xff, a=0x00),
                secondary_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                outline_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                back_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                bold=True,
                italic=False,
                underline=False,
                strike_out=False,
                scale_x=100.0,
                scale_y=100.0,
                spacing=0.0,
                angle=0.0,
                border_style=1,
                outline=1.0,
                shadow=0.0,
                alignment=2,
                margin_l=0,
                margin_r=0,
                margin_v=10,
                encoding=0
            )
            signs_subtitle = ass.line.Style(
                name='Signs',
                fontname='Arial',
                fontsize=14.0,
                primary_color=ass.data.Color(r=0xff, g=0xff, b=0xff, a=0x00),
                secondary_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                outline_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                back_color=ass.data.Color(r=0x00, g=0x00, b=0x00, a=0x00),
                bold=False,
                italic=False,
                underline=False,
                strike_out=False,
                scale_x=100.0,
                scale_y=100.0,
                spacing=0.0,
                angle=0.0,
                border_style=1,
                outline=1.0,
                shadow=0.0,
                alignment=8,
                margin_l=0,
                margin_r=0,
                margin_v=10,
                encoding=0
            )
            subs = [main_subtitle, signs_subtitle]
            doc.styles = ass.section.StylesSection('V4+ Styles', subs)
            LOG.debug(f'{doc.styles = }')

            frequent_style = str(next(iter(style_occurrences)))
            LOG.debug(f'{frequent_style = }')

            set_signs_style_next_event = False
            for event in doc.events:
                clear_text = re.sub(constants.SUBTITLE_TAGS_REGEX, '', event.text).strip()

                if set_signs_style_next_event:
                    event.style = 'Signs'
                    set_signs_style_next_event = False

                if re.search(constants.SUBTITLE_GRAPHIC_REGEX, event.text):
                    event.text = ''
                    set_signs_style_next_event = True
                else:
                    event.text = clear_text

                if re.match(rf'^{frequent_style}', string=event.style):
                    event.style = 'Main'
                else:
                    event.style = 'Signs'

            with open(sub_path_target, 'w', encoding='utf_8_sig') as sub_file_target:
                doc.dump_file(sub_file_target)
            sub_file_target.close()
        sub_file_source.close()

        files.remove(sub_path_source)

    def ass_subtitle_purification(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = f'{constants.STREAM_TYPE_SUBTITLE} PURIFACATION'))
        for f in self.__get_ass_subtitle_files__():
            f_name, f_ext = os.path.splitext(f)
            sub_path_source = os.path.join(self.movies_folder, f)
            sub_path_target = os.path.join(self.movies_folder, f'{f_name}.PURE{f_ext}')
            LOG.debug(f'{sub_path_source = }')
            LOG.debug(f'{sub_path_target = }')
            styles_occurrences = self.__get_styles__(f)
            self.__subtitle_purification__(sub_path_source, sub_path_target, styles_occurrences)
        LOG.debug(constants.LOG_FUNCTION_END.format(name = f'{constants.STREAM_TYPE_SUBTITLE} PURIFACATION'))

    def __subtitle_translation__(self, sub_path_source, sub_path_target):
        with codecs.open(
            sub_path_source, mode='r', encoding=self.__get_file_encoding__(sub_path_source)
        ) as sub_file_source:
            doc = ass.parse(sub_file_source)
            for event in doc.events:
                clear_text = re.sub(r'{[^}]*}', '', event.text).strip()
                clear_text = clear_text.replace('\\N', ' \\N ')
                clear_text = deep_translator.GoogleTranslator(target='ru').translate(clear_text)

            with open(sub_path_target, 'w', encoding='utf_8_sig') as sub_file_target:
                doc.dump_file(sub_file_target)
            sub_file_target.close()
        sub_file_source.close()

        files.remove(sub_path_source)

    def ass_subtitle_translation(self):
        LOG.debug(constants.LOG_FUNCTION_START.format(name = f'{constants.STREAM_TYPE_SUBTITLE} TRANSLATION'))
        for f in self.__get_ass_subtitle_files__():
            f_name, f_ext = os.path.splitext(f)
            if f_ext == constants.ASS:
                sub_path_source = os.path.join(self.movies_folder, f)
                sub_path_target = os.path.join(self.movies_folder, f'{f_name}.translation-out{f_ext}')
                LOG.debug(f'{sub_path_source = }')
                LOG.debug(f'{sub_path_target = }')
                self.__subtitle_translation__(sub_path_source, sub_path_target)
        LOG.debug(constants.LOG_FUNCTION_END.format(name = f'{constants.STREAM_TYPE_SUBTITLE} TRANSLATION'))

    def func_in_progress(self) -> None:
        LOG.info('in progress')
