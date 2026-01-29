# import libs
import logging
from typing import Optional, Dict, List, Any, cast, Literal
from pyThermoLinkDB.models.component_models import ComponentEquationSource
from pythermodb_settings.models import Component, Temperature, ComponentKey, CustomProp
from pythermodb_settings.utils import set_component_id
from pyThermoLinkDB.thermo import Source
from pyThermoDB.core import TableEquation
from pyThermoCalcDB.thermo.enthalpy import (
    En_IG_NASA9_polynomial,
    En_IG_NASA9_polynomial_range,
    En_IG_NASA9_polynomial_ranges,
    En_IG_NASA7_polynomial,
    En_IG_NASA7_polynomial_range,
    En_IG_NASA7_polynomial_ranges,
)
from pyThermoCalcDB.thermo.entropy import (
    S_IG_NASA9_polynomial,
    S_IG_NASA9_polynomial_range,
    S_IG_NASA9_polynomial_ranges,
    S_IG_NASA7_polynomial,
    S_IG_NASA7_polynomial_range,
    S_IG_NASA7_polynomial_ranges,
)
from pyThermoCalcDB.thermo.gibbs import (
    GiFrEn_IG,
    GiFrEn_IG_ranges
)
from pyThermoCalcDB.thermo.heat_capacity import (
    Cp_IG_NASA9_polynomial,
    Cp_IG_NASA7_polynomial
)
# locals
from ..thermo.extractor import DataExtractor
from ..utils.tools import _require_coeffs, _energy_or_entropy_to_mass_basis
from ..configs.constants import NASAType, NASARangeType, BasisType

# NOTE: set up logger
logger = logging.getLogger(__name__)


class HSG(DataExtractor):
    """
    Class for extracting NASA polynomial coefficients from a data source.

    Attributes
    ----------
    req_coeffs_NASA7 : tuple
        Required NASA7 coefficient names: ('a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7').
    req_coeffs_NASA9 : tuple
        Required NASA9 coefficient names: ('a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'b1', 'b2').
    component : Component
        The component for which data is extracted.
    component_key : ComponentKey
        The key type used to identify the component.
    component_id : str
        The unique identifier for the component.
    nasa9_200_1000_coefficients : Optional[Dict[str, float]]
        NASA9 coefficients for the temperature range 200-1000 K.
    nasa9_1000_6000_coefficients : Optional[Dict[str, float]]
        NASA9 coefficients for the temperature range 1000-6000 K.
    nasa9_6000_20000_coefficients : Optional[Dict[str, float]]
        NASA9 coefficients for the temperature range 6000-20000 K.
    nasa7_200_1000_coefficients : Optional[Dict[str, float]]
        NASA7 coefficients for the temperature range 200-1000 K.
    nasa7_1000_6000_coefficients : Optional[Dict[str, float]]
        NASA7 coefficients for the temperature range 1000-6000 K.
    nasa7_6000_20000_coefficients : Optional[Dict[str, float]]
        NASA7 coefficients for the temperature range 6000-20000 K.
    """
    # SECTION: Attributes
    req_coeffs_NASA7 = ("a1", "a2", "a3", "a4", "a5", "a6", "a7")
    req_coeffs_NASA9 = ("a1", "a2", "a3", "a4", "a5", "a6", "a7", "b1", "b2")

    # NOTE: props
    req_props = ("MW",)
    _props = None

    def __init__(
            self,
            source: Source,
            component: Component,
            component_key: ComponentKey,
            nasa_type: NASAType,
            basis: BasisType = "molar",
    ):
        """
        Initialize the HSG extractor with the given data source and component key.

        Parameters
        ----------
        source : Source
            The data source from which to extract information.
        component : Component
            The component for which to extract data.
        component_key : ComponentKey
            The key type used to identify the component.
        nasa_type : NASAType
            The type of NASA polynomial to extract.
        basis : BasisType, optional
            The basis type for the calculations (default is "molar").
        """
        # LINK: initialize parent
        super().__init__(source=source)

        # NOTE: set component
        self.component = component
        # NOTE: set component key
        self.component_key = component_key
        # NOTE: set basis
        self.basis = basis

        # SECTION: set component id
        self.component_id: str = cast(
            str,
            set_component_id(
                component=self.component,
                component_key=self.component_key
            )
        )

        # SECTION: retrieve data
        # NOTE: extract NASA9 coefficients
        if nasa_type == "nasa9":
            self.nasa9_200_1000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa9_200_1000_K",
            )
            self.nasa9_1000_6000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa9_1000_6000_K",
            )
            self.nasa9_6000_20000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa9_6000_20000_K",
            )

        # NOTE: extract NASA7 coefficients
        if nasa_type == "nasa7":
            self.nasa7_200_1000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa7_200_1000_K",
            )
            self.nasa7_1000_6000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa7_1000_6000_K",
            )
            self.nasa7_6000_20000_coefficients: Optional[Dict[str, float]] = self._extract_nasa_coefficients(
                prop_name="nasa7_6000_20000_K",
            )

    @property
    def props(self) -> Optional[Dict[str, float]]:
        """
        Get the component properties.

        Returns
        -------
        Optional[Dict[str, float]]
            The component properties if available, otherwise None.
        """
        return self._props

    @props.setter
    def props(self, value: Optional[Dict[str, float]]):
        self._props = value

    def _extract_nasa_coefficients(
            self,
            prop_name: NASARangeType,
    ) -> Optional[Dict[str, float]]:
        """
        Extract NASA polynomial coefficients for the specified property.

        Parameters
        ----------
        prop_name : NASARangeType
            The name of the property for which to extract the coefficients.

        Returns
        -------
        Optional[Dict[str, float]]
            A dictionary containing the NASA polynomial coefficients if available, otherwise None.
        """
        try:
            # NOTE: extract formation data
            # >> get equation source
            eq_src: ComponentEquationSource | None = self._get_equation_source(
                component=self.component,
                component_key=cast(ComponentKey, self.component_key),
                prop_name=prop_name,
            )

            if eq_src is None:
                return None

            # NOTE: get equation
            equation: TableEquation = eq_src.source

            # >> get coefficients
            coefficients: Dict[str, float] = equation.parms_values

            return coefficients
        except Exception as e:
            logger.exception(
                f"Error extracting NASA9 coefficients: {e}")
            return None

    def _set_nasa_coefficients(
            self,
            nasa_type: NASARangeType,
    ) -> Optional[Dict[str, float]]:
        try:
            if nasa_type == "nasa9_200_1000_K":
                # ! get coeffs [from 200 to 1000 K]
                coeffs = self.nasa9_200_1000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA9)

            elif nasa_type == "nasa9_1000_6000_K":
                # ! get coeffs [from 1000 to 6000 K]
                coeffs = self.nasa9_1000_6000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA9)

            elif nasa_type == "nasa9_6000_20000_K":
                # ! get coeffs [from 6000 to 20000 K]
                coeffs = self.nasa9_6000_20000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA9)

            elif nasa_type == "nasa7_200_1000_K":
                # ! get coeffs [from 200 to 1000 K]
                coeffs = self.nasa7_200_1000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA7)

            elif nasa_type == "nasa7_1000_6000_K":
                # ! get coeffs [from 1000 to 6000 K]
                coeffs = self.nasa7_1000_6000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA7)

            elif nasa_type == "nasa7_6000_20000_K":
                # ! get coeffs [from 6000 to 20000 K]
                coeffs = self.nasa7_6000_20000_coefficients
                # >> check coeffs
                if coeffs is None:
                    return None

                pack = _require_coeffs(coeffs, self.req_coeffs_NASA7)
            else:
                # ! invalid type
                logger.error(f"Invalid NASA type: {nasa_type}")
                return None

            if coeffs is None:
                logger.warning(
                    f"No NASA coefficients available for type {nasa_type}.")
                return None

            # NOTE: pack coeffs
            if pack is None:
                return None

            # NOTE: set props
            self.props = self._set_props(coeffs)

            return pack
        except Exception as e:
            logger.exception(
                f"Error setting NASA coefficients: {e}")
            return None

    def _set_props(
            self,
            coeffs
    ) -> Optional[Dict[str, float]]:
        """
        Extract required properties from the coefficient pack.
        """
        try:
            # SECTION: set properties
            return _require_coeffs(coeffs, self.req_props)
        except Exception as e:
            logger.exception(
                f"Error setting properties: {e}")
            return None

    def calc_absolute_enthalpy(
            self,
            temperature: Temperature,
            nasa_type: NASARangeType,
    ) -> Optional[CustomProp]:
        """
        Calculate the enthalpy at the specified temperature using the NASA polynomial coefficients.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the enthalpy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.

        Returns
        -------
        Optional[CustomProp]
            The calculated enthalpy if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # SECTION: calculate enthalpy
            if nasa_type == "nasa9_200_1000_K" or nasa_type == "nasa9_1000_6000_K" or nasa_type == "nasa9_6000_20000_K":
                enthalpy = En_IG_NASA9_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"],
                    temperature=temperature
                )
            elif nasa_type == "nasa7_200_1000_K" or nasa_type == "nasa7_1000_6000_K" or nasa_type == "nasa7_6000_20000_K":
                enthalpy = En_IG_NASA7_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    temperature=temperature
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return None

            # NOTE: prepare return
            if enthalpy is None:
                logger.warning(
                    f"Enthalpy calculation returned None for type {nasa_type} at temperature {temperature}.")
                return None

            # NOTE: convert to mass basis if needed
            if (
                self.basis == "mass" and
                self.props is not None and
                "MW" in self.props
            ):
                enthalpy = _energy_or_entropy_to_mass_basis(
                    value=enthalpy,
                    mw_g_per_mol=self.props["MW"]
                )

            return enthalpy
        except Exception as e:
            logger.exception(
                f"Error calculating enthalpy at {temperature} K using {nasa_type} coefficients: {e}")
            return None

    def calc_absolute_entropy(
            self,
            temperature: Temperature,
            nasa_type: NASARangeType,
    ) -> Optional[CustomProp]:
        """
        Calculate the entropy at the specified temperature using the NASA polynomial coefficients.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the entropy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.
        Returns
        -------
        Optional[CustomProp]
            The calculated entropy if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # SECTION: calculate entropy
            if nasa_type == "nasa9_200_1000_K" or nasa_type == "nasa9_1000_6000_K" or nasa_type == "nasa9_6000_20000_K":
                entropy = S_IG_NASA9_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"],
                    temperature=temperature
                )
            elif nasa_type == "nasa7_200_1000_K" or nasa_type == "nasa7_1000_6000_K" or nasa_type == "nasa7_6000_20000_K":
                entropy = S_IG_NASA7_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    temperature=temperature
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return None

            # NOTE: prepare return
            if entropy is None:
                logger.warning(
                    f"Entropy calculation returned None for type {nasa_type} at temperature {temperature}.")
                return None

            # NOTE: convert to mass basis if needed
            if (
                self.basis == "mass" and
                self.props is not None and
                "MW" in self.props
            ):
                entropy = _energy_or_entropy_to_mass_basis(
                    value=entropy,
                    mw_g_per_mol=self.props["MW"]
                )

            return entropy
        except Exception as e:
            logger.exception(
                f"Error calculating entropy at {temperature} K using {nasa_type} coefficients: {e}")
            return None

    def calc_gibbs_free_energy(
            self,
            temperature: Temperature,
            nasa_type: NASARangeType,
    ) -> Optional[CustomProp]:
        """
        Calculate the Gibbs free energy at the specified temperature using the NASA polynomial coefficients.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the Gibbs free energy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.
        Returns
        -------
        Optional[CustomProp]
            The calculated Gibbs free energy if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # NOTE: select method
            method = "NASA9" if "nasa9" in nasa_type else "NASA7"

            # SECTION: calculate Gibbs free energy
            if method == "NASA9":
                gibbs_free_energy = GiFrEn_IG(
                    method=method,
                    temperature=temperature,
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"]
                )
            else:
                gibbs_free_energy = GiFrEn_IG(
                    method=method,
                    temperature=temperature,
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"]
                )

            # NOTE: prepare return
            if gibbs_free_energy is None:
                logger.warning(
                    f"Gibbs free energy calculation returned None for type {nasa_type} at temperature {temperature}.")
                return None

            # NOTE: convert to mass basis if needed
            if (
                self.basis == "mass" and
                self.props is not None and
                "MW" in self.props
            ):
                gibbs_free_energy = _energy_or_entropy_to_mass_basis(
                    value=gibbs_free_energy,
                    mw_g_per_mol=self.props["MW"]
                )

            return gibbs_free_energy
        except Exception as e:
            logger.exception(
                f"Error calculating Gibbs free energy at {temperature} K using {nasa_type} coefficients: {e}")
            return None

    def calc_heat_capacity(
            self,
            temperature: Temperature,
            nasa_type: NASARangeType,
    ) -> Optional[CustomProp]:
        """
        Calculate the heat capacity at the specified temperature using the NASA polynomial coefficients.

        Parameters
        ----------
        temperature : Temperature
            The temperature at which to calculate the heat capacity.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.
        Returns
        -------
        Optional[CustomProp]
            The calculated heat capacity if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # SECTION: calculate heat capacity
            if nasa_type == "nasa9_200_1000_K" or nasa_type == "nasa9_1000_6000_K" or nasa_type == "nasa9_6000_20000_K":
                heat_capacity = Cp_IG_NASA9_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"],
                    temperature=temperature
                )
            elif nasa_type == "nasa7_200_1000_K" or nasa_type == "nasa7_1000_6000_K" or nasa_type == "nasa7_6000_20000_K":
                heat_capacity = Cp_IG_NASA7_polynomial(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    temperature=temperature
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return None

            # NOTE: prepare return
            if heat_capacity is None:
                logger.warning(
                    f"Heat capacity calculation returned None for type {nasa_type} at temperature {temperature}.")
                return None

            # NOTE: convert to mass basis if needed
            if (
                self.basis == "mass" and
                self.props is not None and
                "MW" in self.props
            ):
                heat_capacity = _energy_or_entropy_to_mass_basis(
                    value=heat_capacity,
                    mw_g_per_mol=self.props["MW"]
                )

            return heat_capacity
        except Exception as e:
            logger.exception(
                f"Error calculating heat capacity at {temperature} K using {nasa_type} coefficients: {e}")
            return None

    def calc_absolute_enthalpy_range(
            self,
            temperatures: List[Temperature],
            nasa_type: NASARangeType,
    ):
        """
        Calculate the enthalpy over a range of temperatures using the NASA polynomial coefficients.

        Parameters
        ----------
        temperatures : List[Temperature]
            The list of temperatures at which to calculate the enthalpy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.

        Returns
        -------
        Optional[Dict[str, Any]]
            The calculated enthalpy values if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # SECTION: calculate enthalpy range
            if nasa_type == "nasa9_200_1000_K" or nasa_type == "nasa9_1000_6000_K" or nasa_type == "nasa9_6000_20000_K":
                enthalpy_range = En_IG_NASA9_polynomial_ranges(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"],
                    temperatures=temperatures
                )
            elif nasa_type == "nasa7_200_1000_K" or nasa_type == "nasa7_1000_6000_K" or nasa_type == "nasa7_6000_20000_K":
                enthalpy_range = En_IG_NASA7_polynomial_ranges(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    temperatures=temperatures
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return

            # NOTE: prepare return
            if enthalpy_range is None:
                logger.warning(
                    f"Enthalpy range calculation returned None for type {nasa_type} at temperatures {temperatures}.")
                return None

            return enthalpy_range
        except Exception as e:
            logger.exception(
                f"Error calculating enthalpy range at temperatures {temperatures} K using {nasa_type} coefficients: {e}")
            return None

    def calc_absolute_entropy_range(
            self,
            temperatures: List[Temperature],
            nasa_type: NASARangeType,
    ):
        """
        Calculate the entropy over a range of temperatures using the NASA polynomial coefficients.

        Parameters
        ----------
        temperatures : List[Temperature]
            The list of temperatures at which to calculate the entropy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.

        Returns
        -------
        Optional[Dict[str, Any]]
            The calculated entropy values if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # SECTION: calculate entropy range
            if nasa_type == "nasa9_200_1000_K" or nasa_type == "nasa9_1000_6000_K" or nasa_type == "nasa9_6000_20000_K":
                entropy_range = S_IG_NASA9_polynomial_ranges(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"],
                    temperatures=temperatures
                )
            elif nasa_type == "nasa7_200_1000_K" or nasa_type == "nasa7_1000_6000_K" or nasa_type == "nasa7_6000_20000_K":
                entropy_range = S_IG_NASA7_polynomial_ranges(
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    temperatures=temperatures
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return

            # NOTE: prepare return
            if entropy_range is None:
                logger.warning(
                    f"Entropy range calculation returned None for type {nasa_type} at temperatures {temperatures}.")
                return None

            return entropy_range
        except Exception as e:
            logger.exception(
                f"Error calculating entropy range at temperatures {temperatures} K using {nasa_type} coefficients: {e}")
            return None

    def calc_gibbs_free_energy_range(
            self,
            temperatures: List[Temperature],
            nasa_type: NASARangeType,
    ):
        """
        Calculate the Gibbs free energy over a range of temperatures using the NASA polynomial coefficients.

        Parameters
        ----------
        temperatures : List[Temperature]
            The list of temperatures at which to calculate the Gibbs free energy.
        nasa_type : NASARangeType
            The type of NASA polynomial to use for the calculation.

        Returns
        -------
        Optional[Dict[str, Any]]
            The calculated Gibbs free energy values if coefficients are available, otherwise None.
        """
        try:
            # SECTION: get coeffs
            pack = self._set_nasa_coefficients(nasa_type=nasa_type)

            # NOTE: pack coeffs
            if pack is None:
                return None

            # NOTE: select method
            method = "NASA9" if "nasa9" in nasa_type else "NASA7"

            # SECTION: calculate Gibbs free energy range
            if method == "NASA9":
                gibbs_free_energy_range = GiFrEn_IG_ranges(
                    method=method,
                    temperatures=temperatures,
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"],
                    b1=pack["b1"],
                    b2=pack["b2"]
                )
            elif method == "NASA7":
                gibbs_free_energy_range = GiFrEn_IG_ranges(
                    method=method,
                    temperatures=temperatures,
                    a1=pack["a1"],
                    a2=pack["a2"],
                    a3=pack["a3"],
                    a4=pack["a4"],
                    a5=pack["a5"],
                    a6=pack["a6"],
                    a7=pack["a7"]
                )
            else:
                logger.error(f"Invalid NASA type: {nasa_type}")
                return

            # NOTE: prepare return
            if gibbs_free_energy_range is None:
                logger.warning(
                    f"Gibbs free energy range calculation returned None for type {nasa_type} at temperatures {temperatures}.")
                return None

            return gibbs_free_energy_range
        except Exception as e:
            logger.exception(
                f"Error calculating Gibbs free energy range at temperatures {temperatures} K using {nasa_type} coefficients: {e}")
            return None
