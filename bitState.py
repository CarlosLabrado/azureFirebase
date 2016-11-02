"""
Returns the state of a bit out of a Hex string
"""

__author__ = 'Cesar'


def get_bit_state(string, bit_num):
    byte = int(string, 16)
    if bit_num == 7:
        mask = 128
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 6:
        mask = 64
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 5:
        mask = 32
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 4:
        mask = 16
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 3:
        mask = 8
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 2:
        mask = 4
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 1:
        mask = 2
        if byte & mask:
            return '1'
        else:
            return '0'
    elif bit_num == 0:
        mask = 1
        if byte & mask:
            return '1'
        else:
            return '0'
    else:
        return '0'
