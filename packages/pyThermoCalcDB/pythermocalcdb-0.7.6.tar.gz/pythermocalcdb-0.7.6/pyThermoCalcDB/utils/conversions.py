# import libs
import logging
from typing import List, Optional, Dict, Any
from pythermodb_settings.models import Temperature
import pycuc

# NOTE: logger setup
logger = logging.getLogger(__name__)


def _to_J__mol(
    value: float,
    from_unit: str,
    **kwargs
) -> float:
    """
    Convert energy value to J/mol.

    Parameters
    ----------
    value : float
        The energy value to convert.
    from_unit : str
        The unit of the input energy value.

    Returns
    -------
    float
        The energy value in J/mol.
    """
    try:
        converted_value = pycuc.convert_from_to(
            value=value,
            from_unit=from_unit,
            to_unit="J/mol",
        )
        return converted_value
    except Exception as e:
        logger.error(f"Error converting energy to J/mol: {e}")
        raise


def _to_kelvin(temperature: Temperature) -> float:
    """Return temperature value in K."""
    T_value = temperature.value
    T_unit = temperature.unit.strip()
    if T_unit != "K":
        T_value = pycuc.convert_from_to(
            value=T_value, from_unit=T_unit, to_unit="K")
    return float(T_value)
