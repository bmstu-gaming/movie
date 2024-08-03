import random
import string


def get_filename_prefix(size=10, chars=string.ascii_uppercase + string.digits):
    filename_prefix = ''.join(random.choice(chars) for _ in range(size))
    return filename_prefix
