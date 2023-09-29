import codecs
from datetime import datetime
from enum import Enum
import logging
import json
import os
import subprocess
import pysubs2
import chardet

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO) # DEBUG INFO ERROR CRITICAL

BASE_TEMPLATE = "Movie"
CHECK='\u2714'  # ✔ check mark
CROSS='\u274c'  # ❌ cross mark


class Movie(object):
    def __init__(self):
        self.base_template = BASE_TEMPLATE

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

        LOG.debug(f'{self.base_template = }')
        if os.path.isdir(self.movies_path):
            LOG.info(f'MOVIES_PATH: \"{self.movies_path}\" {CHECK}')
        else:
            LOG.error(f'MOVIES_PATH: \"{self.movies_path}\" {CROSS}')
            status = False

        cmd_exec = [self.ffmpeg, '-h']
        try:
            stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
        except Exception as e:
            LOG.error(f'\"{self.ffmpeg}\" not valid: {str(e)}')
            return False

        LOG.info(f'FFMPEG: \"{self.ffmpeg}\" {CHECK}')
        LOG.debug(f"{ stdout.args = }")
        LOG.debug(f"{ stdout.returncode = }")
        LOG.debug(f"{ stdout.stderr = }")
        LOG.debug(f"{ stdout.stdout = }")
        return status

    # get_info
    def get_info(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                first_video = f
                LOG.debug(f"{ first_video = }")
                break

        video_path_source = os.path.join(self.movies_path, first_video)
        LOG.info(f"{ video_path_source = }")

        dt_string = datetime.now().strftime("%Y.%m.%d - %H.%M.%S")
        LOG.debug(f'{ dt_string = }')

        cmd_exec = [self.ffmpeg, '-i', video_path_source]
        stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
        LOG.debug(f"{ stdout.args = }")
        LOG.debug(f"{ stdout.returncode = }")
        LOG.debug(f"{ stdout.stderr = }")
        LOG.debug(f"{ stdout.stdout = }")
        stderr = stdout.stderr.split('\n')

        with open(f"{dt_string}-{first_video}.log", 'w') as fp:
            for item in stderr:
                fp.write("%s\n" % item)
        LOG.info(f' info in: {dt_string}-{first_video}.log')

    # save_necessary_metadata
    def save_necessary_metadata(self, streams):
        maps = [
            item
                for stream in streams
                    for item in ['-map', f'0:{stream}']
        ]
        LOG.debug(f"{ maps = }")
        
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                video_path_result = os.path.join(self.movies_path, f"pure-{f}")

                LOG.info(f"{ video_path_source = }")
                LOG.debug(f"{ video_path_result = }")

                cmd_exec = [self.ffmpeg, '-i', video_path_source,
                            '-c', 'copy',
                            *maps,
                            '-map_metadata', '-1', '-map_chapters', '-1',
                            video_path_result]
                stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
                LOG.debug(f"{ stdout.args = }")
                LOG.debug(f"{ stdout.returncode = }")
                LOG.debug(f"{ stdout.stderr = }")
                LOG.debug(f"{ stdout.stdout = }")

    # remove_video
    def remove_video(self, save_template, do_remove):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                if save_template in f:
                    LOG.debug(f"     {save_template} video: {f}")
                else:
                    LOG.debug(f" non {save_template} video: {f}")
                    non_template_video_path = os.path.join(self.movies_path, f)
                    LOG.info(f" removing: {non_template_video_path}")
                    if do_remove:
                        os.remove(non_template_video_path)

    # make_default_subs
    def set_default_and_language_streams(self, languages, streams):
        default_metadata = []
        for idx in range(len(streams)):
            LOG.debug(f"{ streams[idx] = }")
            LOG.debug(f"{ languages[idx] = }")

            metadata = [f'-metadata:s:{streams[idx]}', f'language={languages[idx]}', '-default_mode',
                        'infer', f'-disposition:s:{streams[idx]}', '-default']
            for elem in metadata:
                default_metadata.append(elem)
            LOG.debug(f"{ default_metadata = }")
        
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".mkv":
                video_path_source = os.path.join(self.movies_path, f)
                video_path_result = os.path.join(self.movies_path, f"default_rus_subs-{f}")

                LOG.info(f"{ video_path_source = }")
                LOG.debug(f"{ video_path_result = }")

                cmd_exec = [self.ffmpeg, '-i', video_path_source,
                            '-c', 'copy',
                            *default_metadata,
                            video_path_result]
                LOG.debug(f"{ cmd_exec = }")
                stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
                LOG.debug(f"{ stdout.args = }")
                LOG.debug(f"{ stdout.returncode = }")
                LOG.debug(f"{ stdout.stderr = }")
                LOG.debug(f"{ stdout.stdout = }")

    # rename_files
    def rename_files(self, do_rename):
        def rename(path, f, template, idx, do_rename):
            file_name, file_extension = os.path.splitext(f)
            new_file_name = template.format(episode_idx = idx)
            LOG.debug(f" old_file: {file_name}{file_extension}")
            LOG.info(f"  new_file: {new_file_name}{file_extension}")
            old_file = os.path.join(path, f)
            new_file = os.path.join(path, new_file_name + file_extension)
            if do_rename:
                os.rename(old_file, new_file)

        base_idx = 1
        subtitle_idx = base_idx
        video_idx = base_idx
        picture_idx = base_idx
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            
            if file_extension == ".mkv":
                TEMPLATE_VIDEO = self.base_template + ".E{episode_idx:02d}"
                rename(path=self.movies_path, f=f, template=TEMPLATE_VIDEO, idx=video_idx, do_rename=do_rename)
                video_idx += 1
            if file_extension == ".ass" or file_extension == ".srt":
                TEMPLATE_SUB = self.base_template + ".E{episode_idx:02d}.RUS"
                rename(path=self.movies_path, f=f, template=TEMPLATE_SUB, idx=subtitle_idx, do_rename=do_rename)
                subtitle_idx += 1
            if file_extension == ".png" or file_extension == ".jpg":
                TEMPLATE_IMG = self.base_template + ".E{episode_idx:02d}"
                rename(path=self.movies_path, f=f, template=TEMPLATE_IMG, idx=picture_idx, do_rename=do_rename)
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

    # __get_max_occur_styles__
    def __get_max_occur_styles__(self, f, max_styles=5, log_info=False):
        lines = []
        sub_path_source = os.path.join(self.movies_path, f)
        with codecs.open(sub_path_source, "r", "utf_8_sig") as file_sub:
            LOG.info(f"Sub: {sub_path_source}")
            lines = file_sub.readlines()

        words = []
        for _, line in enumerate(lines):
            if line.startswith("Style: "):
                styleSettingsList = line[7:].split(",")
                words.append(styleSettingsList[0])
        LOG.debug(f"{words = }")

        sub_file = codecs.open(sub_path_source, "r", "utf_8_sig")
        sub_data = sub_file.read()
        occ = {}
        for style in words:
            occurrences = sub_data.count(style)
            occ[style] = occurrences
        LOG.debug(f"{occ = }")

        import heapq
        styleWithMaxOccurrences = heapq.nlargest(max_styles, occ, key=occ.get)
        sorted_occ = sorted(occ.items(), key=lambda x:x[1], reverse=True)
        sorted_occ_dict = dict(sorted_occ)
        if log_info:
            for key in sorted_occ_dict:
                LOG.info(f"{key}: {sorted_occ_dict[key]}")
        LOG.debug(f"{styleWithMaxOccurrences}")
        return styleWithMaxOccurrences, lines

    # get_sub_info
    def get_sub_info(self):
        for _, f in enumerate(os.listdir(self.movies_path), start=1):
            _, file_extension = os.path.splitext(f)
            if file_extension == ".ass":
                first_video = f
                LOG.debug(f"{ first_video = }")
                self.__get_max_occur_styles__(f=f, log_info=True)
                break
                
    # dialogue_subs_ass
    def dialogue_subs_ass(self, max_styles, do):
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
                styleWithMaxOccurrences, lines = self.__get_max_occur_styles__(f=f, max_styles=max_styles)
                sub_path_source = os.path.join(self.movies_path, f)
                if do:
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
    if not movie.config_verification():
        print(f'config.json {CROSS}')
        return
    else:
        print(f'config.json {CHECK}')

    movie.get_info()
    movie.save_necessary_metadata(streams=["0", "1"])
    movie.remove_video(save_template="pure", do_remove=True)
    movie.get_info()
    movie.set_default_and_language_streams(languages=["ja"], streams=[1])
    # movie.set_default_and_language_streams(languages=["ja", "rus"], streams=[1, 2])
    movie.remove_video(save_template="default_rus_subs", do_remove=True)
    movie.subs_convert_srt_to_ass()
    movie.get_sub_info()
    movie.dialogue_subs_ass(max_styles=3, do=True)
    movie.rename_files(do_rename=False)

if __name__ == "__main__":
    run()

# test_function
def test_function():
    movies_path = "E:\Program Data\Videos\Movies\TV-3"

    streams = [1, 2]
    languages = ["ja", "rus"]

    video_idx = 3

    video_path_source = os.path.join(movies_path, f"pure-0{video_idx}.mkv")
    LOG.debug(f"{ video_path_source = }")

    video_path_result = os.path.join(movies_path, f"0000-0{video_idx}.mkv")
    LOG.debug(f"{ video_path_result = }")

    default_metadata = []
    for idx in range(len(streams)):
        LOG.debug(f"{ streams[idx] = }")
        LOG.debug(f"{ languages[idx] = }")

        metadata = [f'-metadata:s:{streams[idx]}', f'language={languages[idx]}', '-default_mode',
                    'infer', f'-disposition:s:{streams[idx]}', '-default']
        for elem in metadata:
            default_metadata.append(elem)
        LOG.debug(f"{ default_metadata = }")


    cmd_exec = [FFMPEG, '-i', video_path_source,
                '-c', 'copy',
                *default_metadata,
                video_path_result]
    LOG.debug(f"{ cmd_exec = }")
    stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
    LOG.debug(f"{ stdout.args = }")
    LOG.debug(f"{ stdout.returncode = }")
    LOG.debug(f"{ stdout.stderr = }")
    LOG.debug(f"{ stdout.stdout = }")
