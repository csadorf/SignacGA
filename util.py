import numpy as np

def randomString(length):
    """
    Return a random string of pre-defined characters
    of length
    """
    # 32 and 127 serve as bounds for displayable characters
    np.random.seed()
    randArr = np.random.randint(low=32, high=127, size=length)
    code = "".join([chr(i) for i in randArr])
    return code

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
    np.random.seed()
    # random cross value
    halfLength = np.random.randint(low=1, high=len(codeA)-2)
    childA = "{}{}".format(codeA[:halfLength], codeB[halfLength:])
    childB = "{}{}".format(codeB[:halfLength], codeA[halfLength:])
    return childA, childB

def _mutate(code, probability):
    """
    mutate the supplied code
    """
    np.random.seed()

    if np.random.rand() > probability:
        return code

    index = int(np.random.random() * len(code))
    direction = -1 if np.random.random() > 0.5 else 1
    lCode = list(code)
    charOrd = preventOverflow(ord(lCode[index]) + direction)
    lCode[index] = chr(charOrd)
    return "".join(lCode)
