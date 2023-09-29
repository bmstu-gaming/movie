import codecs
from datetime import datetime
from enum import Enum
import logging
import os
import subprocess
import pysubs2

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO) # DEBUG INFO ERROR CRITICAL

FFMPEG = "F:\\Program Files\\Jellyfin\\Server\\FFMPEG.exe"
MOVIES_PATH = "E:\\Program Data\\Videos\\Movies\\Gundam.0083.Stardust.Memory"
BASE_TEMPLATE = "Gundam.0083.Stardust.Memory.E"

def get_info(movies_path):
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".mkv":
            first_video = f
            LOG.debug(f"{ first_video = }")
            break

    video_path_source = os.path.join(movies_path, first_video)
    LOG.info(f"{ video_path_source = }")

    dt_string = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    LOG.info(f" datetime now = {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    cmd_exec = [FFMPEG, '-i', video_path_source]
    stdout = subprocess.run(cmd_exec, capture_output=True, text=True)
    LOG.debug(f"{ stdout.args = }")
    LOG.debug(f"{ stdout.returncode = }")
    LOG.debug(f"{ stdout.stderr = }")
    LOG.debug(f"{ stdout.stdout = }")

    stderr = stdout.stderr.split('\n')
    with open(f"{dt_string}-{first_video}.log", 'w') as fp:
        for item in stderr:
            fp.write("%s\n" % item)

# save_necessary_metadata
def save_necessary_metadata(movies_path, streams):
    maps = [
        item
            for stream in streams
                for item in ['-map', f'0:{stream}']
    ]
    LOG.debug(f"{ maps = }")
    
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".mkv":
            video_path_source = os.path.join(movies_path, f)
            video_path_result = os.path.join(movies_path, f"pure-{f}")

            LOG.info(f"{ video_path_source = }")
            LOG.debug(f"{ video_path_result = }")

            cmd_exec = [FFMPEG, '-i', video_path_source,
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
def remove_video(movies_path, save_template, do_remove):
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".mkv":
            if save_template in f:
                LOG.debug(f"     {save_template} video: {f}")
            else:
                LOG.debug(f" non {save_template} video: {f}")
                non_template_video_path = os.path.join(movies_path, f)
                LOG.info(f" removing: {non_template_video_path}")
                if do_remove:
                    os.remove(non_template_video_path)

# make_default_subs
def make_default_subs(movies_path, languages, streams):
    default_metadata = []
    for idx in range(len(streams)):
        LOG.debug(f"{ streams[idx] = }")
        LOG.debug(f"{ languages[idx] = }")

        metadata = [f'-metadata:s:{streams[idx]}', f'language={languages[idx]}', '-default_mode',
                    'infer', f'-disposition:s:{streams[idx]}', '-default']
        for elem in metadata:
            default_metadata.append(elem)
        LOG.debug(f"{ default_metadata = }")
    
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".mkv":
            video_path_source = os.path.join(movies_path, f)
            video_path_result = os.path.join(movies_path, f"default_rus_subs-{f}")

            LOG.info(f"{ video_path_source = }")
            LOG.debug(f"{ video_path_result = }")

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

# rename_files
def rename_files(movies_path, filename_template, do_rename):
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
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        
        if file_extension == ".mkv":
            TEMPLATE_VIDEO = filename_template + "{episode_idx:02d}"
            rename(path=movies_path, f=f, template=TEMPLATE_VIDEO, idx=video_idx, do_rename=do_rename)
            video_idx += 1
        if file_extension == ".ass" or file_extension == ".srt":
            TEMPLATE_SUB = filename_template + "{episode_idx:02d}.RUS"
            rename(path=movies_path, f=f, template=TEMPLATE_SUB, idx=subtitle_idx, do_rename=do_rename)
            subtitle_idx += 1
        if file_extension == ".png" or file_extension == ".jpg":
            TEMPLATE_IMG = filename_template + "{episode_idx:02d}"
            rename(path=movies_path, f=f, template=TEMPLATE_IMG, idx=picture_idx, do_rename=do_rename)
            picture_idx += 1

# subs_convert_srt_to_ass
def subs_convert_srt_to_ass(movies_path):
    for _, f in enumerate(os.listdir(movies_path), start=1):
        filename, file_extension = os.path.splitext(f)
        if file_extension == ".srt":
            LOG.INFO(f"{filename = }")
            sub_path_source = os.path.join(movies_path, f)
            subs = pysubs2.load(sub_path_source)
            sub_path_target = os.path.join(movies_path, f'{filename}.ass')
            subs.save(sub_path_target)

# __get_max_occur_styles__
def __get_max_occur_styles__(movies_path, f, max_styles=5, log_info=False):
    lines = []
    sub_path_source = os.path.join(movies_path, f)
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
def get_sub_info(movies_path):
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".ass":
            first_video = f
            LOG.debug(f"{ first_video = }")
            __get_max_occur_styles__(movies_path=movies_path, f=f, log_info=True)
            break
            
# dialogue_subs_ass
def dialogue_subs_ass(movies_path, max_styles, do):
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
    
    for _, f in enumerate(os.listdir(movies_path), start=1):
        _, file_extension = os.path.splitext(f)
        if file_extension == ".ass":            
            styleWithMaxOccurrences, lines = __get_max_occur_styles__(movies_path=movies_path, f=f, max_styles=max_styles)
            sub_path_source = os.path.join(movies_path, f)
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

if __name__ == "__main__":
    get_info(MOVIES_PATH)

    # save_necessary_metadata(MOVIES_PATH, streams=["0", "2"])

    # remove_video(MOVIES_PATH, save_template="pure", do_remove=True)

    # get_info(MOVIES_PATH)

    # # make_default_subs(MOVIES_PATH, languages=["ja"], streams=[1])
    # make_default_subs(MOVIES_PATH, languages=["ja", "rus"], streams=[1, 2])

    # remove_video(MOVIES_PATH, save_template="default_rus_subs", do_remove=True)

    # subs_convert_srt_to_ass(MOVIES_PATH)

    # get_sub_info(movies_path=MOVIES_PATH)

    # dialogue_subs_ass(movies_path=MOVIES_PATH, max_styles=1, do=True)

    # rename_files(movies_path=MOVIES_PATH, filename_template=BASE_TEMPLATE, do_rename=True)


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


