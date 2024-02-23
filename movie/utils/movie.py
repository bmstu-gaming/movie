import ass
import codecs
import collections
from datetime import datetime
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import pysubs2
import chardet
import random
import re
import string

from movie.utils import constants
from movie.utils.logging_config import LOG


class Movie(object):
    def __init__(self):
        self.__filename_prefix_generator__()
        pass


    def __verification_movies_path__(self) -> bool:
        LOG.debug(f'{self.movies_path = }')
        if os.path.isdir(self.movies_path):
            LOG.info(f'MOVIES_PATH: "{self.movies_path}" {constants.CHECK}')
            return True
        else:
            LOG.error(f'MOVIES_PATH: "{self.movies_path}" {constants.CROSS}')
            return False


    def __verification_ffmpeg__(self) -> bool:
        LOG.debug(f'{self.ffmpeg = }')
        cmd_exec = [self.ffmpeg, '-version']
        try:
            stdout = self.__command_execution__(cmd_exec)
        except Exception as e:
            LOG.error(f'"{self.ffmpeg}" not valid: {str(e)}')
            LOG.error(f'FFMPEG: "{self.ffmpeg}" {constants.CROSS}')
            return False

        if stdout.returncode != 0:
            LOG.error(f'FFMPEG: "{self.ffmpeg}" {constants.CROSS}')
            return False
        elif "ffmpeg" in stdout.stdout:
            LOG.info(f'FFMPEG: "{self.ffmpeg}" {constants.CHECK}')
        else:
            LOG.error(f'FFMPEG: "{self.ffmpeg}" {constants.CROSS}')
            return False

        return True


    def __verification_base_template__(self) -> bool:
        LOG.debug(f'{self.base_template = }')
        if re.match(r'^[^\/\\\:\*\?\"\<\>\|]+$', self.base_template) is not None:
            LOG.info(f'BASE_TEMPLATE: "{self.base_template}" {constants.CHECK}')
            return True
        else:
            LOG.error(f'BASE_TEMPLATE: "{self.base_template}" {constants.CROSS}')
            return False


    def config_verification(self) -> bool:
        if self.__config_verification__():
            print(f'config.json {constants.CHECK}')
            return True
        else:
            print(f'config.json {constants.CROSS}')
            return False


    def __config_verification__(self) -> bool:
        LOG.info(f'{constants.EQUALS} CONFIG VERIFICATION {constants.EQUALS}')
        status = True
        with open('config.json') as config_json_file:
            config = json.load(config_json_file)
            try:
                self.ffmpeg = config['FFMPEG']
                self.movies_path = config['MOVIES_PATH']
                self.base_template = config['BASE_TEMPLATE']
            except Exception as e:
                LOG.error(f'the configuration file is set incorrectly: {str(e)}')
                return False
        status = self.__verification_ffmpeg__()
        status &= self.__verification_movies_path__()
        status &= self.__verification_base_template__()

        return status


    def __get_video_streams_and_log_file__(self, video: str):
        vid_path_source = os.path.join(self.movies_path, video)
        LOG.debug(f'{vid_path_source = }')
        dt_string = datetime.now().strftime('%Y.%m.%d - %H.%M.%S')
        LOG.debug(f'{dt_string = }')

        cmd_exec = [self.ffmpeg, '-i', vid_path_source]
        stdout = self.__command_execution__(command=cmd_exec)
        log_data = stdout.stderr

        logs_folder = 'logs'
        isExist = os.path.exists(logs_folder)
        if not isExist:
            os.makedirs(logs_folder)

        log_file = f'{dt_string}-{video}.log'
        log_stderr = stdout.stderr.split('\n')
        log_path_target = os.path.join(logs_folder, log_file)

        with open(log_path_target, 'w', encoding='utf-8') as fp:
            for item in log_stderr:
                fp.write('%s\n' % item)
        LOG.info(f'info in: {log_path_target}')

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
            LOG.debug(f'{stream = }')

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
            LOG.debug(f'{extended_stream = }')       

        media_streams = [stream for stream in streams if stream['type'] != 'Attachment']
        for media_stream in media_streams:
            LOG.debug(f'{media_stream = }')

        for idx in range(len(media_streams)):
            for extended_stream in extended_streams:
                if ('stream', idx) in extended_stream.items():
                    media_streams[idx]['title'] = extended_stream['title']

        for media_stream in media_streams:
            LOG.info(f'{media_stream = }')
        self.streams = media_streams

        return log_path_target


    def __get_first_video_in_directory__(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == constants.MKV or file_extension == constants.AVI:
                self.streams_pattern = constants.MKV_STREAMS
                return f
            if file_extension == constants.MP4:
                self.streams_pattern = constants.MP4_STREAMS
                return f

    def __notation_validation__(self, input_str: str) -> bool:
        numbers = set('0123456789')
        commas = set(',')
        hyphens = set('-')

        for char in input_str:
            if char not in numbers and char not in commas and char not in hyphens:
                return False
        return True


    def __notation_recognition__(self, input_str: str) -> list[int]:
        LOG.debug(f'{constants.EQUALS} notation recognition {constants.EQUALS}')
        LOG.debug(f'{input_str = }')

        numbers = []
        try:
            for num in input_str.split(','):
                if '-' in num:
                    start, end = num.split('-')
                    for i in range(int(start), int(end) + 1):
                        numbers.append(i)
                else:
                    numbers.append(int(num))
            for num in numbers:
                LOG.debug(f'{num = }')
            LOG.debug(f'{constants.EQUALS} notation recognition {constants.EQUALS}')
        except Exception as e:
            LOG.error(f'An error occurred: {e}')
        return numbers


    def get_streams_and_log_file(self):
        LOG.info(f'{constants.EQUALS} STREAMS AND LOG FILE {constants.EQUALS}')
        first_video = self.__get_first_video_in_directory__()
        LOG.debug(f'{first_video = }')
        return self.__get_video_streams_and_log_file__(first_video)


    def remove_video(self, do_remove=True):
        LOG.info(f'{constants.EQUALS} REMOVE VIDEO {constants.EQUALS}')
        LOG.debug(f'{self._filename_prefix = }')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension in constants.VIDEO:
                if self._filename_prefix in f:
                    LOG.debug(f'{self._filename_prefix} video: {f}')
                else:
                    LOG.debug(f'non {self._filename_prefix} video: {f}')
                    vid_non_template_path = os.path.join(self.movies_path, f)
                    if do_remove:
                        LOG.info(f'removing: {vid_non_template_path}')
                        os.remove(vid_non_template_path)


    def __filename_prefix_generator__(self, size=10, chars=string.ascii_uppercase + string.digits):
        self._filename_prefix = ''.join(random.choice(chars) for _ in range(size))


    def __get_first_subtitle_type_stream__(self, selected_streams: list[str]) -> str:
        for i in range(len(selected_streams)):
            for stream in self.streams:
                if ('stream', selected_streams[i]) in stream.items():
                    LOG.debug(f'{stream = }')
                    if stream['type'] == constants.SUBTITLE_TYPE:
                        return stream['stream']


    def selected_streams(self, selected_streams: list[str]):
        LOG.info(f'{constants.EQUALS} SELECTED STREAMS {constants.EQUALS}')
        sub_default_stream = self.__get_first_subtitle_type_stream__(selected_streams)
        LOG.debug(f'{sub_default_stream = }')

        streams_metadata = []
        for i, selected_stream in enumerate(selected_streams):
            for stream in self.streams:
                if ('stream', selected_stream) in stream.items():
                    LOG.debug(f'{stream = }')
                    if selected_stream == sub_default_stream:
                        stream_metadata = [
                            '-map', f'0:{stream["stream"]}',
                            f'-disposition:{i}', 'default',
                        ]
                    else:
                        stream_metadata = [
                            '-map', f'0:{stream["stream"]}',
                        ]
                    LOG.debug(f'{stream_metadata = }')
                    for elem in stream_metadata:
                        streams_metadata.append(elem)
        LOG.debug(f'{streams_metadata = }')
        self.__run_ffmpeg__(streams_metadata)


    def set_default_and_language_streams(self, streams_languages: dict):
        LOG.info(f'{constants.EQUALS} SET STREAMS LANGUAGE & DEFAULT')
        streams_metadata = []
        for i, key in enumerate(streams_languages):
            LOG.debug(f'{i = }')
            LOG.debug(f'{key = }')
            LOG.debug(f'{streams_languages[key] = }')

            stream_metadata = [
                '-map', f'0:{key}',
                f'-metadata:s:{i}', f'language={streams_languages[key]}',
                f'-disposition:{i}', 'default'
            ]
            LOG.debug(f'{stream_metadata = }')
            for elem in stream_metadata:
                streams_metadata.append(elem)
        LOG.debug(f'{streams_metadata = }')

        self.__run_ffmpeg__(streams_metadata)


    def __separate_media_streams__(self) -> tuple[list[dict], list[dict], list[dict]]:
        video_list = [d for d in self.streams if d['type'] == 'Video']
        audio_list = [d for d in self.streams if d['type'] == 'Audio']
        subtitle_list = [d for d in self.streams if d['type'] == 'Subtitle']
        return video_list, audio_list, subtitle_list


    def __run_ffmpeg__(self, streams: list[str]):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension in constants.VIDEO:
                vid_path_source = os.path.join(self.movies_path, f)
                vid_path_target = os.path.join(self.movies_path, f'{self._filename_prefix}-{f}')

                LOG.info(f'{vid_path_source = }')
                LOG.debug(f'{vid_path_target = }')

                print(f'folder: {self.movies_path}')
                print(f'{f} -> {self._filename_prefix}-{f}')

                cmd_exec = [
                    self.ffmpeg,
                    '-i', vid_path_source,
                    '-c', 'copy',
                    *streams,
                    vid_path_target
                ]
                LOG.debug(f'{cmd_exec = }')
                self.__command_execution__(command=cmd_exec)


    def __is_series__(self) -> int:
        video_count = 0
        for _, f in enumerate(os.listdir(self.movies_path)):
            _, file_extension = os.path.splitext(f)
            if file_extension in constants.VIDEO:
                video_count += 1
        LOG.debug(f'{video_count = }')
        return video_count


    def __rename__(self, file: str, template: str, idx: int, do_rename=True):
        file_name, file_extension = os.path.splitext(file)
        new_file_name = template.format(episode_idx=idx)
        LOG.debug(f'old_file: {file_name}{file_extension}')
        LOG.info(f'new_file: {new_file_name}{file_extension}')
        old_path = os.path.join(self.movies_path, file)
        new_path = os.path.join(self.movies_path, new_file_name + file_extension)
        if do_rename:
            os.rename(old_path, new_path)


    def rename_files(self, do_rename=True):
        LOG.info(f'{constants.EQUALS} RENAMING FILES {constants.EQUALS}')
        isSeries = True
        if self.__is_series__() == 1:
            isSeries = False
            template_vid = self.base_template
            template_sub = self.base_template + '.RUS'
            template_img = self.base_template
        LOG.debug(f'{isSeries = }')

        base_idx = 1
        sub_idx = base_idx
        vid_idx = base_idx
        img_idx = base_idx
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)

            if file_extension in constants.VIDEO:
                if isSeries:
                    template_vid = self.base_template + ".E{episode_idx:02d}"

                self.__rename__(f, template_vid, vid_idx, do_rename=do_rename)
                vid_idx += 1

            if file_extension in constants.SUBTITLE:
                if isSeries:
                    template_sub = self.base_template + ".E{episode_idx:02d}.RUS"

                self.__rename__(f, template_sub, sub_idx, do_rename=do_rename)
                sub_idx += 1

            if file_extension in constants.IMAGE:
                if isSeries:
                    template_img = self.base_template + ".E{episode_idx:02d}"

                self.__rename__(f, template_img, img_idx, do_rename=do_rename)
                img_idx += 1


    def subs_convert_srt_to_ass(self):
        LOG.info(f'{constants.EQUALS} convert {constants.SRT} -> {constants.ASS} SUBTITLE {constants.EQUALS}')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            filename, file_extension = os.path.splitext(f)
            if file_extension == constants.SRT:
                LOG.info(f'{filename} -> .ass ')

                sub_path_source = os.path.join(self.movies_path, f)
                sub_path_target = os.path.join(self.movies_path, f'{filename}.ass')

                subs = pysubs2.load(sub_path_source, encoding=self.__get_file_encoding__(sub_path_source))
                subs.save(sub_path_target, encoding='utf-8')
                sub_file_srt = os.path.join(self.movies_path, filename + file_extension)
                LOG.debug(f'removing: {sub_file_srt}')
                os.remove(sub_file_srt)


    def __get_styles__(self, file: str) -> dict:
        sub_path_source = os.path.join(self.movies_path, file)
        with codecs.open(sub_path_source, mode='r', encoding=self.__get_file_encoding__(sub_path_source)) as sub_file_source:
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

        for key in sorted_style_occurrences:
            LOG.info(f'{key}: {sorted_style_occurrences[key]}')
            print(f'{key}: {sorted_style_occurrences[key]}')

        return sorted_style_occurrences


    def get_sub_info(self):
        LOG.info(f'{constants.EQUALS} {constants.ASS}-SUBTITLE INFO {constants.EQUALS}')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == constants.ASS:
                first_subtitle = f
                LOG.debug(f'{first_subtitle = }')
                self.style_occurrences = self.__get_styles__(f)
                return
        LOG.info('There is no .ass subtitles in folder')
        print('There is no .ass subtitles in folder')


    def extract_subtitle(self, remove_subtitle=False):
        LOG.info(f'{constants.EQUALS} EXTRACT SUBTITLE FROM VIDEO {constants.EQUALS}')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            filename, file_extension = os.path.splitext(f)
            if file_extension in constants.VIDEO:
                vid_path_source = os.path.join(self.movies_path, f)
                sub_path_target = os.path.join(self.movies_path, filename + constants.SRT)
                LOG.debug(f'{vid_path_source = }')
                LOG.info(f'{sub_path_target = }')
                print(f'{sub_path_target = }')
                cmd_exec = [
                    self.ffmpeg,
                    '-i', vid_path_source,
                    '-map', '0:s:0',
                    sub_path_target
                ]
                self.__command_execution__(command=cmd_exec)
                if remove_subtitle:
                    vid_file_target = f'{filename}.no_subs{file_extension}'
                    vid_path_target = os.path.join(self.movies_path, vid_file_target)
                    LOG.debug(f'{vid_path_target = }')
                    cmd_exec = [
                        self.ffmpeg,
                        '-i', vid_path_source,
                        '-map', '0', '-c', 'copy', '-sn',
                        vid_path_target
                    ]
                    self.__command_execution__(command=cmd_exec)
                    LOG.debug(f'removing: {vid_path_source}')
                    os.remove(vid_path_source)


    def __command_execution__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        LOG.debug(f'{constants.EQUALS}\/ COMMAND \/{constants.EQUALS}')
        LOG.debug(f'{command = }')
        stdout = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        LOG.debug(f'{stdout.args = }')
        LOG.debug(f'{stdout.returncode = }')
        LOG.debug(f'{stdout.stderr = }')
        LOG.debug(f'{stdout.stdout = }')
        LOG.debug(f'{constants.EQUALS}/\ COMMAND /\{constants.EQUALS}')
        return stdout


    def __get_file_encoding__(self, file: str) -> str:
        with open(file, 'rb') as f:
            result = chardet.detect(f.read())
        f.close()
        return result['encoding']


    def __get_resized_preview_image__(self, image):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_path, image)
        img = Image.open(img_path)

        original_width, original_height = img.size
        LOG.debug(f'source: {original_height}x{original_width}')

        target_width = 380
        target_heigth = int(original_height * (target_width / original_width))
        LOG.debug(f'target: {target_heigth}x{target_width}')

        resized_img = img.resize((target_width, target_heigth))
        img_resized_filename = f'{f_name}.resized{f_ext}'

        img_resized_path = os.path.join(self.movies_path, img_resized_filename)
        resized_img.save(img_resized_path)

        img.close()
        LOG.info(f'removing: {img_path}')
        os.remove(img_path)

        return img_resized_filename


    def __get_background_image__(self):
        img_bg = Image.new('RGB', (400, 600), color=(16, 16, 16))
        img_bg_filename = 'bg.jpg'
        img_bg_file_source = os.path.join(self.movies_path, img_bg_filename)
        img_bg.save(img_bg_file_source)
        return img_bg_filename


    def __get_preview_with_background__(self, preview_image, background_image):
        preview_image_path = os.path.join(self.movies_path, preview_image)
        img_preview = Image.open(preview_image_path)
        preview_width, preview_height = img_preview.size

        bg_image_path = os.path.join(self.movies_path, background_image)
        img_bg = Image.open(bg_image_path)
        bg_width, bg_height = img_bg.size

        center_x = bg_width // 2 - preview_width // 2
        center_y = bg_height // 2 - preview_height // 2

        result = Image.new('RGB', (bg_width, bg_height), color=(0, 0, 0))
        result.paste(img_bg, (0, 0))
        result.paste(img_preview, (center_x, center_y))

        f_name, f_ext = os.path.splitext(preview_image)
        img_preview_filename = f'{f_name}.preview{f_ext}'
        img_preview_path = os.path.join(self.movies_path, img_preview_filename)
        result.save(img_preview_path)

        img_preview.close()
        img_bg.close()
        LOG.info(f'removing: {preview_image_path}')
        os.remove(preview_image_path)
        LOG.info(f'removing: {bg_image_path}')
        os.remove(bg_image_path)

        return img_preview_filename


    def __copy_preview_image__(self, image):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_path, image)
        image = Image.open(img_path)

        for i in range(1, self.__is_series__()+1):
            template = f_name + '.copy.{idx:02d}' + f_ext
            copy_filename = template.format(idx=i)
            LOG.debug(f'{copy_filename = }')
            copy_path = os.path.join(self.movies_path, copy_filename)
            image.save(copy_path)
        image.close()
        LOG.info(f'removing: {img_path}')
        os.remove(img_path)


    def __write_number__(self, image, number):
        f_name, f_ext = os.path.splitext(image)

        img_path = os.path.join(self.movies_path, image)
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('impact.ttf', size=50)
        draw.text((0, 0), str(number), fill='yellow', font=font)

        img_target_filename = f'{f_name}-{number}{f_ext}'
        img_target_path = os.path.join(self.movies_path, img_target_filename)
        img.save(img_target_path)

        img.close
        LOG.info(f'removing: {img_path}')
        os.remove(img_path)


    def preview_generate(self):
        LOG.info(f'{constants.EQUALS} PREVIEW GENERATE {constants.EQUALS}')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, f_ext = os.path.splitext(f)
            if f_ext in constants.IMAGE:
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
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, f_ext = os.path.splitext(f)
            if f_ext in constants.IMAGE:
                LOG.debug(f'{f = }')
                LOG.debug(f'{preview_idx = }')
                self.__write_number__(f, preview_idx)
                preview_idx += 1
    
    def __subtitle_purification__(self, sub_path_source, sub_path_target):
        with codecs.open(sub_path_source, mode='r', encoding=self.__get_file_encoding__(sub_path_source)) as sub_file_source:
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

            for event in doc.events:
                clear_text = re.sub(r'{[^}]*}', '', event.text).strip()
                event.text = clear_text
                if re.match(r'^Main', string=event.style) or re.match(r'^Default', string=event.style):
                    event.style = 'Main'
                else:
                    event.style = 'Signs'

            with open(sub_path_target, 'w', encoding='utf_8_sig') as sub_file_target:
                doc.dump_file(sub_file_target)
            sub_file_target.close()
        sub_file_source.close()

        LOG.info(f'removing: {sub_path_source}')
        os.remove(sub_path_source)


    def ass_subtitle_purification(self):
        LOG.info(f'{constants.EQUALS} {constants.ASS}\/ SUBTITLE PURIFACATION \/{constants.EQUALS}')
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            f_name, f_ext = os.path.splitext(f)
            if f_ext == constants.ASS:
                sub_path_source = os.path.join(self.movies_path, f)
                sub_path_target = os.path.join(self.movies_path, f'{f_name}.out{f_ext}')
                LOG.debug(f'{sub_path_source = }')
                LOG.debug(f'{sub_path_target = }')
                self.__subtitle_purification__(sub_path_source, sub_path_target)
        LOG.info(f'{constants.EQUALS} {constants.ASS}/\ SUBTITLE PURIFACATION /\{constants.EQUALS}')
