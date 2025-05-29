import re
from typing import List
from typing import Optional

import colors
import consolemenu

from movie.utils.logging_config import LOG
from movie.utils import movie
from movie.utils import notation
from movie.utils import stream

def _function_end(pu: consolemenu.PromptUtils) -> None:
    pu.println('\nProcess completed successfully!')
    pu.enter_to_continue('Press [Enter] to go back')


def common_call(movie_obj: movie.Movie, function, *args, **kwargs):
    pu = consolemenu.PromptUtils(consolemenu.Screen())

    try:
        function(movie_obj, *args, **kwargs)
    except Exception:
        LOG.exception(f'Error while running function [{function.__name__}]')

    _function_end(pu)


def streams_info(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    movie_obj.analyze_first_video_file()
    _display_streams(pu, movie_obj)
    _function_end(pu)


def _color_print_streams(pu: consolemenu.PromptUtils, title: str, streams: List[stream.Stream], color: str):
    pu.println(f'{colors.color(title, fg=f"{color}")}')
    for s_stream in streams:
        pu.println(f'{colors.color(s_stream, fg=f"{color}")}')


def _display_streams(
        pu: consolemenu.PromptUtils,
        movie_obj: movie.Movie,
        input_streams: Optional[List[int]] = None,
) -> None:
    video_streams, audio_streams, subtitle_streams = movie_obj.__separate_media_streams__()

    if input_streams is not None:
        video_streams = [s for s in video_streams if s.index in input_streams]
        audio_streams = [s for s in audio_streams if s.index in input_streams]
        subtitle_streams = [s for s in subtitle_streams if s.index in input_streams]

    LOG.debug(f'{video_streams = }')
    LOG.debug(f'{audio_streams = }')
    LOG.debug(f'{subtitle_streams = }')

    pu.println(f'{colors.color("#: (Language) Title", fg="#FFFFFF")}')
    _color_print_streams(pu, 'Video streams', video_streams, '#FFFF00')
    _color_print_streams(pu, 'Audio streams', audio_streams, '#00FFFF')
    _color_print_streams(pu, 'Subtitle streams', subtitle_streams, '#FF00FF')
    pu.println('')


def _print_information_streams_selection(pu: consolemenu.PromptUtils) -> None:
    pu.println(
        '''
Please select one or more entries separated by commas, and/or a range of numbers.
For example: 0,1,4,6 or 0-5 or 0-2,4,7-10.
The first selected stream in the category will be set as default.

Enter: q or quit to exit
        '''
    )


def _print_information_entering_language(pu: consolemenu.PromptUtils):
    pu.println(
        '''
Please print language for each choosen stream.

Use ISO 639 language codes (Set 1 or Set 2/T or Set 2/B)
more information: https://wikipedia.org/wiki/List_of_ISO_639_language_codes
For example: en or jpn or ru
        '''
    )


def _print_information_streams_status(pu: consolemenu.PromptUtils):
    pu.println(
        '''
Please select status for input streams
Enter:
a - Yes to All (apply input streams for all video files in folder)
y - Yes (apply input streams only for current video file)
n - No (reenter input streams)
q - Quit (quit form menu)
        '''
    )


def _get_input_streams(pu: consolemenu.PromptUtils, movie_obj: movie.Movie) -> Optional[List[int]]:
    while True:
        raw_input = pu.input('\nEnter stream numbers to save')
        user_input = raw_input.input_string.strip()

        if re.match(r'^q', user_input, re.IGNORECASE):
            pu.println('Quiting\n')
            return None

        if not user_input:
            pu.println('Empty string\n')
            continue

        if not notation.validation(user_input):
            pu.println('Wrong entered stream numbers\n')
            continue

        input_streams = notation.recognition(user_input)

        pu.println(f'\nStreams to save: {input_streams}')
        _display_streams(pu, movie_obj, input_streams)
        if pu.confirm_answer(input_streams):
            return input_streams


def _get_streams_status(pu: consolemenu.PromptUtils) -> Optional[str]:
    while True:
        raw_input = pu.input('\nEnter status')
        user_input = raw_input.input_string.strip().lower()

        if re.match(r'^q', user_input):
            pu.println('Quiting\n')
            return None
        if user_input == 'a':
            return 'all'
        if user_input == 'y':
            return 'current'
        if user_input == 'n':
            return 'reenter'
        if user_input == '':
            pu.println('Empty string\n')
        else:
            pu.println('Invalid input. Please enter a, y, n or q\n')


def _get_streams_to_video_files_map(pu: consolemenu.PromptUtils, movie_obj: movie.Movie) -> Optional[dict]:
    exec_map = {}
    streams_for_all_videos: List[int] = []
    all_videos = movie_obj.__get_video_files__()
    if not all_videos:
        pu.println(f'There is no video file in movie folder: {movie_obj.movies_folder}')
        return None

    for video_file in all_videos:
        movie_obj.analyze_video_file(video_file)
        pu.println(f'=== {video_file} ===')
        if not streams_for_all_videos:
            while True:
                pu.clear()
                LOG.info(f'=== {video_file} ===')
                _display_streams(pu, movie_obj)
                _print_information_streams_selection(pu)
                input_streams = _get_input_streams(pu, movie_obj)
                if input_streams is None:
                    return None

                _print_information_streams_status(pu)
                status = _get_streams_status(pu)
                if status == 'all':
                    streams_for_all_videos = input_streams
                    exec_map[video_file] = streams_for_all_videos
                    break
                if status == 'current':
                    exec_map[video_file] = input_streams
                    break
                if status == 'reenter':
                    continue
                if status is None:
                    return None
        else:
            exec_map[video_file] = streams_for_all_videos

    pu.clear()
    for video_file, input_streams in exec_map.items():
        pu.println(f'=== {video_file} ===')
        movie_obj.analyze_video_file(video_file)
        _display_streams(pu, movie_obj, input_streams)

    if pu.confirm_answer(None, message='Would you like to reenter streams?'):
        exec_map = _get_streams_to_video_files_map(pu, movie_obj)
    return exec_map


def _get_input_streams_language(pu: consolemenu.PromptUtils, input_streams: List[int]) -> dict:
    streams_languages = {}
    for stream_number in input_streams:
        result = pu.input(f'Enter language for {stream_number}')
        streams_languages[stream_number] = result.input_string
    return streams_languages


def _get_streams_language_to_video_files_map(
        pu: consolemenu.PromptUtils,
        movie_obj: movie.Movie,
        map_video_to_selected_streams: dict,
) -> Optional[dict]:
    exec_map = {}
    for video_file, selected_streams in map_video_to_selected_streams.items():
        pu.clear()
        movie_obj.analyze_video_file(video_file)
        pu.println(f'=== {video_file} ===')
        _display_streams(pu, movie_obj, selected_streams)

        _print_information_entering_language(pu)
        input_streams_language = _get_input_streams_language(pu, selected_streams)
        exec_map[video_file] = input_streams_language
    return exec_map


def select_and_process_streams(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())

    try:
        exec_map = _get_streams_to_video_files_map(pu, movie_obj)
        if exec_map is not None:
            pu.println('\nStarting saving streams process\n')
            movie_obj.process_streams_to_video_files(exec_map)
    except Exception:
        LOG.exception('Error while running program')

    _function_end(pu)


def select_and_process_streams_with_language(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())

    try:
        map_video_to_selected_streams = _get_streams_to_video_files_map(pu, movie_obj)
        if map_video_to_selected_streams is not None:
            exec_map = _get_streams_language_to_video_files_map(pu, movie_obj, map_video_to_selected_streams)

            pu.println('\nStarting saving streams process\n')
            movie_obj.process_streams_language_to_video_files(exec_map)
    except Exception:
        LOG.exception('Error while running program')

    _function_end(pu)


def subtitle_extract_to_ass(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        '''
Extracting subtitle stream to .ass file
        '''
    )
    try:
        if pu.confirm_answer('aa', message='Save subtitle track in video file?'):
            movie_obj.extract_subtitle(keep_subtitles=True)
        else:
            movie_obj.extract_subtitle()
        movie_obj.subs_convert_srt_to_ass()
    except Exception:
        LOG.exception('Error while running program')

    _function_end(pu)


def subtitle_ass_translation(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        '''
Translation subtitle
        '''
    )
    movie_obj.get_sub_info()
    try:
        if pu.confirm_answer('aa', message='Would you like to translate subtitle (autotranslate)?'):
            movie_obj.ass_subtitle_translation()
    except Exception:
        LOG.exception('Error while running program')

    _function_end(pu)


def subtitle_ass_purification(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        '''
Making subtitle clear
        '''
    )
    movie_obj.ass_subtitle_purification()

    _function_end(pu)
