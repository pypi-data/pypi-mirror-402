# import libs
import re
import logging
from typing import Optional, Dict, List, Any, cast, Literal, Tuple
from pythermodb_settings.models import Temperature, CustomProp
import pycuc
# local
from pythermocalcdb_nasa.configs.constants import NASAType, NASARangeType

# NOTE: logger setup
logger = logging.getLogger(__name__)


def _require_coeffs(
    coeffs: Dict[str, Any],
    required: Tuple[str, ...]
) -> Optional[Dict[str, Any]]:
    missing = [k for k in required if k not in coeffs]
    if missing:
        logger.error(
            f"Missing coefficients for En_IG: {missing}. Required: {list(required)}")
        return None
    return {k: coeffs[k] for k in required}


def _to_Kelvin(temp: Temperature) -> float:
    return pycuc.convert_from_to(
        value=temp.value,
        from_unit=temp.unit,
        to_unit="K"
    )


def _select_nasa_type(
    temperature: Temperature,
    break_temp_min: Temperature,
    break_temp_max: Temperature,
    nasa_type: Literal['nasa7', 'nasa9']
) -> NASARangeType:
    """
    Select the appropriate NASA polynomial type based on temperature.
    """
    try:
        # >> convert break temp to Kelvin
        T = _to_Kelvin(temperature)

        # >> convert break temp to Kelvin
        T_break_min = _to_Kelvin(break_temp_min)
        T_break_max = _to_Kelvin(break_temp_max)

        if T <= T_break_min:
            return "nasa7_200_1000_K" if nasa_type == "nasa7" else "nasa9_200_1000_K"
        elif T_break_min < T <= T_break_max:
            return "nasa7_1000_6000_K" if nasa_type == "nasa7" else "nasa9_1000_6000_K"
        elif T > T_break_max:
            return "nasa7_6000_20000_K" if nasa_type == "nasa7" else "nasa9_6000_20000_K"
        else:
            raise ValueError(
                f"Temperature {T} K is out of expected range."
            )
    except Exception as e:
        logger.exception(f"Error selecting NASA type: {e}")
        raise


# Allowed energy units
_ENERGY_UNITS = {"j", "kj", "cal", "kcal"}

# Strict grammar:
#   Energy:
#       J/mol
#       kJ/kmol
#   Entropy:
#       J/mol.K
#       kJ/kmol.K
#
# Explicitly DOES NOT accept J/mol/K
_UNIT_RE = re.compile(
    r"""^\s*
    (?P<eu>j|kj|cal|kcal)        # energy unit
    \s*/\s*
    (?P<amount>mol|kmol)        # amount basis
    (?:\.(?P<temp>k))?          # optional .K (entropy)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _energy_or_entropy_to_mass_basis(
    value: CustomProp,
    mw_g_per_mol: float,
) -> CustomProp:
    """
    Convert:
    - Energy:  J/mol, kJ/kmol
    - Entropy: J/mol.K, kJ/kmol.K

    to mass basis:
    - Energy:  J/kg
    - Entropy: J/kg.K

    Notes
    -----
    - The temperature dimension MUST be written with a dot: `.K`
    - Units like `J/mol/K` are intentionally rejected
    """
    try:
        if mw_g_per_mol <= 0:
            raise ValueError(f"mw must be > 0 (got {mw_g_per_mol})")

        unit_raw = value.unit.strip()
        unit_norm = unit_raw.lower().replace(" ", "")

        match = _UNIT_RE.match(unit_norm)
        if not match:
            raise ValueError(
                f"Unsupported or invalid unit format: '{value.unit}'. "
                "Use 'J/mol', 'kJ/kmol', 'J/mol.K', or 'kJ/kmol.K'"
            )

        energy_unit = match.group("eu")     # j, kj, cal, kcal
        amount = match.group("amount")      # mol or kmol
        has_K = match.group("temp") is not None

        # Preserve original energy-unit casing (kJ vs kj)
        energy_unit_out = unit_raw.split("/")[0].strip()

        if amount == "mol":
            mw_kg_per_mol = mw_g_per_mol / 1000.0
            mass_value = value.value / mw_kg_per_mol
        else:  # kmol
            # g/mol numerically equals kg/kmol
            mw_kg_per_kmol = mw_g_per_mol
            mass_value = value.value / mw_kg_per_kmol

        if has_K:
            mass_unit = f"{energy_unit_out}/kg.K"
        else:
            mass_unit = f"{energy_unit_out}/kg"

        return CustomProp(value=mass_value, unit=mass_unit)

    except Exception as e:
        logger.exception(f"Error converting to mass basis: {e}")
        raise
