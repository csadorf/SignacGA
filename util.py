import numpy as np

def preventOverflow(charOrd):
    if charOrd > 127:
        return 127
    if charOrd < 32:
        return 32
    return charOrd

def _mate(codeA, codeB):
    """
    mate the two supplied codes
    """
    halfLength = len(codeA) // 2
    childA = "{}{}".format(codeA[:halfLength], codeB[halfLength:])
    childB = "{}{}".format(codeB[:halfLength], codeA[halfLength:])
    return childA, childB

def _mutate(code, probability):
    """
    mutate the supplied code
    """

    if np.random.rand() > probability:
        return None

    index = int(np.random.random() * len(code))
    direction = -1 if np.random.random() > 0.5 else 1
    lCode = list(code)
    charOrd = preventOverflow(ord(lCode[index]) + direction)
    lCode[index] = chr(charOrd)
    return "".join(lCode)
