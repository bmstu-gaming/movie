
from consolemenu import *
from consolemenu.items import *
import logging

import movie

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG) # DEBUG INFO ERROR CRITICAL


def handler(*args, **kwargs):
    pu = PromptUtils(Screen())

    LOG.debug(f'{args = }')
    LOG.debug(f'{kwargs = }')

    call = kwargs["call"]
    for key, value in kwargs.items():
        if key == "func":
            if value == movie.Movie.config_verification:
                LOG.debug(f'executing {movie.Movie.config_verification}')
                call()

    pu.enter_to_continue()

def input_handler():
    pu = PromptUtils(Screen())
    result = pu.input("Enter an input")
    print(f'\nYou entered: {result.input_string}\n')
    pu.enter_to_continue()

def run():
    obj = movie.Movie()
    if not obj.config_verification():
        print(f'{movie.CROSS} Config not valid! {movie.CROSS}')
        return
    
    menu = ConsoleMenu("Movie Menu", "This is movie preparation program")

    config_verification_item = FunctionItem(
        "Automatic: Config verification",
        handler,
        args=["arg string"],
        kwargs={
            "call": obj.config_verification,
            "func": movie.Movie.config_verification,
        }
    )
    # get_info_item = FunctionItem(
    #     "Get info",
    #     handler,
    #     args=["arg string"],
    #     kwargs={
    #         "func": anime.Movie.get_info,
    #         "object": obj,
    #         "streams": ["0", "1"],
    #     }
    # )


    partion_submenu = ConsoleMenu("Partion methods")

    function_item_1 = FunctionItem("Input test function 1", input_handler)
    function_item_2 = FunctionItem("Input test function 2", input_handler)
    function_item_3 = FunctionItem("Input test function 3", input_handler)
    function_item_4 = FunctionItem("Input test function 4", input_handler)
    function_item_5 = FunctionItem("Input test function 5", input_handler)
    function_item_6 = FunctionItem("Input test function 6", input_handler)
    function_item_7 = FunctionItem("Input test function 7", input_handler)
    function_item_8 = FunctionItem("Input test function 8", input_handler)

    partion_submenu.append_item(function_item_1)
    partion_submenu.append_item(function_item_2)
    partion_submenu.append_item(function_item_3)
    partion_submenu.append_item(function_item_4)
    partion_submenu.append_item(function_item_5)
    partion_submenu.append_item(function_item_6)
    partion_submenu.append_item(function_item_7)
    partion_submenu.append_item(function_item_8)

    partion_submenu_item = SubmenuItem("Partion methods", submenu=partion_submenu)
    partion_submenu_item.set_menu(menu)

    menu.append_item(config_verification_item)
    menu.append_item(partion_submenu_item)

    menu.start()
    menu.join()


if __name__ == "__main__":
    run()