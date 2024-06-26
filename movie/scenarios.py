import colors
import consolemenu
import re

from movie.utils import movie


def common_call(object: movie.Movie, function):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    function(object)
    pu.println('Process completed successfully!')
    pu.enter_to_continue('Press [Enter] to go back')


def streams_info(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    print_streams(pu, object, print_log_file=True)
    pu.enter_to_continue('Press [Enter] to go back')


def color_print_streams(pu: consolemenu.PromptUtils, title: str, streams: list[dict], color: str):
    pu.println(f'{colors.color(title, fg=f"{color}")}')
    for stream in streams:
        out = f'{stream.get("stream")}: ({stream.get("language")}) {stream.get("title") if stream.get("title") is not None else ""}'
        pu.println(f'{colors.color(out, fg=f"{color}")}')


def print_streams(pu: consolemenu.PromptUtils, object: movie.Movie, print_log_file=False):
    logs_file_path = object.get_streams_and_log_file()
    if print_log_file:
        pu.println(f'{colors.color(f"ffmpeg work logs in: {logs_file_path}", fg=f"#FFFFFF")}')
    video_streams, audio_streams, subtitle_streams = object.__separate_media_streams__()
    pu.println(f'{colors.color("#: (Language) Title", fg=f"#FFFFFF")}')
    color_print_streams(pu, 'Video streams', video_streams, '#FFFF00')
    color_print_streams(pu, 'Audio streams', audio_streams, '#00FFFF')
    color_print_streams(pu, 'Subtitle streams', subtitle_streams, '#FF00FF')


def get_input_selected_streams(pu: consolemenu.PromptUtils, object: movie.Movie):
    object.get_streams_and_log_file()
    print_streams(pu, object)

    pu.println(
        f'''
Please select one or more entries separated by commas, and/or a range of numbers.
For example: 0,1,4,6 or 0-5 or 0-2,4,7-10

Enter: q or quit to exit
        '''
    )
    print_flag = False
    while not print_flag:
        result = pu.input("\nEnter stream numbers to save")
        input = result.input_string.strip()
        if re.match(r'^q', string=input):
            pu.enter_to_continue('Press [Enter] to go back')
            return

        if input == '':
            pu.println(f'Empty string\n')
            continue

        if not object.__notation_validation__(input):
            pu.println(f'Wrong entered stream numbers\n')
            continue

        selected_streams = object.__notation_recognition__(input)
        pu.println(f'\nStreams to save: {selected_streams}')
        if pu.confirm_answer(selected_streams, message='Is streams correct?'):
            print_flag = True
    return selected_streams


def selected_streams(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    selected_streams = get_input_selected_streams(pu, object)

    pu.println(f'\nStarting saving streams process\n')
    object.selected_streams(selected_streams)
    object.remove_video()
    pu.println(f'\nProcess is completed!\n')

    pu.enter_to_continue('Press [Enter] to go back')


def set_default_and_language_streams(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    selected_streams = get_input_selected_streams(pu, object)

    pu.println(
        f'''
Please print language for each choosen stream. 
Use ISO 639 language codes (Set 1 or Set 2/T or Set 2/B)
more info: https://wikipedia.org/wiki/List_of_ISO_639_language_codes
For example: en or jpn or ru
        '''
    )    
    streams_languages = {}
    for stream_number in selected_streams:
        result = pu.input(f"Enter language for {stream_number}")
        streams_languages[stream_number] = result.input_string

    pu.println(f'\nStarting saving streams process\n')
    object.set_default_and_language_streams(streams_languages)
    object.remove_video()
    pu.println(f'\nProcess is completed!\n')

    pu.enter_to_continue('Press [Enter] to go back')


def subtitle_extract_to_ass(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        f'''
Extracting subtitle stream to .ass file
        '''
    )
    try:
        if pu.confirm_answer('aa', message='Would you like to remove subtitle from video?'):
            object.extract_subtitle(remove_subtitle=True)
        else:
            object.extract_subtitle()
        object.subs_convert_srt_to_ass()
    except Exception as e:
        pu.println(f'Error: {e}')
    pu.enter_to_continue('Press [Enter] to go back')


def subtitle_ass_translation(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        f'''
Translation subtitle
        '''
    )
    object.get_sub_info()
    try:
        if pu.confirm_answer('aa', message='Would you like to translate subtitle (autotranslate)?'):
            object.ass_subtitle_translation()
    except Exception as e:
        pu.println(f'Error: {e}')    
    pu.enter_to_continue('Press [Enter] to go back')

def subtitle_ass_purification(object: movie.Movie):
    pu = consolemenu.PromptUtils(consolemenu.Screen())
    pu.println(
        f'''
Making subtitle clear
        '''
    )
    object.get_sub_info()
    object.ass_subtitle_purification()
    pu.enter_to_continue('Press [Enter] to go back')
