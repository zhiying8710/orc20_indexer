import random
import string


def random_string(k=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k))