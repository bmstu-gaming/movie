import consolemenu

from movie.utils import config
from movie.utils import constants
from movie.utils.logging_config import LOG
from movie.utils.movie import Movie
from movie import scenarios


def get_stream_submenu(movie_obj: Movie) -> consolemenu.items.SelectionItem:
    selection_stream_submenu = consolemenu.ConsoleMenu(
        'Streams selection', prologue_text='select the type of indication for saving streams:', exit_menu_char='q')

    item_selected_streams = consolemenu.items.FunctionItem(
        'Select Streams (simple)', scenarios.select_and_process_streams, args=[movie_obj])
    item_selected_streams_and_language = consolemenu.items.FunctionItem(
        'Select Streams (with language)', scenarios.select_and_process_streams_with_language, args=[movie_obj])

    selection_stream_submenu.append_item(item_selected_streams)
    selection_stream_submenu.append_item(item_selected_streams_and_language)

    stream_submenu = consolemenu.items.SubmenuItem('Select streams', submenu=selection_stream_submenu, menu_char='v')
    return stream_submenu


def get_extract_audio_submenu(movie_obj: Movie) -> consolemenu.items.SelectionItem:
    extract_audio_submenu = consolemenu.ConsoleMenu(
        'Extract audio from video', prologue_text='select the type of audio output:', exit_menu_char='q')

    for audio_type in constants.AUDIO:
        item_extract_audio = consolemenu.items.FunctionItem(
            f'{audio_type}', scenarios.common_call, args=[movie_obj, Movie.extract_audio_from_video_files, audio_type])
        extract_audio_submenu.append_item(item_extract_audio)

    extract_audio_menu = consolemenu.items.SubmenuItem('Extract audio from video', submenu=extract_audio_submenu)
    return extract_audio_menu


def get_audio_submenu(movie_obj: Movie) -> consolemenu.items.SelectionItem:
    selection_audio_submenu = consolemenu.ConsoleMenu(
        'Audio settings', prologue_text='select the type of audio settings:', exit_menu_char='q')

    item_extract_audio = get_extract_audio_submenu(movie_obj)
    item_extract_audio.set_menu(selection_audio_submenu)
    item_insert_audio = consolemenu.items.FunctionItem(
        'Insert/combine audio with video (in work)',scenarios.common_call, args=[movie_obj, Movie.func_in_progress])
    item_non_default_external_audio = consolemenu.items.FunctionItem(
        'Remove default settings from external audio',
        scenarios.common_call, args=[movie_obj, Movie.set_external_audio_non_default])

    selection_audio_submenu.append_item(item_extract_audio)
    selection_audio_submenu.append_item(item_insert_audio)
    selection_audio_submenu.append_item(item_non_default_external_audio)

    audio_submenu = consolemenu.items.SubmenuItem('Select audio', submenu=selection_audio_submenu, menu_char='a')
    return audio_submenu


def get_subtitle_submenu(movie_obj: Movie) -> consolemenu.items.SelectionItem:
    subtitle_settings_submenu = consolemenu.ConsoleMenu(
        'Subtitle settings', prologue_text='select the type of subtitle settings:', exit_menu_char='q')
    item_subtitle_information = consolemenu.items.FunctionItem(
        'Information', scenarios.common_call, args=[movie_obj, Movie.get_sub_info])
    item_subtitle_extract_to_ass = consolemenu.items.FunctionItem(
        'Extraction', scenarios.subtitle_extract_to_ass, args=[movie_obj])
    item_subtitle_purification = consolemenu.items.FunctionItem(
        'Purification', scenarios.subtitle_ass_purification, args=[movie_obj])
    item_subtitle_convert_srt_to_ass = consolemenu.items.FunctionItem(
        'Convert SRT to ASS', scenarios.common_call, args=[movie_obj, Movie.subs_convert_srt_to_ass])
    item_subtitle_translation = consolemenu.items.FunctionItem(
        'Translation', scenarios.subtitle_ass_translation, args=[movie_obj])
    subtitle_settings_submenu.append_item(item_subtitle_information)
    subtitle_settings_submenu.append_item(item_subtitle_extract_to_ass)
    subtitle_settings_submenu.append_item(item_subtitle_purification)
    subtitle_settings_submenu.append_item(item_subtitle_convert_srt_to_ass)
    subtitle_settings_submenu.append_item(item_subtitle_translation)

    subtitle_submenu = consolemenu.items.SubmenuItem(
        'Subtitle settings', submenu=subtitle_settings_submenu, menu_char='s')

    return subtitle_submenu


def main_menu():
    LOG.debug('')
    LOG.debug('                      PROGRAM START')
    LOG.debug('')

    movie_obj = config.apply_config()

    menu = consolemenu.ConsoleMenu('Main menu', prologue_text=f'logs in: {constants.LOG_FILE}', exit_menu_char='q')

    item_update_config = consolemenu.items.FunctionItem(
        'Update config', scenarios.common_call, args=[movie_obj, config.update_config])

    item_streams_info = consolemenu.items.FunctionItem('Streams info & log', scenarios.streams_info, args=[movie_obj])

    item_streams_processing = get_stream_submenu(movie_obj)
    item_streams_processing.set_menu(menu)

    item_audio_processing = get_audio_submenu(movie_obj)
    item_audio_processing.set_menu(menu)

    item_subtitle = get_subtitle_submenu(movie_obj)
    item_subtitle.set_menu(menu)

    item_preview = consolemenu.items.FunctionItem(
        'Preview generation', scenarios.common_call, args=[movie_obj, Movie.preview_generate], menu_char='g')
    item_renaming = consolemenu.items.FunctionItem(
        'Renaming files', scenarios.common_call, args=[movie_obj, Movie.rename_files], menu_char='r')

    menu.append_item(item_update_config)
    menu.append_item(item_streams_info)
    menu.append_item(item_streams_processing)
    menu.append_item(item_audio_processing)
    menu.append_item(item_subtitle)
    menu.append_item(item_preview)
    menu.append_item(item_renaming)

    menu.start()
    menu.join()
