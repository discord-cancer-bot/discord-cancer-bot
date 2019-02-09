import random
import math


def mock_string(sentence: str) -> str:
    char_count = len(sentence)

    # Subtract from char_count if not a letter
    for i in sentence:
        if not i.isalpha():
            char_count -= 1

    mock_count = math.ceil(char_count - char_count / 2)
    sentence_mock = list(sentence.lower())

    index = 0
    current_mock_count = 0
    loop_limit = 4
    while current_mock_count in range(0, mock_count) and loop_limit > 0:
        capitalize = bool(random.getrandbits(1))
        val = str(sentence_mock[index])
        # Don't want to count a char mutation for spaces / integers / capitals.
        if capitalize and sentence_mock[index] != ' ' and val.isalpha() and not (val.isdigit() or val.isupper()):
            sentence_mock[index] = sentence_mock[index].upper()
            current_mock_count += 1
        index += 1
        # Restart at beginning of string if mock_count is not met.
        # Only allow # of runs set in loop_limit above.
        if index == len(sentence_mock):
            index = 0
            loop_limit -= 1

    sentence = ''.join(str(e) for e in sentence_mock)

    if current_mock_count < 1:
        return None

    return sentence
