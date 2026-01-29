import base64
import hashlib
import itertools
import random
import re
import secrets
import string
import unicodedata
from typing import Any

_control_chars = "".join(
    map(chr, itertools.chain(range(0x00, 0x20), range(0x7F, 0xA0)))
)
_re_control_char = re.compile("[%s]" % re.escape(_control_chars))
_re_combine_whitespace = re.compile(r"\s+")


def slugify(value: object, allow_unicode: bool = False) -> str:
    """
    Maps directly to Django's slugify function.
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def random_16():
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))


def to_human_string(s: Any) -> tuple[Any | str, bool]:
    """
    Cleans up a string by removing extra whitespace and control characters.

    Removes unnecessary whitespace and control characters from the input string.
    This function is designed to validate and clean user-provided string input
    while preserving input that does not require modification. It returns the
    cleaned string along with a boolean indicating whether changes were made
    to the original string.

    Parameters:
    s : any
        The input value to clean and validate. If it is not a string, it is
        returned unchanged with a modification flag of False.

    Returns:
    tuple
        A tuple where the first element is the cleaned string (or the original
        input if it is not a string), and the second element is a boolean
        indicating whether the string was modified.
    """
    if not isinstance(s, str):
        return s, False

    c = _re_combine_whitespace.sub(" ", s).strip()
    clean_string = _re_control_char.sub("", c)
    if clean_string == s:
        return s, False
    return clean_string, True


def is_quoted_string(s: str, strip: bool = False) -> tuple[bool, str]:
    """
    Checks if a given string is enclosed in quotes and optionally strips the quotes.

    The function determines whether a given string starts and ends with matching quotes,
    either single quotes (') or double quotes ("). If the string is quoted and
    the `strip` parameter is set to True, it removes the enclosing quotes and returns
    the unquoted string.

    Parameters:
    s : str
        The input string to check and possibly process.
    strip : bool, optional
        Indicates whether to remove the enclosing quotes if the string is quoted.
        Defaults to False.

    Returns:
    tuple[bool, str]
        A tuple where the first element is a boolean indicating whether the string
        is quoted, and the second element is the original string or the stripped
        version if `strip` is True.
    """
    is_quoted = False
    result = s
    if not isinstance(s, str):
        return is_quoted, result

    if s[0] == s[-1]:
        if s[0] in ['"', "'"]:
            is_quoted = True
            if strip:
                if s[0] == "'":
                    result = s.strip("'")
                elif s[0] == '"':
                    result = s.strip('"')
    return is_quoted, result


def is_numeric_string(s: str, convert: bool = False) -> tuple[bool, str | int | float]:
    """
    Checks if the given string represents a numeric value and optionally converts it.

    This function determines if the provided string represents a numeric value.
    If the input is numeric and the `convert` flag is set to True, it returns
    the numeric value converted to either an integer (if the float represents
    an integer) or a float. If the input is not numeric, it returns the original
    input string.

    Parameters
    ----------
    s : str
        The input string to check.
    convert : bool, optional
        A flag indicating whether to convert the numeric string to a numeric
        type (default is False).

    Returns
    -------
    tuple
        A tuple containing a boolean and the result:
            - A boolean indicating whether the input string is numeric or not.
            - The numeric value if `convert` is True and the string is numeric;
              otherwise, the original string.
    """
    is_numeric = False
    result = s
    f = None
    if not isinstance(s, str):
        return is_numeric, result
    try:
        f = float(s)
        is_numeric = True
    except ValueError:
        is_numeric = False

    if is_numeric and convert:
        result = int(f) if f.is_integer() else f

    return is_numeric, result


def custom_slug(s: str) -> str:
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", "", s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", "_", s)

    return s


def b64_encode(s: str | bytes) -> str:
    """
    Encodes a string or bytes into its Base64 representation.

    This function takes an input, either a string or bytes, and encodes it
    into its Base64 representation. If the input is a string, it is first
    encoded into bytes using UTF-8 encoding. The resulting Base64 encoded
    value is returned as a string.

    Args:
        s: The input to encode, which can be either a string or bytes.

    Returns:
        The Base64 encoded representation of the input as a string.
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    return base64.b64encode(s).decode("utf-8")


def b64_decode(s: str) -> bytes:
    """
    Decodes a Base64 encoded string to its original binary format.

    This function takes a Base64 encoded string and decodes it to its
    original bytes form. Base64 encoding may omit padding characters, so
    the function ensures the input is properly padded before decoding.

    Parameters:
    s: str
        A Base64 encoded string that needs to be decoded.

    Returns:
    bytes
        The decoded binary data.

    Raises:
    ValueError
        If the input string contains invalid Base64 characters.
    """
    pad = "=" * (-len(s) % 4)
    return base64.b64decode(s + pad)


def calc_hash(*args: Any) -> str:
    """
    Calculate and return a SHA-1 hash for the given arguments.

    This function joins the provided arguments into a single string, encodes it
    using UTF-16, and calculates the SHA-1 hash of the resulting bytes.

    Args:
        *args: A variable number of arguments to include in the hash.

    Returns:
        str: The computed SHA-1 hash as a hexadecimal string.
    """
    s = "_".join(map(str, args))
    return hashlib.sha1(s.encode("utf-16")).hexdigest()


def generate_random_password(n: int = 10) -> str:
    """
    Generates a random password meeting specific criteria for complexity. The
    function ensures the password contains at least one lowercase letter, one
    uppercase letter, and at least three numeric digits. The length of the
    password can be customized using the 'n' parameter.

    Parameters:
        n (int): Length of the password to be generated. Default is 10.

    Returns:
        str: A randomly generated password that meets the specified criteria.
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(n))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3
        ):
            break
    return password


def generate_crypto_password(n: int = 32) -> str:
    """
    Generates a cryptographically secure password string.

    This function uses the `secrets` module to generate a cryptographically
    secure random string with a specified length. The default length of
    the password is 32 characters.

    Parameters:
    n: int, optional
        Length of the password string. Defaults to 32.

    Returns:
    str
        A cryptographically secure randomly generated password string.
    """
    return secrets.token_urlsafe(n)
