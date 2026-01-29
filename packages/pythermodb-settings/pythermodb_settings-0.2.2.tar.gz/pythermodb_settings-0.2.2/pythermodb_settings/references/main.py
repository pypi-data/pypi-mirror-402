# import libs
import logging
from typing import List, Dict, Optional, Any, Literal, Union
from pathlib import Path
# locals
from ..models import Component, ComponentKey
from .component_extractor import ComponentExtractor
from ..utils import measure_time

# NOTE: logger setup
logger = logging.getLogger(__name__)


@measure_time
def extract_reference_components(
    reference_file: Path,
    components: List[Component],
    component_key: ComponentKey,
    separator_symbol: str = "-",
    case: Optional[Literal['lower', 'upper', None]] = None,
    renumber: bool = True,
    save_reference: bool = False,
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Extract a reference component list from a given reference file.

    Parameters
    ----------
    reference_file : Path
        Path to the reference file containing component data.
    components : List[Component]
        List of Component instances to filter from the reference file.
    component_key : ComponentKey
        Key type to identify components.
    separator_symbol : str, optional
        Symbol used to separate fields in the component key. Default is "-".
    case : Literal['lower', 'upper', None], optional
        Case transformation for component keys. Default is None.
    renumber : bool, optional
        Whether to renumber component IDs. Default is True.
    save_reference : bool, optional
        Whether to save the filtered reference to a file. Default is False.
    output_path : Optional[Union[str, Path]], optional
        Path to save the filtered reference file if save_reference is True. Default is None.
    **kwargs
        Additional keyword arguments.
        - mode : Literal['silent', 'log', 'attach'], optional
            Mode for time measurement logging. Default is 'log'.

    Returns:
        Dict[str, any]: Dictionary containing matched components, missing components, and saved path if applicable.
    """
    try:
        # NOTE: extractor instance
        ce = ComponentExtractor()

        # filter components from file
        result = ce.filter_components_from_file(
            reference_file,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case,
            renumber=renumber,
            save_reference=save_reference,
            output_path=output_path,
        )
        return result
    except Exception as e:
        logger.error(f"Error in building reference components: {e}")
        raise


@measure_time
def check_reference_component_availability(
    reference: str | Path | Dict[str, Any],
    *,
    component_keys: Optional[List[str]] = None,
    components: Optional[List[Component]] = None,
    component_key: ComponentKey = "Name",
    separator_symbol: str = "-",
    case: Literal['lower', 'upper'] | None = None,
    renumber: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Check whether requested components exist in a reference and return a summary.

    Parameters
    ----------
    reference : Union[str, Path, Dict[str, Any]]
        Reference file path or reference data dictionary.
    component_keys : List[str], optional
        List of component keys to check in the reference such as 'H2O', 'CO2'.
    components : List[Component]
        List of Component to check in the reference such as name, formula.
    component_key : ComponentKey, optional
        Key type to identify components. Default is "Name".
    separator_symbol : str, optional
        Symbol used to separate fields in the component key. Default is "-".
    case : Literal['lower', 'upper', None], optional
        Case transformation for component keys. Default is None.
    renumber : bool, optional
        Whether to renumber component IDs. Default is False.
    **kwargs
        Additional keyword arguments.

    Returns:
        Dict[str, any]: Dictionary containing matched components and missing components.
    """
    try:
        # NOTE: extractor instance
        ce = ComponentExtractor()

        # check component availability
        result = ce.check_component_availability(
            reference,
            component_keys=component_keys,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case,
            renumber=renumber,
        )
        return result
    except Exception as e:
        logger.error(f"Error in checking component availability: {e}")
        raise
