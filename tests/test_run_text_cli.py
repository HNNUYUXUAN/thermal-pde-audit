from pathlib import Path
from typing import Any

from thermal_pde_audit import cli
from thermal_pde_audit.schema import ThermalExperimentSpec


VALID_TEXT = (
    "模拟长度10毫米、热扩散率1e-6平方米每秒、初始温升100K的"
    "一维热传导，计算0.1秒，使用32个空间点和50个时间步，使用CPU"
)


def test_run_text_executes_only_the_controlled_spec(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run_experiment(
        spec: ThermalExperimentSpec,
        output_dir: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        captured["spec"] = spec.to_dict()
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        return {
            "status": "success",
            "artifacts": {"result_json": str(output_dir / "result.json")},
        }

    monkeypatch.setattr(cli, "run_experiment", fake_run_experiment)
    monkeypatch.setattr(
        cli,
        "recommend_quantum_profile",
        lambda spec, validate_environment: {
            "status": "validated_profile",
            "selection_mode": "exact_empirical_match",
            "parameters": {
                "quantum_steps": 2,
                "ancilla_qubits": 8,
                "auxiliary_range": 16.0,
                "recovery_point": 1,
            },
        },
    )
    output_dir = tmp_path / "natural-language"

    exit_code = cli.main(
        [
            "run-text",
            "--text",
            VALID_TEXT,
            "--output",
            str(output_dir),
            "--error-decomposition",
        ]
    )

    assert exit_code == 0
    assert captured["spec"]["device"] == "cpu"
    assert captured["spec"]["length_m"] == 0.01
    assert captured["input_provenance"]["mode"] == "natural_language"
    assert captured["input_provenance"]["spec"] == captured["spec"]
    assert captured["input_provenance"]["execution_plan"][
        "validated_profile"
    ] is True
    assert captured["user_task"] == VALID_TEXT
    assert VALID_TEXT not in captured["reproduce_command"]
    assert "--input " in captured["reproduce_command"]
    assert str(output_dir / "input.json") in captured["reproduce_command"]
    assert captured["error_decomposition"] is True
    assert "--validated-profile" in captured["reproduce_command"]


def test_run_text_rejects_unsupported_boundary_before_execution(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    called = False

    def fail_if_called(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(cli, "run_experiment", fail_if_called)
    output_dir = tmp_path / "rejected"

    exit_code = cli.main(
        [
            "run-text",
            "--text",
            f"{VALID_TEXT}，采用周期边界",
            "--output",
            str(output_dir),
        ]
    )

    assert exit_code == 2
    assert called is False
    assert output_dir.exists() is False
