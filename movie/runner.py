from movie.utils import movie
from movie.utils import constants


def run():
    movie_obj = movie.Movie()
    if movie_obj.config_verification():
        print(f'config.json {constants.CHECK}')
    else:
        print(f'config.json {constants.CROSS}')
        return

    movie_obj.get_streams_and_log_file()

    ### first selected audio/subtitles - default
    # selected_streams = [0, 2, 4]
    # movie_obj.selected_streams(selected_streams=selected_streams)
    # movie_obj.remove_video(do_remove=True)

    # streams_languages = {0: 'jpn', 1: 'jpn'}
    # movie_obj.set_default_and_language_streams(streams_languages=streams_languages)
    # movie_obj.remove_video(do_remove=True)

    # movie_obj.get_sub_info()
    # movie_obj.extract_subtitle()
    # movie_obj.subs_convert_srt_to_ass()
    # movie_obj.ass_subtitle_purification()

    # movie_obj.preview_generate()

    # movie_obj.rename_files(do_rename=True)
