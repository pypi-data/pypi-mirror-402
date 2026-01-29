# import libs
from typing import Literal

# SECTION: PyThermoDBLink/PyThermoDB
DATASOURCE = "datasource"
EQUATIONSOURCE = "equationsource"


# SECTION: constants
R_J_molK = 8.314462618  # universal gas constant in J/mol.K
T_ref_K = 298.15  # reference temperature in K
P_ref_Pa = 101325.0  # reference pressure in Pa

# SECTION: NASA polynomial types
NASAType = Literal["nasa7", "nasa9"]

# NASA polynomial temperature ranges
NASA7_200_1000_K = "nasa7_200_1000_K"
NASA7_1000_6000_K = "nasa7_1000_6000_K"
NASA7_6000_20000_K = "nasa7_6000_20000_K"
NASA9_200_1000_K = "nasa9_200_1000_K"
NASA9_1000_6000_K = "nasa9_1000_6000_K"
NASA9_6000_20000_K = "nasa9_6000_20000_K"

NASARangeType = Literal[
    "nasa7_200_1000_K",
    "nasa7_1000_6000_K",
    "nasa7_6000_20000_K",
    "nasa9_200_1000_K",
    "nasa9_1000_6000_K",
    "nasa9_6000_20000_K",
]

NASA_POLY_TYPES = (
    NASA7_200_1000_K,
    NASA7_1000_6000_K,
    NASA7_6000_20000_K,
    NASA9_200_1000_K,
    NASA9_1000_6000_K,
    NASA9_6000_20000_K,
)

# SECTION: Temperature breaks
# NASA7
# temperature break for NASA7 polynomials in K
TEMPERATURE_BREAK_NASA7_200_K = 200.0
# temperature break for NASA7 polynomials in K
TEMPERATURE_BREAK_NASA7_1000_K = 1000.0
# temperature break for NASA7 polynomials in K
TEMPERATURE_BREAK_NASA7_6000_K = 6000.0
# NASA9
# temperature break for NASA9 polynomials in K
TEMPERATURE_BREAK_NASA9_200_K = 200.0
TEMPERATURE_BREAK_NASA9_1000_K = 1000.0  # temperature
# temperature break for NASA9 polynomials in K
TEMPERATURE_BREAK_NASA9_6000_K = 6000.0

# SECTION: Basis types
BasisType = Literal["molar", "mass"]
