import random
import string

def codeGenerate(length: int):
    num_digits = 2
    num_letters = length - num_digits
    digits = ''.join(random.choice(string.digits) for _ in range(num_digits))
    characters = string.ascii_uppercase
    code = digits + ''.join(random.choice(characters) for _ in range(num_letters))
    code_list = list(code)
    random.shuffle(code_list)
    code = ''.join(code_list)
    return code