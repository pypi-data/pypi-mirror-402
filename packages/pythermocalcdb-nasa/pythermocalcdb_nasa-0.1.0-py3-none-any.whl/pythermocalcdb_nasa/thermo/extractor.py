# import libs
import logging
from typing import Optional, Dict, List, Any
from pyThermoLinkDB.thermo import Source
from pyThermoLinkDB.models.component_models import ComponentEquationSource
from pythermodb_settings.models import Component, ComponentKey
from pythermodb_settings.utils import set_component_id
# locals

# NOTE: set up logger
logger = logging.getLogger(__name__)


class DataExtractor:

    def __init__(
            self,
            source: Source,
    ):
        # NOTE: set source
        self.source = source

    def _get_formation_data(
        self,
        component: Component,
        component_key: ComponentKey,
        prop_name: str,
    ) -> Optional[Dict[str, Any]]:
        '''
        Retrieve formation data for the specified property.

        Parameters
        ----------
        component_id : str
            The unique identifier of the component.
        component_key : ComponentKey
            The key type used to identify the component.
        prop_name : str
            The name of the property for which formation data is to be retrieved.

        Returns
        -------
        Optional[Dict[str, Any]]
            A dictionary containing the formation data if available, otherwise None.
        '''
        try:
            # NOTE: set component id
            component_id = set_component_id(
                component=component,
                component_key=component_key
            )

            # NOTE: retrieve formation data
            return self.source.data_extractor(
                component_id=component_id,
                prop_name=prop_name,
            )
        except Exception as e:
            logger.exception(
                f"Error retrieving formation data for {prop_name}: {e}")
            return None

    def _get_equation_source(
            self,
            component: Component,
            component_key: ComponentKey,
            prop_name: str,
    ) -> Optional[ComponentEquationSource]:
        '''
        Retrieve the equation source for the specified property.

        Parameters
        ----------
        component : Component
            The component for which the equation source is to be retrieved.
        component_key : ComponentKey
            The key type used to identify the component.
        prop_name : str
            The name of the property for which the equation source is to be retrieved.

        Returns
        -------
        Optional[ComponentEquationSource]
            The equation source if available, otherwise None.
        '''
        try:
            # NOTE: set component id
            component_id = set_component_id(
                component=component,
                component_key=component_key
            )

            # NOTE: build equation
            eq_src = self.source.eq_builder(
                components=[component],
                prop_name=prop_name,
                component_key=component_key  # type: ignore
            )

            # >> check equation
            if eq_src is None:
                logger.warning(
                    f"No equation available for property {prop_name} for component {component_id}.")
                return None

            # >> for component
            component_eq_src: ComponentEquationSource | None = eq_src.get(
                component_id
            )

            if component_eq_src is None:
                logger.warning(
                    f"No equation available for property {prop_name} for component {component_id}.")
                return None

            return component_eq_src
        except Exception as e:
            logger.exception(
                f"Error retrieving equation source for {prop_name}: {e}")
            raise
