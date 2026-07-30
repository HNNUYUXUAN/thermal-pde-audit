# 参考与致谢

`thermal-pde-audit` 是一个采用 MIT License 开源的科研竞赛项目。项目在
开源科学计算软件和壁仞竞赛计算平台的支持下，完成了一维热传导量子仿真、
物理审计与可复现实验链路。

## 软件与计算平台

- [UnitaryLab Algorithms](https://github.com/unitarylab/unitarylab_algorithms)
  提供本项目量子仿真层调用的热方程 Schrödingerization 实现。
- [UnitaryLab](https://pypi.org/project/unitarylab/) 提供量子线路构造、
  CPU/GPU 模拟执行、日志与线路可视化能力。
- 壁仞 SUPA SDK、`torch_br` 与竞赛容器提供 Biren GPU 运行环境和 `.su`
  编译工具链。
- [PyTorch](https://pytorch.org/) 与 `torch.supa` 提供张量执行和设备侧
  误差归约能力。
- [NumPy](https://numpy.org/)、[SciPy](https://scipy.org/) 与
  [Matplotlib](https://matplotlib.org/) 支持解析/经典基线、半离散精确演化
  和实验可视化。
- [pytest](https://pytest.org/)、[Ruff](https://docs.astral.sh/ruff/) 与
  [Mypy](https://www.mypy-lang.org/) 支持自动化测试和代码质量验证。

项目的自然语言实验协议、量子参数档案、CPU/GPU 路由适配、经典与解析基线、
双 SUPA 误差验证、物理审计、证据校验、报告与可视化系统由本项目实现。

## 科学基础

项目参考线性偏微分方程 Schrödingerization 研究与经典热方程有限差分方法，
并将解析解、半离散参考、同参数恢复和 Trotter 结果组织为可比较的误差层。
论文、公式及其在验证体系中的作用见
[docs/scientific_basis.md](docs/scientific_basis.md)。

感谢赛事组织方、壁仞平台团队和 UnitaryLab 开源社区提供计算环境、框架与
技术资料，使端到端量子 PDE 实验得以完成并开源复现。
