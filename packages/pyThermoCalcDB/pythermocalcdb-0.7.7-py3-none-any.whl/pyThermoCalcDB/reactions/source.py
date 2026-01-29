# import libs
import logging
from typing import List, Optional, Dict, Any, Callable
from pyreactlab_core.models.reaction import Reaction
from pythermodb_settings.models import Temperature, CustomProp
from pythermodb_settings.utils import measure_time
# locals
from .rxn import RXN

# NOTE: logger setup
LOGGER = logging.getLogger(__name__)


def rxn(
    reaction: Reaction,
) -> RXN:
    """
    Create a RXN object from a Reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.

    Returns
    -------
    RXN
        The RXN object.
    """
    return RXN(reaction=reaction)


@measure_time
def dH_rxn_STD(
    reaction: Reaction,
    H_i_IG: Dict[str, Any],
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard enthalpy change of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    H_i_IG : Dict[str, Any]
        A dictionary of standard enthalpies of formation for each component.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The standard enthalpy change of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.dH_rxn_STD(H_i_IG=H_i_IG)
    except Exception as e:
        LOGGER.error(f"Error in dH_STD calculation: {e}")
        return None


@measure_time
def dG_rxn_STD(
    reaction: Reaction,
    G_i_IG: Dict[str, Any],
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard Gibbs free energy change of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    G_i_IG : Dict[str, Any]
        A dictionary of standard Gibbs free energies of formation for each component.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The standard Gibbs free energy change of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.dG_rxn_STD(G_i_IG=G_i_IG)
    except Exception as e:
        LOGGER.error(f"Error in dG_STD calculation: {e}")
        return None


@measure_time
def dS_rxn_STD(
    reaction: Reaction,
    S_i_IG: Dict[str, Any],
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard entropy change of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    S_i_IG : Dict[str, Any]
        A dictionary of standard entropies for each component.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The standard entropy change of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.dS_rxn_STD(S_i_IG=S_i_IG)
    except Exception as e:
        LOGGER.error(f"Error in dS_STD calculation: {e}")
        return None


@measure_time
def Keq(
    reaction: Reaction,
    dG_rxn_STD: CustomProp,
    temperature: Temperature,
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the equilibrium constant of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    dG_rxn_STD : CustomProp
        The standard Gibbs free energy change of the reaction.
    temperature : Temperature
        The temperature at which to calculate the equilibrium constant.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The equilibrium constant of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.Keq(
            dG_rxn_STD=dG_rxn_STD,
            temperature=temperature,
        )
    except Exception as e:
        LOGGER.error(f"Error in Keq calculation: {e}")
        return None


@measure_time
def Keq_vh(
    reaction: Reaction,
    Keq_STD: CustomProp,
    dH_rxn_STD_func: Callable[[Temperature], Optional[CustomProp]],
    temperature: Temperature,
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the temperature-dependent equilibrium constant of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    Keq_STD : CustomProp
        The standard equilibrium constant of the reaction.
    dH_rxn_STD_func : Callable[[Temperature], Optional[CustomProp]]
        A function that returns the standard enthalpy change of the reaction at a given temperature.
    temperature : Temperature
        The temperature at which to calculate the equilibrium constant.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The temperature-dependent equilibrium constant of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.Keq_vh(
            Keq_STD=Keq_STD,
            dH_rxn_STD_func=dH_rxn_STD_func,
            temperature=temperature,
        )
    except Exception as e:
        LOGGER.error(f"Error in Keq_T calculation: {e}")
        return None


@measure_time
def Keq_vh_shortcut(
    reaction: Reaction,
    Keq_STD: CustomProp,
    dH_rxn_STD: CustomProp,
    temperature: Temperature,
    **kwargs
):
    """
    Calculate the temperature-dependent equilibrium constant of the reaction.

    Parameters
    ----------
    reaction : Reaction
        The reaction object.
    Keq_STD : CustomProp
        The standard equilibrium constant of the reaction.
    dH_rxn_STD : CustomProp
        The standard enthalpy change of the reaction.
    temperature : Temperature
        The temperature at which to calculate the equilibrium constant.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The temperature-dependent equilibrium constant of the reaction.
    """
    try:
        rxn = RXN(reaction=reaction)
        return rxn.Keq_vh_shortcut(
            Keq_STD=Keq_STD,
            dH_rxn_STD=dH_rxn_STD,
            temperature=temperature,
        )
    except Exception as e:
        LOGGER.error(f"Error in Keq_T calculation: {e}")
        return None
