import re
from typing import List
from typing import Union

import colors
import consolemenu

from movie.utils import movie
from movie.utils import notation
from movie.utils import stream


def _function_end(pu: consolemenu.PromptUtils) -> None:
    pu.println('\nProcess completed successfully!')
    pu.enter_to_continue('Press [Enter] to go back')


def common_call(movie_obj: movie.Movie, function):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    function(movie_obj)
    _function_end(pu)


def streams_info(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    print_streams(pu, movie_obj)

    _function_end(pu)


def color_print_streams(pu: consolemenu.PromptUtils, title: str, streams: List[stream.Stream], color: str):
    pu.println(f'{colors.color(title, fg=f"{color}")}')
    for s_stream in streams:
        pu.println(f'{colors.color(s_stream, fg=f"{color}")}')


def print_streams(pu: consolemenu.PromptUtils, movie_obj: movie.Movie) -> Union[str, None]:
    logs_file_path = movie_obj.get_streams_and_log_file()
    if logs_file_path is None:
        pu.println(f'There is no video file in movie folder: {movie_obj.movies_folder}')
        return None

    video_streams, audio_streams, subtitle_streams = movie_obj.__separate_media_streams__()
    pu.println(f'{colors.color("#: (Language) Title", fg="#FFFFFF")}')
    color_print_streams(pu, 'Video streams', video_streams, '#FFFF00')
    color_print_streams(pu, 'Audio streams', audio_streams, '#00FFFF')
    color_print_streams(pu, 'Subtitle streams', subtitle_streams, '#FF00FF')
    return 'OK'

def get_input_selected_streams(pu: consolemenu.PromptUtils, movie_obj: movie.Movie) -> Union[List[int], None]:
    if print_streams(pu, movie_obj) is None:
        return None

    pu.println(
        '''
Please select one or more entries separated by commas, and/or a range of numbers.
For example: 0,1,4,6 or 0-5 or 0-2,4,7-10.
The first selected stream in the category will be set as default.

Enter: q or quit to exit
        '''
    )
    input_streams = []
    print_flag = False
    while not print_flag:
        result = pu.input('\nEnter stream numbers to save')
        input_string = result.input_string.strip()
        if re.match(r'^q', string=input_string):
            pu.println('Quiting\n')
            return None

        if input_string == '':
            pu.println('Empty string\n')
            continue

        if not notation.validation(input_string):
            pu.println('Wrong entered stream numbers\n')
            continue

        input_streams = notation.recognition(input_string)
        pu.println(f'\nStreams to save: {input_streams}')
        if pu.confirm_answer(input_streams, message='Is streams correct?'):
            print_flag = True
    return input_streams


def select_and_process_streams(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    input_streams = get_input_selected_streams(pu, movie_obj)
    if input_streams is not None:
        pu.println('\nStarting saving streams process\n')
        movie_obj.process_streams(input_streams)

    _function_end(pu)


def select_and_process_streams_with_language(movie_obj: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    input_streams = get_input_selected_streams(pu, movie_obj)

    if input_streams is not None:
        pu.println(
            '''
    Please print language for each choosen stream. 
    Use ISO 639 language codes (Set 1 or Set 2/T or Set 2/B)
    more info: https://wikipedia.org/wiki/List_of_ISO_639_language_codes
    For example: en or jpn or ru
            '''
)
        streams_languages = {}
        for stream_number in input_streams:
            result = pu.input(f'Enter language for {stream_number}')
            streams_languages[stream_number] = result.input_string

        pu.println('\nStarting saving streams process\n')
        movie_obj.process_streams_with_language(streams_languages)

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
    except Exception as e:
        pu.println(f'Error: {e}')

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
    except Exception as e:
        pu.println(f'Error: {e}')

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
