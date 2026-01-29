# import libs
import logging
from typing import List, Optional, Union, Tuple, Dict, Literal, cast, Any
from pythermodb_settings.models import Component, Temperature, ComponentKey, CustomProp
from pyThermoLinkDB.thermo import Source
from pythermodb_settings.utils import set_component_id
# locals
from .hsg import HSG
from ..utils.tools import _select_nasa_type
from ..configs.constants import (
    NASARangeType,
    NASAType,
    TEMPERATURE_BREAK_NASA7_200_K,
    TEMPERATURE_BREAK_NASA7_1000_K,
    TEMPERATURE_BREAK_NASA7_6000_K,
    TEMPERATURE_BREAK_NASA9_200_K,
    TEMPERATURE_BREAK_NASA9_1000_K,
    TEMPERATURE_BREAK_NASA9_6000_K,
)

# NOTE: setup logger
logger = logging.getLogger(__name__)


class HSGs:
    """
    Class for handling multiple HSG objects.
    """
    # SECTION: Attributes

    def __init__(
        self,
        source: Source,
        components: List[Component],
        component_key: ComponentKey,
        nasa_type: NASAType
    ) -> None:
        """
        Initialize HSGs object.

        Parameters
        ----------
        source : Source
            The data source for the HSG calculations.
        components : List[Component]
            A list of Component objects for which to create HSGs.
        component_key : ComponentKey
            The key to identify components.
        nasa_type : NASAType
            The type of NASA polynomial to use ("nasa7" or "nasa9").
        """
        # NOTE: set
        self.source = source
        self.components = components
        self.component_key = component_key
        self.nasa_type = nasa_type

        # SECTION: set methods
        self.component_ids = [
            set_component_id(
                component=component,
                component_key=component_key
            )
            for component in components
        ]

        # NOTE: reaction component ids
        self.reaction_component_ids = {}
        # iterate over components
        for comp_id, component in zip(self.component_ids, components):
            # set
            self.reaction_component_ids[comp_id] = f"{component.formula}-{component.state}"

        # SECTION: set nasa temperature break value (range)
        # ! min [1000 K]
        nasa_temperature_break_min_value = TEMPERATURE_BREAK_NASA7_1000_K if self.nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_1000_K
        self.nasa_temperature_break_min = Temperature(
            value=nasa_temperature_break_min_value,
            unit="K"
        )

        # ! max [6000 K]
        nasa_temperature_break_max_value = TEMPERATURE_BREAK_NASA7_6000_K if self.nasa_type == "nasa7" else TEMPERATURE_BREAK_NASA9_6000_K
        self.nasa_temperature_break_max = Temperature(
            value=nasa_temperature_break_max_value,
            unit="K"
        )

        # SECTION: build hsgs
        self.components_hsg = self.build_components_hsg()

    def build_components_hsg(
        self,
    ) -> Dict[str, HSG]:
        """
        Build HSG objects for all components.

        Returns
        -------
        Dict[str, HSG]
            A dictionary with component IDs as keys and HSG objects as values.
        """
        # NOTE: init
        hsgs: Dict[str, HSG] = {}

        # NOTE: loop components
        for id, component in zip(self.component_ids, self.components):
            # NOTE: get hsg
            hsg = HSG(
                source=self.source,
                component=component,
                component_key=cast(ComponentKey, self.component_key),
                nasa_type=cast(NASAType, self.nasa_type),
            )

            # NOTE: set
            hsgs[id] = hsg

        # NOTE: return
        return hsgs

    def calc_components_hsg(
        self,
        temperature: Temperature,
        prop_name: Literal["enthalpy", "entropy", "gibbs", "heat_capacity"],
        reaction_ids: bool = False,
        **kwargs
    ) -> Optional[Dict[str, CustomProp]]:
        """
        Calculate the specified thermodynamic property for all components at a given temperature.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the property.
        prop_name : Literal["enthalpy", "entropy", "gibbs"]
            The property to calculate. Options are "enthalpy", "entropy", or "gibbs".
        reaction_ids : bool, optional
            Whether to use reaction component IDs as keys in the returned dictionary. Default is False.

        Returns
        -------
        Optional[Dict[str, CustomProp]]
            A dictionary with component IDs as keys and calculated property values as values.
            Returns None if an error occurs.
        """
        try:
            # SECTION: select nasa type
            nasa_type_selected = _select_nasa_type(
                temperature=temperature,
                break_temp_min=self.nasa_temperature_break_min,
                break_temp_max=self.nasa_temperature_break_max,
                nasa_type=cast(NASAType, self.nasa_type)
            )
            # >> cast
            nasa_type_selected = cast(
                NASARangeType,
                nasa_type_selected
            )

            # SECTION: calc hsgs
            # NOTE: init
            hsgs_data: Dict[str, Any] = {}

            # SECTION: loop hsgs
            for id, hsg in self.components_hsg.items():
                # NOTE: set methods
                if prop_name == "enthalpy":
                    prop_func = hsg.calc_absolute_enthalpy
                elif prop_name == "entropy":
                    prop_func = hsg.calc_absolute_entropy
                elif prop_name == "gibbs":
                    prop_func = hsg.calc_gibbs_free_energy
                elif prop_name == "heat_capacity":
                    prop_func = hsg.calc_heat_capacity
                else:
                    logger.error(f"Invalid prop_name: {prop_name}")
                    return None

                # NOTE: calc
                res = prop_func(
                    temperature=temperature,
                    nasa_type=nasa_type_selected
                )

                # >> check
                if res is None:
                    logger.warning(
                        f"{prop_name.capitalize()} calculation returned None for component ID {id} "
                        f"at temperature {temperature} K using {nasa_type_selected} coefficients."
                    )
                    continue

                # NOTE: set data based on component formula and state
                # >> set
                if reaction_ids:
                    hsgs_data[self.reaction_component_ids[id]] = res
                else:
                    hsgs_data[id] = res

            # NOTE: return
            return hsgs_data
        except Exception as e:
            logger.error(f"Error in calc_components_hsg: {e}")
            return None
