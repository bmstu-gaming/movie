import consolemenu

from movie.utils import movie
from movie.utils import constants
from movie import scenarios


def run_menu():
    print(f'logs in: {constants.LOG_FILE}')
    movie_obj = movie.Movie()
    if not movie_obj.config_verification():
        return

    menu = consolemenu.ConsoleMenu("Main menu", prologue_text=(f'logs in: {constants.LOG_FILE}'))

    item1 = consolemenu.items.FunctionItem("Config check", scenarios.common_call, args=[movie_obj, movie.Movie.config_verification])
    item2 = consolemenu.items.FunctionItem("Streams info & log", scenarios.streams_info, args=[movie_obj])

    selection_stream_submenu = consolemenu.ConsoleMenu('Streams selection', prologue_text='select the type of indication for saving streams:')
    item_selected_streams = consolemenu.items.FunctionItem("Select Streams (simple)", scenarios.selected_streams, args=[movie_obj])
    item_selected_streams_and_language = consolemenu.items.FunctionItem("Select Streams (with language)", scenarios.set_default_and_language_streams, args=[movie_obj])
    selection_stream_submenu.append_item(item_selected_streams)
    selection_stream_submenu.append_item(item_selected_streams_and_language)
    item3 = consolemenu.items.SubmenuItem("Select streams", submenu=selection_stream_submenu)
    item3.set_menu(menu)

    subtitle_settings_submenu = consolemenu.ConsoleMenu('Subtitle settings', prologue_text='select the type of subtitle settings:')
    item_subtitle_information = consolemenu.items.FunctionItem("Information", scenarios.common_call, args=[movie_obj, movie.Movie.get_sub_info])
    item_subtitle_extract_to_ass = consolemenu.items.FunctionItem("Extraction", scenarios.subtitle_extract_to_ass, args=[movie_obj])
    item_subtitle_purification = consolemenu.items.FunctionItem("Purification", scenarios.subtitle_ass_purification, args=[movie_obj])
    subtitle_settings_submenu.append_item(item_subtitle_information)
    subtitle_settings_submenu.append_item(item_subtitle_extract_to_ass)
    subtitle_settings_submenu.append_item(item_subtitle_purification)
    item4 = consolemenu.items.SubmenuItem("Subtitle settings", submenu=subtitle_settings_submenu)
    item4.set_menu(menu)

    item5 = consolemenu.items.FunctionItem("Preview generation", scenarios.common_call, args=[movie_obj, movie.Movie.preview_generate])
    item6 = consolemenu.items.FunctionItem("Renaming files", scenarios.common_call, args=[movie_obj, movie.Movie.rename_files])

    menu.append_item(item1)
    menu.append_item(item2)
    menu.append_item(item3)
    menu.append_item(item4)
    menu.append_item(item5)
    menu.append_item(item6)

    menu.start()
    menu.join()
