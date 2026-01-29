"""Coordinate stateful access to discovery and harmonization APIs.

'why': provide a single, inspectable entry point that captures configuration once
and exposes typed discovery and harmonization helpers (sync/async) for consumers
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from ._core import harmonize as _harmonize
from ._core import harmonize_async as _harmonize_async
from ._data_model_store import (
    get_pv_set as _get_pv_set,
    get_pv_set_async as _get_pv_set_async,
    list_cdes as _list_cdes,
    list_cdes_async as _list_cdes_async,
    list_data_models as _list_data_models,
    list_data_models_async as _list_data_models_async,
    list_pvs as _list_pvs,
    list_pvs_async as _list_pvs_async,
)
from ._discovery import (
    discover_cde_mapping as _discover_cde_mapping,
    discover_mapping as _discover_mapping,
    discover_mapping_async as _discover_mapping_async,
    discover_mapping_from_csv_async as _discover_mapping_from_csv_async,
)
from ._config import build_settings
from ._errors import ClientConfigurationError
from ._logging import configure_logger
from ._models import CDE, DataModel, HarmonizationResult, LogLevel, PermissibleValue, Settings


ManifestPayload = dict[str, dict[str, dict[str, object]]]


class NetriasClient:
    """Expose discovery and harmonization workflows behind instance state.

    A `NetriasClient` manages configuration snapshots (API key, URLs, thresholds,
    bypass preferences) and threads them through every outbound call. Consumers
    typically instantiate a client, call :meth:`configure`, and then interact via
    the discovery/harmonization methods below.
    """

    def __init__(self) -> None:
        """Initialise an empty client awaiting configuration."""

        self._lock: threading.Lock = threading.Lock()
        self._settings: Settings | None = None
        self._logger_name: str = f"netrias_client.{uuid4().hex}"
        self._logger: logging.Logger | None = None

    def configure(
        self,
        api_key: str,
        timeout: float | None = None,
        log_level: LogLevel | str | None = None,
        confidence_threshold: float | None = None,
        discovery_use_gateway_bypass: bool | None = None,
        log_directory: Path | str | None = None,
    ) -> None:
        """Validate inputs and persist a new immutable settings snapshot.

        Parameters
        ----------
        api_key:
            Netrias API bearer token used for authentication.
        timeout:
            Overall request timeout in seconds (defaults to six hours).
        log_level:
            Desired logging verbosity as a :class:`~netrias_client._models.LogLevel`
            (string aliases are also accepted for convenience).
        confidence_threshold:
            Minimum confidence score required for discovery recommendations.
        discovery_use_gateway_bypass:
            When ``True`` (default) calls the temporary Lambda bypass instead of
            API Gateway.
        log_directory:
            Optional directory where this client's log files should be written.
            When omitted, logging remains stream-only.

        Calling this method multiple times replaces the active snapshot and
        reconfigures the package logger.
        """

        settings = build_settings(
            api_key=api_key,
            timeout=timeout,
            log_level=log_level,
            confidence_threshold=confidence_threshold,
            discovery_use_gateway_bypass=discovery_use_gateway_bypass,
            log_directory=log_directory,
        )
        logger = configure_logger(
            self._logger_name,
            settings.log_level,
            settings.log_directory,
        )
        with self._lock:
            self._settings = settings
            self._logger = logger

    @property
    def settings(self) -> Settings:
        """Return a defensive copy of the current settings.

        'why': aid observability without exposing internal state for mutation
        """

        return self._snapshot_settings()

    def discover_mapping(
        self,
        target_schema: str,
        target_version: str,
        column_samples: Mapping[str, Sequence[object]],
        top_k: int | None = None,
    ) -> ManifestPayload:
        """Perform synchronous mapping discovery for the provided schema."""

        settings = self._snapshot_settings()

        return _discover_mapping(
            settings=settings,
            target_schema=target_schema,
            target_version=target_version,
            column_samples=column_samples,
            logger=self._require_logger(),
            top_k=top_k,
        )

    async def discover_mapping_async(
        self,
        target_schema: str,
        target_version: str,
        column_samples: Mapping[str, Sequence[object]],
        top_k: int | None = None,
    ) -> ManifestPayload:
        """Async variant of :meth:`discover_mapping` with identical semantics."""

        settings = self._snapshot_settings()

        return await _discover_mapping_async(
            settings=settings,
            target_schema=target_schema,
            target_version=target_version,
            column_samples=column_samples,
            logger=self._require_logger(),
            top_k=top_k,
        )

    def discover_mapping_from_csv(
        self,
        source_csv: Path,
        target_schema: str,
        target_version: str,
        sample_limit: int = 25,
        top_k: int | None = None,
    ) -> ManifestPayload:
        """Derive column samples from a CSV file then perform mapping discovery."""

        settings = self._snapshot_settings()

        return _discover_cde_mapping(
            settings=settings,
            source_csv=source_csv,
            target_schema=target_schema,
            target_version=target_version,
            sample_limit=sample_limit,
            logger=self._require_logger(),
            top_k=top_k,
        )

    def discover_cde_mapping(
        self,
        source_csv: Path,
        target_schema: str,
        target_version: str,
        sample_limit: int = 25,
        top_k: int | None = None,
    ) -> ManifestPayload:
        """Compatibility alias for :meth:`discover_mapping_from_csv`."""

        return self.discover_mapping_from_csv(
            source_csv=source_csv,
            target_schema=target_schema,
            target_version=target_version,
            sample_limit=sample_limit,
            top_k=top_k,
        )

    async def discover_mapping_from_csv_async(
        self,
        source_csv: Path,
        target_schema: str,
        target_version: str,
        sample_limit: int = 25,
        top_k: int | None = None,
    ) -> ManifestPayload:
        """Async variant of :meth:`discover_mapping_from_csv`."""

        settings = self._snapshot_settings()

        return await _discover_mapping_from_csv_async(
            settings=settings,
            source_csv=source_csv,
            target_schema=target_schema,
            target_version=target_version,
            sample_limit=sample_limit,
            logger=self._require_logger(),
            top_k=top_k,
        )

    def harmonize(
        self,
        source_path: Path,
        manifest: Path | Mapping[str, object],
        output_path: Path | None = None,
        manifest_output_path: Path | None = None,
    ) -> HarmonizationResult:
        """Execute the harmonization workflow synchronously and block.

        The method accepts either a manifest mapping or a JSON file path and
        writes the harmonized CSV to the resolved output location (which may be
        auto-versioned). A :class:`HarmonizationResult` is always returned even on
        failure, allowing callers to inspect status and description.
        """

        settings = self._snapshot_settings()

        return _harmonize(
            settings=settings,
            source_path=source_path,
            manifest=manifest,
            output_path=output_path,
            manifest_output_path=manifest_output_path,
            logger=self._require_logger(),
        )

    async def harmonize_async(
        self,
        source_path: Path,
        manifest: Path | Mapping[str, object],
        output_path: Path | None = None,
        manifest_output_path: Path | None = None,
    ) -> HarmonizationResult:
        """Async counterpart to :meth:`harmonize` with identical semantics."""

        settings = self._snapshot_settings()

        return await _harmonize_async(
            settings=settings,
            source_path=source_path,
            manifest=manifest,
            output_path=output_path,
            manifest_output_path=manifest_output_path,
            logger=self._require_logger(),
        )

    # ---- Data Model Store methods ----

    def list_data_models(
        self,
        query: str | None = None,
        include_versions: bool = False,
        include_counts: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[DataModel, ...]:
        """Fetch data models from the Data Model Store.

        Parameters
        ----------
        query:
            Substring search on model key or name.
        include_versions:
            Include version metadata per model.
        include_counts:
            Include CDE/PV counts per version.
        limit:
            Maximum number of results to return.
        offset:
            Number of results to skip.
        """

        settings = self._snapshot_settings()

        return _list_data_models(
            settings=settings,
            query=query,
            include_versions=include_versions,
            include_counts=include_counts,
            limit=limit,
            offset=offset,
        )

    async def list_data_models_async(
        self,
        query: str | None = None,
        include_versions: bool = False,
        include_counts: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[DataModel, ...]:
        """Async variant of :meth:`list_data_models`."""

        settings = self._snapshot_settings()

        return await _list_data_models_async(
            settings=settings,
            query=query,
            include_versions=include_versions,
            include_counts=include_counts,
            limit=limit,
            offset=offset,
        )

    def list_cdes(
        self,
        model_key: str,
        version: str,
        include_description: bool = False,
        query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[CDE, ...]:
        """Fetch CDEs for a data model version from the Data Model Store.

        Parameters
        ----------
        model_key:
            Data model key (e.g., 'ccdi').
        version:
            Version label (e.g., 'v1').
        include_description:
            Include CDE descriptions.
        query:
            Substring search on cde_key.
        limit:
            Maximum number of results to return.
        offset:
            Number of results to skip.
        """

        settings = self._snapshot_settings()

        return _list_cdes(
            settings=settings,
            model_key=model_key,
            version=version,
            include_description=include_description,
            query=query,
            limit=limit,
            offset=offset,
        )

    async def list_cdes_async(
        self,
        model_key: str,
        version: str,
        include_description: bool = False,
        query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[CDE, ...]:
        """Async variant of :meth:`list_cdes`."""

        settings = self._snapshot_settings()

        return await _list_cdes_async(
            settings=settings,
            model_key=model_key,
            version=version,
            include_description=include_description,
            query=query,
            limit=limit,
            offset=offset,
        )

    def list_pvs(
        self,
        model_key: str,
        version: str,
        cde_key: str,
        include_inactive: bool = False,
        query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[PermissibleValue, ...]:
        """Fetch permissible values for a CDE from the Data Model Store.

        Parameters
        ----------
        model_key:
            Data model key (e.g., 'ccdi').
        version:
            Version label (e.g., 'v1').
        cde_key:
            CDE key (e.g., 'sex_at_birth').
        include_inactive:
            Include inactive permissible values.
        query:
            Substring search on PV value.
        limit:
            Maximum number of results to return.
        offset:
            Number of results to skip.
        """

        settings = self._snapshot_settings()

        return _list_pvs(
            settings=settings,
            model_key=model_key,
            version=version,
            cde_key=cde_key,
            include_inactive=include_inactive,
            query=query,
            limit=limit,
            offset=offset,
        )

    async def list_pvs_async(
        self,
        model_key: str,
        version: str,
        cde_key: str,
        include_inactive: bool = False,
        query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[PermissibleValue, ...]:
        """Async variant of :meth:`list_pvs`."""

        settings = self._snapshot_settings()

        return await _list_pvs_async(
            settings=settings,
            model_key=model_key,
            version=version,
            cde_key=cde_key,
            include_inactive=include_inactive,
            query=query,
            limit=limit,
            offset=offset,
        )

    def get_pv_set(
        self,
        model_key: str,
        version: str,
        cde_key: str,
        include_inactive: bool = False,
    ) -> frozenset[str]:
        """Return all permissible values for a CDE as a set for O(1) membership testing.

        'why': validation use case requires efficient lookup; auto-paginates all results

        Parameters
        ----------
        model_key:
            Data model key (e.g., 'ccdi').
        version:
            Version label (e.g., 'v1').
        cde_key:
            CDE key (e.g., 'sex_at_birth').
        include_inactive:
            Include inactive permissible values.
        """

        settings = self._snapshot_settings()

        return _get_pv_set(
            settings=settings,
            model_key=model_key,
            version=version,
            cde_key=cde_key,
            include_inactive=include_inactive,
        )

    async def get_pv_set_async(
        self,
        model_key: str,
        version: str,
        cde_key: str,
        include_inactive: bool = False,
    ) -> frozenset[str]:
        """Async variant of :meth:`get_pv_set`."""

        settings = self._snapshot_settings()

        return await _get_pv_set_async(
            settings=settings,
            model_key=model_key,
            version=version,
            cde_key=cde_key,
            include_inactive=include_inactive,
        )

    def validate_value(
        self,
        value: str,
        model_key: str,
        version: str,
        cde_key: str,
    ) -> bool:
        """Check if a value is in the permissible values for a CDE.

        'why': convenience wrapper for the common validation use case

        Parameters
        ----------
        value:
            The value to validate.
        model_key:
            Data model key (e.g., 'ccdi').
        version:
            Version label (e.g., 'v1').
        cde_key:
            CDE key (e.g., 'sex_at_birth').
        """

        pv_set = self.get_pv_set(model_key, version, cde_key)
        return value in pv_set

    async def validate_value_async(
        self,
        value: str,
        model_key: str,
        version: str,
        cde_key: str,
    ) -> bool:
        """Async variant of :meth:`validate_value`."""

        pv_set = await self.get_pv_set_async(model_key, version, cde_key)
        return value in pv_set

    def _snapshot_settings(self) -> Settings:
        """Return a copy of the current settings or raise if not configured."""

        with self._lock:
            if self._settings is None:
                raise ClientConfigurationError(
                    "client not configured; call configure(api_key=...) before use"
                )
            return replace(self._settings)

    def _require_logger(self) -> logging.Logger:
        if self._logger is None:
            raise ClientConfigurationError(
                "client not configured; call configure(api_key=...) before use"
            )
        return self._logger
