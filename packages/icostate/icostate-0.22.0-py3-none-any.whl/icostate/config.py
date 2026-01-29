"""Load configuration data"""

# -- Imports ------------------------------------------------------------------

from dynaconf import Dynaconf, Validator
from netaddr import AddrFormatError, EUI


def is_valid_eui(text: str) -> bool:
    """Check if the given text is a valid EUI

    Args:

        text:

            The text that should be checked

    Returns:

        - ``True``, if the text contains a valid EUI
        - ``False``, otherwise

    """

    try:
        EUI(text)
    except AddrFormatError:
        return False

    return True


# -- Attributes ---------------------------------------------------------------

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    validators=[
        Validator(
            "sensor_node.eui",
            must_exist=True,
            condition=is_valid_eui,
            messages={
                "condition": "The value “{value}” is not a valid EUI",
            },
        )
    ],
    settings_files=["settings.yaml"],
)
