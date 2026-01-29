# import libs
import logging
import yaml
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set, Union, Literal
from pythermodb_settings.utils import measure_time, set_component_id
# locals
from ..models import ComponentKey, Component
from .yaml_extractor import YAMLExtractor

# Prefer C-accelerated YAML loaders/dumpers when available
try:
    from yaml import CSafeDumper as BaseSafeDumper, CSafeLoader as BaseSafeLoader
except ImportError:  # pragma: no cover - fallback when libyaml not present
    from yaml import SafeDumper as BaseSafeDumper, SafeLoader as BaseSafeLoader

# NOTE: logger
logger = logging.getLogger(__name__)


class ComponentExtractor:
    """
    Extract component data from YAML reference text and rebuild a trimmed reference.
    """

    def __init__(self, extractor: Optional[YAMLExtractor] = None):
        self.extractor = extractor or YAMLExtractor()
        self._yaml_dumper = self._build_flow_seq_dumper()
        self._reference_data: Optional[Dict[str, Any]] = None

    @measure_time
    def filter_components_from_file(
        self,
        path: Union[str, Path],
        component_keys: Optional[List[str]] = None,
        *,
        components: Optional[List[Component]] = None,
        component_key: ComponentKey = "Name",
        separator_symbol: str = "-",
        case: Literal['lower', 'upper', None] = None,
        renumber: bool = True,
        save_reference: bool = False,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Read a YAML reference file, filter components, and rebuild a smaller YAML string.
        """
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8")

        # If save_reference is requested without an explicit path, auto-name alongside the source.
        derived_output = output_path
        if save_reference and not derived_output:
            derived_output = file_path.with_name(
                f"{file_path.stem}-filtered.yaml")

        result = self.filter_components(
            text,
            component_keys=component_keys,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case,
            renumber=renumber,
            save_reference=save_reference,
            output_path=derived_output
        )
        result["source_path"] = str(file_path)
        return result

    def load_ref(self, ref: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load and cache a reference from a path, YAML string, or already-parsed dict.
        """
        if isinstance(ref, dict):
            parsed = ref
        else:
            if isinstance(ref, Path):
                text = ref.read_text(encoding="utf-8")
            else:
                # assume string path or YAML content
                ref_path = Path(ref)
                if ref_path.exists():
                    text = ref_path.read_text(encoding="utf-8")
                else:
                    text = str(ref)
            parsed = yaml.load(text, Loader=BaseSafeLoader)

        if not isinstance(parsed, dict):
            raise ValueError("Loaded reference is not a mapping/dict.")

        self._reference_data = parsed
        return parsed

    def filter_components(
        self,
        reference_text: str,
        component_keys: Optional[List[str]] = None,
        *,
        components: Optional[List[Component]] = None,
        component_key: ComponentKey = "Name",
        separator_symbol: str = "-",
        case: Literal['lower', 'upper', None] = None,
        renumber: bool = True,
        save_reference: bool = False,
        output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Filter the reference by component identifiers and rebuild a smaller YAML string.

        Args:
            reference_text: Raw text that contains a YAML reference block.
            component_keys: Identifiers to look for (shape controlled by ``component_key``).
            components: List of Component objects; keys will be derived via ``set_component_id``.
            component_key: How to build the component key from a row (see ``ComponentKey``).
            separator_symbol: Separator to join key parts (default "-").
            case: Apply casing to generated identifiers ('lower', 'upper', or None).
            renumber: If True, re-number the ``No.`` column after filtering.
            save_reference: If True, write the rebuilt YAML to ``output_path``.
            output_path: Destination path to save the YAML when ``save_reference`` is True.

        Returns:
            Dict with the filtered data, rendered YAML string, and match bookkeeping.
        """
        key_inputs = self._collect_keys(
            component_keys=component_keys,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case
        )

        sections = self.extractor.extract_yaml_sections(reference_text)
        if not sections:
            raise ValueError(
                "No YAML sections were found in the provided text.")

        reference_dict = self._pick_reference_section(sections)
        if reference_dict is None:
            raise ValueError(
                "No YAML section with a 'REFERENCES' root was found.")

        filtered, found = self._filter_reference_dict(
            reference_dict,
            key_inputs,
            component_key,
            separator_symbol=separator_symbol,
            case_mode=case,
            renumber=renumber
        )

        yaml_str = yaml.dump(
            filtered,
            Dumper=self._yaml_dumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=10_000  # keep long flow-style sequences on a single line
        )

        requested = {
            self._normalize_key(cid, separator_symbol, case) for cid in key_inputs
        }
        missing = requested - found

        saved_to = None
        if save_reference:
            if not output_path:
                raise ValueError("save_reference=True requires output_path.")
            path = Path(output_path)
            path.write_text(yaml_str, encoding="utf-8")
            saved_to = str(path)

        return {
            "data": filtered,
            "yaml": yaml_str,
            "matched": sorted(found),
            "missing": sorted(missing),
            "saved_to": saved_to
        }

    @measure_time
    def check_component_availability(
        self,
        reference: Union[str, Path, Dict[str, Any]],
        *,
        component_keys: Optional[List[str]] = None,
        components: Optional[List[Component]] = None,
        component_key: ComponentKey = "Name",
        separator_symbol: str = "-",
        case: Literal['lower', 'upper', None] = None,
        renumber: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check whether requested components exist in a reference and return a summary.

        Args:
            reference: YAML text, path to a YAML file, or already-parsed reference dict.
            component_keys/components/component_key/etc: Same semantics as filter_components.
            renumber: Passed through to _filter_reference_dict when building matches (defaults to False to avoid rewriting IDs).

        Returns:
            Dict with matched, missing, normalized requested keys, and a human-readable summary string.
        """
        key_inputs = self._collect_keys(
            component_keys=component_keys,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case
        )

        # Load reference data from dict, YAML text, or file path.
        if isinstance(reference, dict):
            reference_dict = deepcopy(reference)
        else:
            if isinstance(reference, Path):
                text = reference.read_text(encoding="utf-8")
            else:
                ref_path = Path(reference)
                text = ref_path.read_text(
                    encoding="utf-8") if ref_path.exists() else str(reference)

            sections = self.extractor.extract_yaml_sections(text)
            if not sections:
                raise ValueError(
                    "No YAML sections were found in the provided text.")

            reference_dict = self._pick_reference_section(sections)
            if reference_dict is None:
                raise ValueError(
                    "No YAML section with a 'REFERENCES' root was found.")

        _, found = self._filter_reference_dict(
            reference_dict,
            key_inputs,
            component_key,
            separator_symbol=separator_symbol,
            case_mode=case,
            renumber=renumber
        )

        requested = {
            self._normalize_key(cid, separator_symbol, case) for cid in key_inputs
        }
        missing = requested - found

        summary_parts = [f"Found {len(found)}/{len(requested)} component(s)."]
        if missing:
            summary_parts.append(f"Missing: {', '.join(sorted(missing))}.")
        else:
            summary_parts.append("All requested components are present.")

        return {
            "matched": sorted(found),
            "missing": sorted(missing),
            "requested": sorted(requested),
            "summary": " ".join(summary_parts)
        }

    @measure_time
    def filter_components_from_data(
        self,
        reference_data: Optional[Union[Dict[str, Any], str]] = None,
        component_keys: Optional[List[str]] = None,
        *,
        components: Optional[List[Component]] = None,
        component_key: ComponentKey = "Name",
        separator_symbol: str = "-",
        case: Literal['lower', 'upper', None] = None,
        renumber: bool = True,
        save_reference: bool = False,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fast-path filtering when the reference is already loaded/parsed (API-friendly).

        Args:
            reference_data: Parsed reference dict (preferred) or YAML string. If None, use cached reference from load_ref().
            component_keys/components/component_key/etc: Same semantics as filter_components.
        """
        key_inputs = self._collect_keys(
            component_keys=component_keys,
            components=components,
            component_key=component_key,
            separator_symbol=separator_symbol,
            case=case
        )

        if reference_data is None:
            if self._reference_data is None:
                raise ValueError(
                    "No reference_data provided and no cached reference loaded. Call load_ref() first or pass reference_data.")
            parsed_reference = self._reference_data
        elif isinstance(reference_data, str):
            parsed_reference = yaml.load(reference_data, Loader=BaseSafeLoader)
        else:
            parsed_reference = reference_data

        if not isinstance(parsed_reference, dict):
            raise ValueError(
                "reference_data must be a dict or YAML string yielding a dict.")

        filtered, found = self._filter_reference_dict(
            parsed_reference,
            key_inputs,
            component_key,
            separator_symbol=separator_symbol,
            case_mode=case,
            renumber=renumber
        )

        yaml_str = yaml.dump(
            filtered,
            Dumper=self._yaml_dumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=10_000
        )

        requested = {
            self._normalize_key(cid, separator_symbol, case) for cid in key_inputs
        }
        missing = requested - found

        saved_to = None
        if save_reference:
            if not output_path:
                raise ValueError("save_reference=True requires output_path.")
            path = Path(output_path)
            path.write_text(yaml_str, encoding="utf-8")
            saved_to = str(path)

        return {
            "data": filtered,
            "yaml": yaml_str,
            "matched": sorted(found),
            "missing": sorted(missing),
            "saved_to": saved_to
        }

    def _pick_reference_section(self, sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the first parsed section that looks like a reference payload."""
        for section in sections:
            content = section.get("content")
            if isinstance(content, dict) and "REFERENCES" in content:
                return deepcopy(content)

        # Fallback: return first dict content if nothing matches the expected shape
        for section in sections:
            content = section.get("content")
            if isinstance(content, dict):
                return deepcopy(content)

        return None

    def _filter_reference_dict(
        self,
        reference: Dict[str, Any],
        component_keys: List[str],
        component_key: ComponentKey,
        *,
        separator_symbol: str,
        case_mode: Literal['lower', 'upper', None],
        renumber: bool = True
    ) -> Tuple[Dict[str, Any], Set[str]]:
        """Filter all table VALUE rows to only keep requested components."""
        normalized_targets = {
            self._normalize_key(cid, separator_symbol, case_mode) for cid in component_keys
        }
        filtered = deepcopy(reference)
        found: Set[str] = set()

        references = filtered.get("REFERENCES", {})
        for ref_name, ref_body in references.items():
            tables = ref_body.get("TABLES", {})
            for table_name, table in tables.items():
                values = table.get("VALUES")
                structure = table.get("STRUCTURE", {}) or {}
                columns = structure.get("COLUMNS") or []

                if not values or not isinstance(values, list):
                    continue

                filtered_rows: List[Any] = []
                for row in values:
                    match_key = self._build_component_key(
                        row,
                        columns,
                        component_key,
                        separator_symbol,
                        case_mode
                    )
                    if match_key and match_key in normalized_targets:
                        filtered_rows.append(row)
                        found.add(match_key)

                if renumber:
                    filtered_rows = self._renumber_rows(filtered_rows, columns)

                table["VALUES"] = filtered_rows
                logger.debug(
                    "Table %s/%s filtered to %d rows using key %s",
                    ref_name, table_name, len(filtered_rows), component_key
                )

        return filtered, found

    def _build_component_key(
        self,
        row: Any,
        columns: List[str],
        component_key: ComponentKey,
        separator_symbol: str,
        case_mode: Literal['lower', 'upper', None]
    ) -> Optional[str]:
        """Construct a comparable component key from a VALUES row."""
        column_lookup = {str(col).lower(): idx for idx,
                         col in enumerate(columns)}
        name = self._get_column_value(row, column_lookup.get("name"))
        formula = self._get_column_value(row, column_lookup.get("formula"))
        state = self._get_column_value(row, column_lookup.get("state"))

        builders = {
            "Name": lambda: name,
            "Formula": lambda: formula,
            "Name-State": lambda: self._join_parts([name, state], separator_symbol),
            "Formula-State": lambda: self._join_parts([formula, state], separator_symbol),
            "Name-Formula": lambda: self._join_parts([name, formula], separator_symbol),
            "Name-Formula-State": lambda: self._join_parts([name, formula, state], separator_symbol),
            "Formula-Name-State": lambda: self._join_parts([formula, name, state], separator_symbol),
        }

        builder = builders.get(component_key)
        if not builder:
            return None

        result = builder()
        return self._normalize_key(result, separator_symbol, case_mode) if result else None

    def _get_column_value(self, row: Any, idx: Optional[int]) -> Optional[str]:
        """Safely read a cell value from a VALUES row."""
        if idx is None:
            return None

        try:
            return str(row[idx])
        except (TypeError, IndexError):
            return None

    def _join_parts(self, parts: List[Optional[str]], sep: str) -> Optional[str]:
        """Join non-empty components with the provided separator."""
        cleaned = [p.strip() for p in parts if p]
        return sep.join(cleaned) if cleaned else None

    def _renumber_rows(self, rows: List[Any], columns: List[str]) -> List[Any]:
        """Rewrite the No. column so filtered tables stay sequential."""
        if not rows:
            return []

        column_lookup = {str(col).lower(): idx for idx,
                         col in enumerate(columns)}
        number_idx = column_lookup.get("no.") or column_lookup.get("no")
        if number_idx is None:
            return rows

        renumbered = []
        for i, row in enumerate(rows, start=1):
            try:
                row_copy = list(row)
                row_copy[number_idx] = i
            except Exception:
                # If the row is not sequence-like, leave it untouched
                row_copy = row
            renumbered.append(row_copy)

        return renumbered

    def _normalize_key(
        self,
        value: Optional[str],
        sep: str,
        case_mode: Literal['lower', 'upper', None] = None
    ) -> str:
        """Normalize identifiers for comparison (case-insensitive by default)."""
        if value is None:
            return ""
        normalized = str(value).strip().replace("|", sep)
        parts = [p.strip() for p in normalized.split(sep)]
        normalized = sep.join(parts)
        normalized = " ".join(normalized.split())

        target_case = case_mode if case_mode is not None else 'lower'
        if target_case == 'lower':
            normalized = normalized.lower()
        elif target_case == 'upper':
            normalized = normalized.upper()

        return normalized

    def _collect_keys(
        self,
        *,
        component_keys: Optional[List[str]],
        components: Optional[List[Component]],
        component_key: ComponentKey,
        separator_symbol: str,
        case: Literal['lower', 'upper', None]
    ) -> List[str]:
        """Gather all key inputs from provided components and raw keys."""
        key_inputs: List[str] = []

        if components:
            key_inputs.extend([
                set_component_id(
                    component=comp,
                    component_key=component_key,
                    separator_symbol=separator_symbol,
                    case=case
                )
                for comp in components
            ])

        if component_keys:
            key_inputs.extend(component_keys)

        if not key_inputs:
            raise ValueError("No component keys provided.")

        return key_inputs

    def _build_flow_seq_dumper(self):
        """
        Build a YAML dumper that keeps scalar-only sequences in flow style
        (e.g., rows stay as ``[1, "...", ...]`` instead of multi-line).
        """

        base = BaseSafeDumper
        try:
            FlowSeqDumper = type("FlowSeqDumper", (base,), {})
        except TypeError:
            # Some environments disallow subclassing the C dumper; fall back to Python dumper.
            FlowSeqDumper = type("FlowSeqDumper", (yaml.SafeDumper,), {})

        def _represent_list(dumper, data):
            is_scalar_seq = all(
                not isinstance(item, (list, dict)) for item in data
            )
            return dumper.represent_sequence(
                "tag:yaml.org,2002:seq",
                data,
                flow_style=is_scalar_seq
            )

        FlowSeqDumper.add_representer(list, _represent_list)
        return FlowSeqDumper
