# import libs
import logging
from typing import List, Optional, Union, Dict, Literal, cast
from pythermodb_settings.models import Temperature, CustomProp
from pyreactlab_core.models.reaction import Reaction
from pyThermoCalcDB.reactions.source import (
    dH_rxn_STD,
    dS_rxn_STD,
    dG_rxn_STD,
    Keq,
    Keq_vh_shortcut
)
# locals


# NOTE: setup logger
logger = logging.getLogger(__name__)


class RXNAdapter:
    """
    Adapter class for reaction calculations.

    Methods
    -------
    dH_rxn_std
        Calculate standard enthalpy change of the reaction.
    dS_rxn_std
        Calculate standard entropy change of the reaction.
    dG_rxn_std
        Calculate standard Gibbs free energy change of the reaction.
    Keq
        Calculate the equilibrium constant of the reaction.
    Keq_vh_shortcut
        Calculate the equilibrium constant of the reaction using van't Hoff shortcut.
    """

    def __init__(self, reaction: Reaction):
        """
        Initialize RXNAdapter with a Reaction object.

        Parameters
        ----------
        reaction : Reaction
            The reaction for which to perform calculations.
        """
        self.reaction = reaction

    def dH_rxn_std(
        self,
        *,
        H_i_IG: Dict[str, CustomProp],
        **kwargs
    ) -> Optional[CustomProp]:
        """
        Calculate standard enthalpy change of the reaction.

        Parameters
        ----------
        H_i_IG : Dict[str, CustomProp]
            Dictionary of ideal gas enthalpy properties for each component.

        Returns
        -------
        Optional[CustomProp]
            Standard enthalpy change of the reaction.
        """
        return dH_rxn_STD(
            reaction=self.reaction,
            H_i_IG=H_i_IG,
            **kwargs
        )

    def dS_rxn_std(
        self,
        *,
        S_i_IG: Dict[str, CustomProp],
        **kwargs
    ) -> Optional[CustomProp]:
        """
        Calculate standard entropy change of the reaction.

        Parameters
        ----------
        S_i_IG : Dict[str, CustomProp]
            Dictionary of ideal gas entropy properties for each component.

        Returns
        -------
        Optional[CustomProp]
            Standard entropy change of the reaction.
        """
        return dS_rxn_STD(
            reaction=self.reaction,
            S_i_IG=S_i_IG,
            **kwargs
        )

    def dG_rxn_std(
        self,
        *,
        G_i_IG: Dict[str, CustomProp],
        **kwargs
    ) -> Optional[CustomProp]:
        """
        Calculate standard Gibbs free energy change of the reaction.

        Parameters
        ----------
        dH_rxn_STD : Dict[str, CustomProp]
            Dictionary of ideal gas Gibbs free energy properties for each component.

        Returns
        -------
        Optional[CustomProp]
            Standard Gibbs free energy change of the reaction.
        """
        return dG_rxn_STD(
            reaction=self.reaction,
            G_i_IG=G_i_IG,
            **kwargs
        )

    def Keq(
        self,
        *,
        dG_rxn_STD: CustomProp,
        temperature: Temperature,
        **kwargs
    ) -> Optional[CustomProp]:
        """
        Calculate the equilibrium constant of the reaction.

        Parameters
        ----------
        dG_rxn_STD : CustomProp
            Standard Gibbs free energy change of the reaction.
        temperature : Temperature
            Temperature at which to calculate the equilibrium constant.

        Returns
        -------
        Optional[CustomProp]
            Equilibrium constant of the reaction.
        """
        return Keq(
            reaction=self.reaction,
            dG_rxn_STD=dG_rxn_STD,
            temperature=temperature,
            **kwargs
        )

    def Keq_vh_shortcut(
        self,
        *,
        Keq_STD: CustomProp,
        dH_rxn_STD: CustomProp,
        temperature: Temperature,
        **kwargs
    ) -> Optional[CustomProp]:
        """
        Calculate the equilibrium constant of the reaction using van't Hoff shortcut.

        Parameters
        ----------
        Keq_STD : CustomProp
            Standard equilibrium constant of the reaction.
        dH_rxn_STD : CustomProp
            Standard enthalpy change of the reaction.
        temperature : Temperature
            Temperature at which to calculate the equilibrium constant.

        Returns
        -------
        Optional[CustomProp]
            Equilibrium constant of the reaction.
        """
        return Keq_vh_shortcut(
            reaction=self.reaction,
            Keq_STD=Keq_STD,
            dH_rxn_STD=dH_rxn_STD,
            temperature=temperature,
            **kwargs
        )
