"""Static project capability boundary."""

from __future__ import annotations


def capability_summary() -> dict[str, object]:
    """Return the first-round supported and rejected scope."""

    return {
        "supported": {
            "task": ["heat_equation_1d"],
            "boundary": ["dirichlet_zero"],
            "initial_condition": ["sine_mode_1"],
            "source": ["zero"],
            "devices": ["cpu", "gpu"],
            "spatial_points": "power of two within [4, 256]",
            "validated_quantum_profiles": (
                "exact Fo/spatial-point matches in validated_profiles.json; "
                "no interpolation or extrapolation"
            ),
            "supa_audit": (
                "real torch.supa error reductions with independent NumPy "
                "consistency checks"
            ),
            "custom_supa_audit": (
                "project-owned fixed-path float32 .su single-block parallel "
                "reduction for aligned thermal fields of at most 256 values"
            ),
            "saved_result_validation": (
                "framework-free checks for the six artifacts, exact profile, "
                "GPU route, torch.supa, custom SUPA, report, and PNG"
            ),
        },
        "not_supported": [
            "2D geometry",
            "nonlinear PDE",
            "arbitrary boundary conditions",
            "arbitrary source functions",
            "arbitrary code execution",
            "material database lookup",
            "quantum hardware execution",
            "multi-block or large-field custom SUPA reduction",
            "quantum advantage claims",
        ],
    }
