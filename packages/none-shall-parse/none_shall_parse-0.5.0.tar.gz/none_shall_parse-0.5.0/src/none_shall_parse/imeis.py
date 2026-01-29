
LUHN_DOUBLES = [0, 2, 4, 6, 8, 1, 3, 5, 7, 9]


def get_luhn_digit(n: str | int) -> int:
    """
    Calculates the Luhn checksum digit for a given number.

    The function processes a number using the Luhn algorithm. It computes
    the Luhn checksum digit based on the provided digits, ensuring that the
    resulting number adheres to the Luhn standard. The method is useful for
    validating numerical identifiers like credit card numbers or IMEIs.

    Parameters:
        n (str | int): A number represented as a string or integer that
        requires Luhn checksum digit calculation.

    Returns:
        int: The Luhn checksum digit as an integer.
    """
    chars = [int(ch) for ch in str(n)]
    firsts = [ch for ch in chars[0::2]]
    doubles = [LUHN_DOUBLES[ch] for ch in chars[1::2]]
    check = 10 - divmod(sum((sum(firsts), sum(doubles))), 10)[1]
    return divmod(check, 10)[1]


def is_valid_luhn(n: str | int) -> bool:
    """
    Determines if a given number, represented as a string or integer, adheres
    to the Luhn algorithm.

    The Luhn algorithm, also known as the mod 10 algorithm, is a simple checksum
    formula used to validate identification numbers such as credit card numbers.

    Parameters:
    n : Union[str, int]
        The input number to be validated. It can be provided as a string or an integer.

    Returns:
    bool
        Returns True if the input number satisfies the Luhn algorithm; otherwise, False.
    """
    n = "".join(
        [
            e
            for e in n
            if e
            in [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                "0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
            ]
        ]
    )
    chars = [int(ch) for ch in str(n)][::-1]  # Reversed Digits
    firsts = [ch for ch in chars[0::2]]
    doubles = [LUHN_DOUBLES[ch] for ch in chars[1::2]]
    final = sum((sum(firsts), sum(doubles)))
    return divmod(final, 10)[1] == 0


def is_valid_imei(n: str | int) -> bool:
    """
    Determines whether the given number is a valid IMEI (International Mobile
    Equipment Identity) number.

    An IMEI number is a 15-digit unique identifier for a mobile device. This function
    first checks that the length of the input is 15 characters and then validates
    it using the Luhn algorithm.

    Parameters:
    n: Union[str, int]
        The number to be checked, represented as a string or integer.

    Returns:
    bool
        True if the given number is a valid IMEI, otherwise False.
    """
    return len(str(n)) == 15 and is_valid_luhn(n)


def normalize_imei(c: str | int) -> str:
    """
    Normalizes the given IMEI number by extracting the first 14 digits and appending
    the calculated Luhn check digit to make it a valid IMEI.

    The IMEI (International Mobile Equipment Identity) is a unique identifier
    typically consisting of 15 digits. This function ensures that the provided
    IMEI-like input is converted into a valid IMEI format by calculating and appending
    the appropriate check digit.

    Parameters:
    c: Union[str, int]
        The input IMEI or a value resembling an IMEI. It can be provided as a string
        or an integer.

    Returns:
    str
        A 15-digit valid IMEI as a string.

    Raises:
    Exception
        Raises any exceptions occurring internally within the `get_luhn_digit` function
        if the calculation of the check digit fails.

    Notes:
    This function assumes the presence of the `get_luhn_digit` function for Luhn
    digit calculation.
    """
    t = str(c)[:14]
    check_digit = get_luhn_digit(t)
    return "%s%s" % (t, check_digit)


def get_tac_from_imei(n: str | int) -> tuple[bool, str]:
    """
    Determines the validity of an IMEI number and extracts its TAC if valid.

    This function checks whether a provided IMEI (International Mobile Equipment
    Identity) number is valid based on IMEI validation rules. If the given IMEI
    is valid, the function also extracts and returns the TAC (Type Allocation
    Code), which corresponds to the first 8 digits of the IMEI.

    Parameters:
    n (str): The IMEI number to be validated and processed.

    Returns:
    tuple: A tuple containing a boolean indicating whether the IMEI is valid
    and a string representing the TAC if valid or a placeholder if invalid.
    """
    tac = "Not a Valid IMEI"
    is_valid = is_valid_imei(n)
    if not is_valid:
        return False, tac
    else:
        tac = str(n)[:8]
        return True, tac


def decrement_imei(n: str | int) -> tuple[bool, str]:
    """
    Decrements the given IMEI number by one and normalizes it.

    This function validates the provided IMEI number. If it is a valid IMEI, the
    function decrements the first 14 digits by one and computes the new IMEI
    checksum to generate a normalized IMEI. If the provided IMEI is not valid,
    it returns a failure status and an error message.

    Parameters:
    n: int
        The IMEI number to be validated and decremented.

    Returns:
    tuple[bool, str]
        A tuple where the first element is a boolean indicating whether the
        operation was successful, and the second element is the resulting IMEI
        or an error message if the input was invalid.
    """
    result = "Not a Valid IMEI"
    is_valid = is_valid_imei(n)
    if not is_valid:
        return False, result
    else:
        result = normalize_imei(int(str(n)[:14]) - 1)
        return True, result


def increment_imei(n: str | int) -> tuple[bool, str]:
    """
    Determines if a given IMEI number is valid and increments it by 1 if valid.

    This function first checks if the provided IMEI number is valid using the
    is_valid_imei function. If the input is a valid IMEI, it increments the IMEI
    value by 1 while retaining only the first 14 digits. If the input is not valid,
    it returns a predefined invalid result.

    Parameters:
    n: int
        IMEI number to be validated and potentially incremented.

    Returns:
    tuple[bool, str]
        A tuple where the first element is a boolean indicating whether the operation
        was successful, and the second element is a string containing the incremented
        IMEI number if valid or an error message if not valid.
    """
    result = "Not a Valid IMEI"
    is_valid = is_valid_imei(n)
    if not is_valid:
        return False, result
    else:
        result = normalize_imei(int(str(n)[:14]) + 1)
        return True, result
