# Acknowledgments

`thermal-pde-audit` is an MIT-licensed research and competition project built
with open scientific software and the competition's Biren computing platform.

## Software and platforms

- [UnitaryLab Algorithms](https://github.com/unitarylab/unitarylab_algorithms)
  provides the Schrödingerization heat-equation implementation used by the
  CPU/GPU simulation layer.
- [UnitaryLab](https://pypi.org/project/unitarylab/) provides quantum circuit
  construction, execution, logs, and circuit visualizations.
- Biren SUPA SDK, `torch_br`, and the competition container provide the Biren
  GPU runtime and `.su` compiler toolchain.
- [PyTorch](https://pytorch.org/) and `torch.supa` provide tensor execution and
  device-side error reductions.
- [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), and
  [Matplotlib](https://matplotlib.org/) support numerical baselines, exact
  semi-discrete evolution, and visualization.
- [pytest](https://pytest.org/), [Ruff](https://docs.astral.sh/ruff/), and
  [Mypy](https://www.mypy-lang.org/) support automated validation.

The repository contains project code and generated experiment evidence. The
listed frameworks remain under their respective upstream licenses.

## Scientific foundations

The implementation is informed by the Schrödingerization literature for
linear PDEs and by standard finite-difference heat-equation analysis. Papers,
equations, and their role in the validation design are listed in
[docs/scientific_basis.md](docs/scientific_basis.md).

We thank the competition organizers, the Biren platform team, and the
UnitaryLab open-source community for providing the environment and software
that made the end-to-end experiment possible.
