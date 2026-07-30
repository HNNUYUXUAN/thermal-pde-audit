from thermal_pde_audit.cli import _build_parser


def test_run_parser_accepts_schrodingerization_controls() -> None:
    args = _build_parser().parse_args(
        [
            "run",
            "--input",
            "examples/standard_heat.json",
            "--output",
            "results/standard_heat",
            "--quantum-steps",
            "32",
            "--ancilla-qubits",
            "8",
            "--auxiliary-range",
            "16",
            "--recovery-point",
            "1",
            "--supa-audit",
            "--validated-profile",
            "--custom-supa-audit",
            "--error-decomposition",
        ]
    )

    assert args.quantum_steps == 32
    assert args.ancilla_qubits == 8
    assert args.auxiliary_range == 16.0
    assert args.recovery_point == 1
    assert args.supa_audit is True
    assert args.validated_profile is True
    assert args.custom_supa_audit is True
    assert args.error_decomposition is True


def test_run_text_parser_accepts_controlled_execution_arguments() -> None:
    args = _build_parser().parse_args(
        [
            "run-text",
            "--text",
            (
                "模拟长度10毫米、热扩散率1e-6平方米每秒、"
                "初始温升100K的一维热传导，计算0.1秒，使用GPU"
            ),
            "--output",
            "results/natural_language_gpu_validation",
            "--compare-cpu-gpu",
            "--supa-audit",
            "--custom-supa-audit",
            "--error-decomposition",
            "--validated-profile",
        ]
    )

    assert args.command == "run-text"
    assert args.compare_cpu_gpu is True
    assert args.supa_audit is True
    assert args.custom_supa_audit is True
    assert args.error_decomposition is True
    assert args.validated_profile is True
    assert not hasattr(args, "device")


def test_plan_text_parser_accepts_only_text() -> None:
    args = _build_parser().parse_args(
        ["plan-text", "--text", "请模拟一维热传导"]
    )

    assert args.command == "plan-text"
    assert args.text == "请模拟一维热传导"


def test_recommend_parser_accepts_controlled_input() -> None:
    args = _build_parser().parse_args(
        ["recommend", "--input", "examples/standard_heat.json"]
    )

    assert args.command == "recommend"


def test_validate_result_parser_accepts_device_requirements() -> None:
    args = _build_parser().parse_args(
        [
            "validate-result",
            "--result-dir",
            "results/fast_quantum_validation",
            "--require-gpu",
            "--require-supa",
            "--require-custom-supa",
            "--require-error-decomposition",
            "--require-natural-language",
        ]
    )

    assert args.command == "validate-result"
    assert args.require_gpu is True
    assert args.require_supa is True
    assert args.require_custom_supa is True
    assert args.require_error_decomposition is True
    assert args.require_natural_language is True


def test_validate_profiles_parser_is_controlled() -> None:
    args = _build_parser().parse_args(["validate-profiles"])

    assert args.command == "validate-profiles"


def test_validate_interactions_parser_has_controlled_default() -> None:
    args = _build_parser().parse_args(["validate-interactions"])

    assert args.command == "validate-interactions"
    assert str(args.interactions_dir) == "results\\interactions" or str(
        args.interactions_dir
    ) == "results/interactions"
