# import libs
import logging
from typing import Optional, Literal, cast, Dict
from pythermodb_settings.models import Temperature, Component, CustomProp, ComponentKey
from pyThermoLinkDB.models import ModelSource
from pyThermoLinkDB.thermo import Source
from pyreactlab_core.models.reaction import Reaction
from pythermodb_settings.utils import measure_time
# locals
from .core.hsg import HSG
from .core.hsgs import HSGs
from .docs.rxn_adapter import RXNAdapter
from .configs.constants import (
    NASAType,
    TEMPERATURE_BREAK_NASA7_1000_K,
    TEMPERATURE_BREAK_NASA7_6000_K,
    TEMPERATURE_BREAK_NASA9_1000_K,
    TEMPERATURE_BREAK_NASA9_6000_K,
    NASARangeType,
    BasisType
)
from .utils.tools import _select_nasa_type

# NOTE: set up logger
logger = logging.getLogger(__name__)


@measure_time
def H_T(
    component: Component,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    basis: BasisType = "molar",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the enthalpy H(T) at specified temperatures for a given component using NASA polynomials.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate enthalpy.
    temperature : Temperature
        The temperature at which to calculate enthalpy.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the component, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    basis : BasisType, optional
        The basis for the calculation ("molar" or "mass"), by default "molar".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated enthalpy as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # SECTION: hsg calculation
        hsg = HSG(
            source=Source_,
            component=component,
            component_key=component_key,
            nasa_type=nasa_type,
            basis=basis
        )

        # SECTION: set nasa temperature break value
        # ! min [1000K]
        nasa_temp_break_min_value = TEMPERATURE_BREAK_NASA7_1000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_1000_K
        nasa_temperature_break_min = Temperature(
            value=nasa_temp_break_min_value,
            unit="K"
        )

        # ! max [6000K]
        nasa_temp_break_max_value = TEMPERATURE_BREAK_NASA7_6000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_6000_K
        nasa_temperature_break_max = Temperature(
            value=nasa_temp_break_max_value,
            unit="K"
        )

        # SECTION: select nasa type
        nasa_type_selected = _select_nasa_type(
            temperature=temperature,
            break_temp_min=nasa_temperature_break_min,
            break_temp_max=nasa_temperature_break_max,
            nasa_type=cast(NASAType, nasa_type)
        )

        # >> cast
        nasa_type_selected = cast(
            NASARangeType,
            nasa_type_selected
        )

        # NOTE: Calculate enthalpy
        res = hsg.calc_absolute_enthalpy(
            temperature=temperature,
            nasa_type=nasa_type_selected
        )

        return res
    except Exception as e:
        logger.exception(
            f"Error calculating enthalpy for component {component} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def S_T(
    component: Component,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    basis: BasisType = "molar",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the entropy S(T) at specified temperatures for a given component using NASA polynomials.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate entropy.
    temperature : Temperature
        The temperature at which to calculate entropy.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the component, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    basis : BasisType, optional
        The basis for the calculation ("molar" or "mass"), by default "molar".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated entropy as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # SECTION: hsg calculation
        hsg = HSG(
            source=Source_,
            component=component,
            component_key=component_key,
            nasa_type=nasa_type,
            basis=basis
        )

        # SECTION: set nasa temperature break value
        # ! min [1000K]
        nasa_temp_break_min_value = TEMPERATURE_BREAK_NASA7_1000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_1000_K
        nasa_temperature_break_min = Temperature(
            value=nasa_temp_break_min_value,
            unit="K"
        )

        # ! max [6000K]
        nasa_temp_break_max_value = TEMPERATURE_BREAK_NASA7_6000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_6000_K
        nasa_temperature_break_max = Temperature(
            value=nasa_temp_break_max_value,
            unit="K"
        )

        # SECTION: select nasa type
        nasa_type_selected = _select_nasa_type(
            temperature=temperature,
            break_temp_min=nasa_temperature_break_min,
            break_temp_max=nasa_temperature_break_max,
            nasa_type=cast(NASAType, nasa_type)
        )

        # >> cast
        nasa_type_selected = cast(
            NASARangeType,
            nasa_type_selected
        )

        # NOTE: Calculate entropy
        res = hsg.calc_absolute_entropy(
            temperature=temperature,
            nasa_type=nasa_type_selected
        )

        return res
    except Exception as e:
        logger.exception(
            f"Error calculating entropy for component {component} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def G_T(
    component: Component,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    basis: BasisType = "molar",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the Gibbs free energy G(T) at specified temperatures for a given component using NASA polynomials.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate Gibbs free energy.
    temperature : Temperature
        The temperature at which to calculate Gibbs free energy.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the component, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    basis : BasisType, optional
        The basis for the calculation ("molar" or "mass"), by default "molar".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated Gibbs free energy as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # SECTION: hsg calculation
        hsg = HSG(
            source=Source_,
            component=component,
            component_key=component_key,
            nasa_type=nasa_type,
            basis=basis
        )

        # SECTION: set nasa temperature break value
        # ! min [1000K]
        nasa_temp_break_min_value = TEMPERATURE_BREAK_NASA7_1000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_1000_K
        nasa_temperature_break_min = Temperature(
            value=nasa_temp_break_min_value,
            unit="K"
        )

        # ! max [6000K]
        nasa_temp_break_max_value = TEMPERATURE_BREAK_NASA7_6000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_6000_K
        nasa_temperature_break_max = Temperature(
            value=nasa_temp_break_max_value,
            unit="K"
        )

        # SECTION: select nasa type
        nasa_type_selected = _select_nasa_type(
            temperature=temperature,
            break_temp_min=nasa_temperature_break_min,
            break_temp_max=nasa_temperature_break_max,
            nasa_type=cast(NASAType, nasa_type)
        )

        # >> cast
        nasa_type_selected = cast(
            NASARangeType,
            nasa_type_selected
        )

        # NOTE: Calculate Gibbs free energy
        res = hsg.calc_gibbs_free_energy(
            temperature=temperature,
            nasa_type=nasa_type_selected
        )

        return res
    except Exception as e:
        logger.exception(
            f"Error calculating Gibbs free energy for component {component} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def Cp_T(
    component: Component,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    basis: BasisType = "molar",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the heat capacity Cp(T) at specified temperatures for a given component using NASA polynomials.

    Parameters
    ----------
    component : Component
        The chemical component for which to calculate heat capacity.
    temperature : Temperature
        The temperature at which to calculate heat capacity.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the component, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    basis : BasisType, optional
        The basis for the calculation ("molar" or "mass"), by default "molar".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated heat capacity as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # SECTION: hsg calculation
        hsg = HSG(
            source=Source_,
            component=component,
            component_key=component_key,
            nasa_type=nasa_type,
            basis=basis
        )

        # SECTION: set nasa temperature break value
        # ! min [1000K]
        nasa_temp_break_min_value = TEMPERATURE_BREAK_NASA7_1000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_1000_K
        nasa_temperature_break_min = Temperature(
            value=nasa_temp_break_min_value,
            unit="K"
        )

        # ! max [6000K]
        nasa_temp_break_max_value = TEMPERATURE_BREAK_NASA7_6000_K if nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_6000_K
        nasa_temperature_break_max = Temperature(
            value=nasa_temp_break_max_value,
            unit="K"
        )

        # SECTION: select nasa type
        nasa_type_selected = _select_nasa_type(
            temperature=temperature,
            break_temp_min=nasa_temperature_break_min,
            break_temp_max=nasa_temperature_break_max,
            nasa_type=cast(NASAType, nasa_type)
        )

        # >> cast
        nasa_type_selected = cast(
            NASARangeType,
            nasa_type_selected
        )

        # NOTE: Calculate heat capacity
        res = hsg.calc_heat_capacity(
            temperature=temperature,
            nasa_type=nasa_type_selected
        )

        return res
    except Exception as e:
        logger.exception(
            f"Error calculating heat capacity for component {component} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def dG_rxn_STD(
    reaction: Reaction,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard Gibbs free energy change of a reaction ΔG(T) at a specified temperature.

    Parameters
    ----------
    reaction : Reaction
        The reaction for which to calculate the standard Gibbs free energy change.
    temperature : Temperature
        The temperature at which to calculate the standard Gibbs free energy change.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the components, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated standard Gibbs free energy change of the reaction as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # NOTE: components
        components = reaction.available_components

        # SECTION: hsgs calculation
        hsgs = HSGs(
            source=Source_,
            components=components,
            component_key=component_key,
            nasa_type=nasa_type
        )

        # NOTE: Calculate standard Gibbs free energy change of the reaction
        G_i_IG: Dict[str, CustomProp] | None = hsgs.calc_components_hsg(
            temperature=temperature,
            prop_name="gibbs",
            reaction_ids=True
        )

        if G_i_IG is None:
            logger.error(
                f"Failed to calculate Gibbs free energy for components in reaction: {reaction.reaction}"
            )
            return None

        # SECTION: calculate dG_rxn_STD
        rxn_adapter = RXNAdapter(
            reaction=reaction,
        )

        dG_rxn_STD = rxn_adapter.dG_rxn_std(
            G_i_IG=G_i_IG,
            **kwargs
        )

        return dG_rxn_STD
    except Exception as e:
        logger.exception(
            f"Error calculating standard Gibbs free energy change for reaction {reaction.reaction} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def dS_rxn_STD(
    reaction: Reaction,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard entropy change of a reaction ΔS(T) at a specified temperature.

    Parameters
    ----------
    reaction : Reaction
        The reaction for which to calculate the standard entropy change.
    temperature : Temperature
        The temperature at which to calculate the standard entropy change.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the components, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated standard entropy change of the reaction as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # NOTE: components
        components = reaction.available_components

        # SECTION: hsgs calculation
        hsgs = HSGs(
            source=Source_,
            components=components,
            component_key=component_key,
            nasa_type=nasa_type
        )

        # NOTE: Calculate standard entropy change of the reaction
        S_i_IG: Dict[str, CustomProp] | None = hsgs.calc_components_hsg(
            temperature=temperature,
            prop_name="entropy",
            reaction_ids=True
        )

        if S_i_IG is None:
            logger.error(
                f"Failed to calculate entropy for components in reaction: {reaction.reaction}"
            )
            return None

        # SECTION: calculate dS_rxn_STD
        rxn_adapter = RXNAdapter(
            reaction=reaction,
        )

        dS_rxn_STD = rxn_adapter.dS_rxn_std(
            S_i_IG=S_i_IG,
            **kwargs
        )

        return dS_rxn_STD
    except Exception as e:
        logger.exception(
            f"Error calculating standard entropy change for reaction {reaction.reaction} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def dH_rxn_STD(
    reaction: Reaction,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the standard enthalpy change of a reaction ΔH(T) at a specified temperature.

    Parameters
    ----------
    reaction : Reaction
        The reaction for which to calculate the standard enthalpy change.
    temperature : Temperature
        The temperature at which to calculate the standard enthalpy change.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the components, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated standard enthalpy change of the reaction as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # NOTE: components
        components = reaction.available_components

        # SECTION: hsgs calculation
        hsgs = HSGs(
            source=Source_,
            components=components,
            component_key=component_key,
            nasa_type=nasa_type
        )

        # NOTE: Calculate standard enthalpy change of the reaction
        H_i_IG: Dict[str, CustomProp] | None = hsgs.calc_components_hsg(
            temperature=temperature,
            prop_name="enthalpy",
            reaction_ids=True
        )

        if H_i_IG is None:
            logger.error(
                f"Failed to calculate enthalpy for components in reaction: {reaction.reaction}"
            )
            return None

        # SECTION: calculate dH_rxn_STD
        rxn_adapter = RXNAdapter(
            reaction=reaction,
        )

        dH_rxn_STD = rxn_adapter.dH_rxn_std(
            H_i_IG=H_i_IG,
            **kwargs
        )

        return dH_rxn_STD
    except Exception as e:
        logger.exception(
            f"Error calculating standard enthalpy change for reaction {reaction.reaction} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def Keq(
    reaction: Reaction,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the equilibrium constant Keq(T) at a specified temperature.

    Parameters
    ----------
    reaction : Reaction
        The reaction for which to calculate the equilibrium constant.
    temperature : Temperature
        The temperature at which to calculate the equilibrium constant.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the components, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated equilibrium constant as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # NOTE: components
        components = reaction.available_components

        # SECTION: hsgs calculation
        hsgs = HSGs(
            source=Source_,
            components=components,
            component_key=component_key,
            nasa_type=nasa_type
        )

        # NOTE: calculate standard Gibbs free energy change of the reaction
        dG_rxn_STD_ = dG_rxn_STD(
            reaction=reaction,
            temperature=temperature,
            model_source=model_source,
            component_key=component_key,
            nasa_type=nasa_type,
            **kwargs
        )

        # >> check
        if dG_rxn_STD_ is None:
            logger.error(
                f"Failed to calculate standard Gibbs free energy change for reaction: {reaction.reaction}"
            )
            return None

        # SECTION: calculate Keq
        rxn_adapter = RXNAdapter(
            reaction=reaction,
        )

        Keq = rxn_adapter.Keq(
            dG_rxn_STD=dG_rxn_STD_,
            temperature=temperature,
            **kwargs
        )

        return Keq
    except Exception as e:
        logger.exception(
            f"Error calculating equilibrium constant for reaction {reaction.reaction} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None


@measure_time
def Keq_vh_shortcut(
    reaction: Reaction,
    temperature: Temperature,
    model_source: ModelSource,
    component_key: ComponentKey = "Name-Formula",
    nasa_type: NASAType = "nasa9",
    **kwargs
) -> Optional[CustomProp]:
    """
    Calculate the equilibrium constant Keq(T) using van't Hoff shortcut at a specified temperature.

    Parameters
    ----------
    reaction : Reaction
        The reaction for which to calculate the equilibrium constant.
    temperature : Temperature
        The temperature at which to calculate the equilibrium constant.
    model_source : ModelSource
        The source of the thermodynamic model data.
    component_key : ComponentKey, optional
        The key type used to identify the components, by default "Name-Formula".
    nasa_type : NASAType, optional
        The type of NASA polynomial to use ("nasa7" or "nasa9"), by default "nasa9".
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns
    -------
    Optional[CustomProp]
        The calculated equilibrium constant as a CustomProp, or None if calculation fails.
    """
    try:
        # SECTION: input preparation
        # NOTE: standard temperature 298.15 K
        standard_temperature = Temperature(
            value=298.15,
            unit="K"
        )

        # SECTION: Prepare source
        Source_ = Source(
            model_source=model_source,
            component_key=component_key
        )

        # NOTE: components
        components = reaction.available_components

        # SECTION: hsgs calculation
        hsgs = HSGs(
            source=Source_,
            components=components,
            component_key=component_key,
            nasa_type=nasa_type
        )

        # NOTE: Calculate standard enthalpy change of the reaction
        # ! Using H at standard temperature
        dH_rxn_STD_ = dH_rxn_STD(
            reaction=reaction,
            temperature=standard_temperature,
            model_source=model_source,
            component_key=component_key,
            nasa_type=nasa_type,
            **kwargs
        )

        # >> check
        if dH_rxn_STD_ is None:
            logger.error(
                f"Failed to calculate standard enthalpy change for reaction: {reaction.reaction}"
            )
            return None

        # NOTE: Calculate gibbs free energy change at standard temperature
        # ! Using G at standard temperature
        dG_rxn_STD_ = dG_rxn_STD(
            reaction=reaction,
            temperature=standard_temperature,
            model_source=model_source,
            component_key=component_key,
            nasa_type=nasa_type,
            **kwargs
        )

        # >> check
        if dG_rxn_STD_ is None:
            logger.error(
                f"Failed to calculate standard Gibbs free energy change for reaction: {reaction.reaction}"
            )
            return None

        # SECTION: calculate Keq using van't Hoff shortcut
        rxn_adapter = RXNAdapter(
            reaction=reaction,
        )

        # NOTE: Calculate equilibrium constant at standard temperature
        Keq_STD_ = rxn_adapter.Keq(
            dG_rxn_STD=dG_rxn_STD_,
            temperature=standard_temperature,
            **kwargs
        )

        # >> check
        if Keq_STD_ is None:
            logger.error(
                f"Failed to calculate standard equilibrium constant for reaction: {reaction.reaction}"
            )
            return None

        Keq_vh_shortcut = rxn_adapter.Keq_vh_shortcut(
            Keq_STD=Keq_STD_,
            dH_rxn_STD=dH_rxn_STD_,
            temperature=temperature,
            **kwargs
        )

        return Keq_vh_shortcut
    except Exception as e:
        logger.exception(
            f"Error calculating equilibrium constant using van't Hoff shortcut for reaction {reaction.reaction} at temperature {temperature.value} K using {nasa_type} coefficients: {e}")
        return None
