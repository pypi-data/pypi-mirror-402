"""
High level wrapper for LifeCycleModel datasets.
"""
from __future__ import annotations

from typing import Any, Mapping, cast
from uuid import uuid4

from ..core.base import TidasEntity
from ..core.markdown import ensure_list, format_number, join_texts, pick_short_description
from ..generated.tidas_lifecyclemodels import (
    LifeCycleModelDataSetAdministrativeInformationDataEntryBy,
    LifeCycleModelDataSetAdministrativeInformationPublicationAndOwnership,
    LifeCycleModelDataSetLifeCycleModelInformationQuantitativeReference,
    LifeCycleModelDataSetLifeCycleModelInformationDataSetInformation,
    LifeCycleModelDataSetLifeCycleModelInformationTechnology,
    Lifecyclemodels,
    LifecyclemodelsLifeCycleModelDataSet,
    LifecyclemodelsLifeCycleModelDataSetAdministrativeInformation,
    LifecyclemodelsLifeCycleModelDataSetLifeCycleModelInformation,
)
from .utils import default_timestamp, ensure_model, ensure_multilang


class TidasLifeCycleModel(TidasEntity[Lifecyclemodels]):
    schema_name = "tidas_lifecyclemodels.json"

    def __init__(
        self,
        initial_data: dict[str, Any] | Lifecyclemodels | None = None,
        *,
        validate_on_init: bool = False,
    ) -> None:
        super().__init__(Lifecyclemodels, initial_data, validate_on_init=validate_on_init)

    @property
    def life_cycle_model_data_set(self) -> LifecyclemodelsLifeCycleModelDataSet:
        return cast(LifecyclemodelsLifeCycleModelDataSet, getattr(self.model, "life_cycle_model_data_set"))

    @life_cycle_model_data_set.setter
    def life_cycle_model_data_set(
        self,
        value: LifecyclemodelsLifeCycleModelDataSet | Mapping[str, Any],
    ) -> None:
        TidasEntity.__setattr__(self, "life_cycle_model_data_set", value)

    def ensure_defaults(self) -> None:
        dataset = ensure_model(self, "life_cycle_model_data_set", LifecyclemodelsLifeCycleModelDataSet)
        dataset.xmlns = dataset.xmlns or "http://eplca.jrc.ec.europa.eu/ILCD/LifeCycleModel/2017"
        dataset.xmlns_acme = dataset.xmlns_acme or "http://acme.com/custom"
        dataset.xmlns_common = dataset.xmlns_common or "http://lca.jrc.it/ILCD/Common"
        dataset.xmlns_xsi = dataset.xmlns_xsi or "http://www.w3.org/2001/XMLSchema-instance"
        dataset.version = dataset.version or "1.1"
        dataset.locations = dataset.locations or "../ILCDLocations.xml"
        dataset.xsi_schema_location = (
            dataset.xsi_schema_location
            or "http://eplca.jrc.ec.europa.eu/ILCD/LifeCycleModel/2017 ../../schemas/ILCD_LifeCycleModelDataSet.xsd"
        )

        info = ensure_model(
            dataset,
            "life_cycle_model_information",
            LifecyclemodelsLifeCycleModelDataSetLifeCycleModelInformation,
        )
        data_info = ensure_model(
            info,
            "data_set_information",
            LifeCycleModelDataSetLifeCycleModelInformationDataSetInformation,
        )
        if not data_info.common_uuid:
            data_info.common_uuid = str(uuid4())
        ensure_multilang(data_info, "common_name")
        ensure_multilang(data_info, "common_synonyms")
        ensure_multilang(data_info, "common_general_comment")

        admin = ensure_model(
            dataset,
            "administrative_information",
            LifecyclemodelsLifeCycleModelDataSetAdministrativeInformation,
        )
        data_entry = ensure_model(
            admin,
            "data_entry_by",
            LifeCycleModelDataSetAdministrativeInformationDataEntryBy,
        )
        if not data_entry.common_time_stamp:
            data_entry.common_time_stamp = default_timestamp()
        ensure_model(
            admin,
            "publication_and_ownership",
            LifeCycleModelDataSetAdministrativeInformationPublicationAndOwnership,
        )

    def to_markdown(self, lang: str = "en") -> str:
        dataset = getattr(self, "life_cycle_model_data_set", None)
        info = getattr(dataset, "life_cycle_model_information", None) if dataset else None
        data_info = getattr(info, "data_set_information", None) if info else None
        quant_ref = getattr(info, "quantitative_reference", None) if info else None
        technology = getattr(info, "technology", None) if info else None
        modelling = getattr(dataset, "modelling_and_validation", None) if dataset else None

        title = self._compose_title(data_info, lang)

        lines: list[str] = [f"# {title}", ""]
        lines.append("**Entity:** Life Cycle Model")

        if data_info and data_info.common_uuid:
            lines.append(f"**UUID:** `{data_info.common_uuid}`")

        version = self._data_set_version(dataset)
        if version:
            lines.append(f"**Version:** {version}")

        ref_name, ref_id = self._reference_process_summary(quant_ref, technology, lang)
        if ref_name or ref_id:
            suffix = f" (ID {ref_id})" if ref_id else ""
            lines.append(f"**Reference Process:** {ref_name or 'Reference process'}{suffix}")

        resulting_process = pick_short_description(getattr(data_info, "reference_to_resulting_process", None), lang)
        if resulting_process:
            lines.append(f"**Resulting Process:** {resulting_process}")

        external_doc = pick_short_description(getattr(data_info, "reference_to_external_documentation", None), lang)
        if external_doc:
            lines.append(f"**External Documentation:** {external_doc}")

        classification = self._classification_path(data_info)
        if classification:
            lines.append(f"**Classification:** {classification}")

        synonyms = join_texts(getattr(data_info, "common_synonyms", None), lang)
        if synonyms:
            lines.append(f"**Synonyms:** {synonyms}")

        if lines and lines[-1] != "":
            lines.append("")

        description = join_texts(getattr(data_info, "common_general_comment", None), lang)
        if description:
            lines.extend(["## Description", "", description, ""])

        use_advice = self._use_advice(modelling, lang)
        if use_advice:
            lines.extend(["## Use Advice", "", use_advice, ""])

        process_lines = self._process_lines(technology, lang)
        if process_lines:
            lines.append("## Process Instances")
            lines.append("")
            lines.extend(process_lines)
            lines.append("")

        diagram = pick_short_description(getattr(technology, "reference_to_diagram", None), lang) if technology else None
        if diagram:
            lines.extend(["## Technology", "", f"Diagram: {diagram}", ""])

        if lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)

    def _compose_title(
        self,
        data_info: LifeCycleModelDataSetLifeCycleModelInformationDataSetInformation | None,
        lang: str,
    ) -> str:
        if not data_info:
            return "Life Cycle Model"
        name_obj = getattr(data_info, "name", None)
        parts: list[str] = []
        for field in (
            "base_name",
            "mix_and_location_types",
            "treatment_standards_routes",
            "functional_unit_flow_properties",
        ):
            part = join_texts(getattr(name_obj, field, None), lang, sep=" | ") if name_obj else None
            if part:
                parts.append(part)
        return " | ".join(parts) if parts else "Life Cycle Model"

    def _classification_path(
        self, data_info: LifeCycleModelDataSetLifeCycleModelInformationDataSetInformation | None
    ) -> str | None:
        if not data_info:
            return None
        classification_info = getattr(data_info, "classification_information", None)
        common_classification = getattr(classification_info, "common_classification", None) if classification_info else None
        classes = ensure_list(getattr(common_classification, "common_class", None)) if common_classification else []
        if not classes:
            return None

        def _level_value(item: Any) -> int | None:
            level = getattr(item, "level", None)
            try:
                return int(level)
            except Exception:
                return None

        sorted_classes = sorted(
            classes,
            key=lambda entry: (_level_value(entry) is None, _level_value(entry) or 0),
        )
        parts: list[str] = []
        for entry in sorted_classes:
            text = getattr(entry, "text", None)
            if text:
                parts.append(str(text))
                continue
            if isinstance(entry, dict) and entry.get("#text"):
                parts.append(str(entry["#text"]))
        return " > ".join(parts) if parts else None

    def _data_set_version(self, dataset: LifecyclemodelsLifeCycleModelDataSet | None) -> str | None:
        if not dataset:
            return None
        admin = getattr(dataset, "administrative_information", None)
        publication = getattr(admin, "publication_and_ownership", None) if admin else None
        return getattr(publication, "common_data_set_version", None)

    def _process_instances(
        self, technology: LifeCycleModelDataSetLifeCycleModelInformationTechnology | None
    ) -> list[Any]:
        processes = getattr(technology, "processes", None) if technology else None
        instances = getattr(processes, "process_instance", None) if processes else None
        return ensure_list(instances)

    def _reference_process_summary(
        self,
        quant_ref: LifeCycleModelDataSetLifeCycleModelInformationQuantitativeReference | None,
        technology: LifeCycleModelDataSetLifeCycleModelInformationTechnology | None,
        lang: str,
    ) -> tuple[str | None, str | None]:
        ref_id = getattr(quant_ref, "reference_to_reference_process", None) if quant_ref else None
        if not ref_id:
            return None, None

        instances = self._process_instances(technology)
        for item in instances:
            inst_id = getattr(item, "data_set_internal_id", None)
            if inst_id is None and isinstance(item, dict):
                inst_id = item.get("@dataSetInternalID")
            if inst_id is not None and str(inst_id) == str(ref_id):
                ref = item.get("referenceToProcess") if isinstance(item, dict) else getattr(item, "reference_to_process", None)
                name = pick_short_description(ref, lang)
                return name, str(ref_id)
        return None, str(ref_id)

    def _process_lines(
        self, technology: LifeCycleModelDataSetLifeCycleModelInformationTechnology | None, lang: str
    ) -> list[str]:
        instances = self._process_instances(technology)
        if not instances:
            return []

        def _as_int(value: Any) -> int | None:
            try:
                return int(str(value))
            except Exception:
                return None

        def _inst_id(item: Any) -> Any:
            inst_id = getattr(item, "data_set_internal_id", None)
            if inst_id is None and isinstance(item, dict):
                inst_id = item.get("@dataSetInternalID")
            return inst_id

        sorted_instances = sorted(
            enumerate(instances),
            key=lambda pair: (_as_int(_inst_id(pair[1])) is None, _as_int(_inst_id(pair[1])) or 0, pair[0]),
        )

        lines: list[str] = []
        for _, item in sorted_instances:
            inst_id = _inst_id(item)
            mult = getattr(item, "multiplication_factor", None)
            ref = getattr(item, "reference_to_process", None)
            if isinstance(item, dict):
                mult = item.get("@multiplicationFactor", mult)
                ref = item.get("referenceToProcess", ref)
            name = pick_short_description(ref, lang) or "Process"
            mult_text = format_number(mult) if mult is not None else None
            suffix = f" ×{mult_text}" if mult_text else ""
            label = f"ID {inst_id}" if inst_id is not None else "Process"
            lines.append(f"- {label}: {name}{suffix}")
        return lines

    def _use_advice(self, modelling: Any, lang: str) -> str | None:
        data_sources = getattr(modelling, "data_sources_treatment_etc", None) if modelling else None
        return join_texts(getattr(data_sources, "use_advice_for_data_set", None), lang)
