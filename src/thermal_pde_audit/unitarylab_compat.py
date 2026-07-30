"""Scoped compatibility helpers for the installed UnitaryLab heat adapter."""

from __future__ import annotations

import functools
import inspect
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol


_DEVICE_ROUTE_LOCK = threading.RLock()


class _SchrodingerizationModule(Protocol):
    """Structural type for the installed module patched by the adapter."""

    schro_trotter: Any


class DeviceRouteCompatibilityError(RuntimeError):
    """Raised when the installed lower-level API cannot accept a device."""


@contextmanager
def route_schro_trotter_device(
    schro_module: _SchrodingerizationModule,
    requested_device: str,
    routed_calls: list[dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Temporarily record and, when missing, inject the Trotter device.

    The installed 1D heat class imports ``schro_trotter`` from a shared module.
    A process-wide reentrant lock therefore covers the entire patched call.
    This prevents two project adapter calls in the same process from
    overwriting each other's device route.
    """

    original = schro_module.schro_trotter
    try:
        signature = inspect.signature(original)
    except (TypeError, ValueError) as exc:
        raise DeviceRouteCompatibilityError(
            "Cannot inspect the installed schro_trotter signature."
        ) from exc
    accepts_device = "device" in signature.parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if not accepts_device:
        raise DeviceRouteCompatibilityError(
            "Installed schro_trotter cannot accept a device argument; "
            f"observed signature: {signature}"
        )

    metadata: dict[str, Any] = {
        "strategy": "scoped_process_lock_and_call_recording",
        "requested_device": requested_device,
        "lower_level_signature": str(signature),
        "lock_scope": "current Python process",
        "injection_count": 0,
        "forwarded_count": 0,
        "conflict_count": 0,
        "all_devices_match_requested": True,
        "restored": False,
    }

    @functools.wraps(original)
    def routed(*args: Any, **kwargs: Any) -> Any:
        device_was_injected = "device" not in kwargs
        if device_was_injected:
            kwargs["device"] = requested_device
            metadata["injection_count"] += 1
        else:
            metadata["forwarded_count"] += 1
        routed_device = str(kwargs["device"]).lower()
        device_matches_requested = routed_device == requested_device
        if not device_matches_requested:
            metadata["conflict_count"] += 1
            metadata["all_devices_match_requested"] = False
        routed_calls.append(
            {
                "device": routed_device,
                "requested_device": requested_device,
                "device_was_injected": device_was_injected,
                "device_matches_requested": device_matches_requested,
                "Nt": kwargs.get("Nt"),
                "na": kwargs.get("na"),
                "R": kwargs.get("R"),
                "order": kwargs.get("order"),
                "point": kwargs.get("point"),
            }
        )
        if not device_matches_requested:
            raise DeviceRouteCompatibilityError(
                "Installed heat solver forwarded a conflicting lower-level "
                f"device: requested={requested_device}, observed={routed_device}."
            )
        return original(*args, **kwargs)

    with _DEVICE_ROUTE_LOCK:
        if schro_module.schro_trotter is not original:
            raise DeviceRouteCompatibilityError(
                "schro_trotter changed before the scoped route was installed."
            )
        schro_module.schro_trotter = routed
        try:
            yield metadata
        finally:
            schro_module.schro_trotter = original
            metadata["restored"] = schro_module.schro_trotter is original
