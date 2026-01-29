"""
Helper functions
"""

def gradient_range(a: int, b: int):

    """
    Creates an iterator that returns all values from a to b, creating a gradient. For example, if a = 3 and b = 5, it returns 3, 4 and 5. If a = 2 and b = -1, it returns 2, 1, 0, -1
    
    :param a: Initial value
    :type a: int
    :param b: Final value
    :type b: int
    """

    return range(a, b + (1 if a < b else -1), 1 if a < b else -1)

def is_number_colon_number(s: str) -> bool:

    """
    Checks if a string follows the format "number:number"
    
    :param s: The string subject to the check
    :type s: str
    :return: True or false
    :rtype: bool
    """

    parts = s.split(":")

    if len(parts) != 2: #easy check
        return False
    
    return parts[0].isdigit() and parts[1].isdigit()