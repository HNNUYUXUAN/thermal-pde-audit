# 科学基础

## 热方程参考问题

受控实验求解：

```text
∂T/∂t = α ∂²T/∂x²,      0 < x < L
T(0,t) = T(L,t) = 0
T(x,0) = A sin(πx/L)
```

解析解为：

```text
T(x,t) = A exp[-α(π/L)²t] sin(πx/L)
```

解析解为每个空间点提供直接的物理参考。

## 经典离散

显式中心有限差分更新为：

```text
Tᵢⁿ⁺¹ = Tᵢⁿ + r(Tᵢ₋₁ⁿ - 2Tᵢⁿ + Tᵢ₊₁ⁿ)
r = αΔt/Δx²
```

求解前检查经典稳定性条件 `r ≤ 1/2`，从而形成时间和空间离散均透明的独立
数值基线。

## 无量纲化

将物理实验映射为：

```text
x* = x/L
t* = αt/L²
```

归一化方程具有单位长度和单位热扩散率。量子执行结束后再按初始温升恢复温度
尺度。无量纲时长即 Fourier 数：

```text
Fo = αt/L²
```

## Schrödingerization 量子仿真层

量子仿真路径调用 UnitaryLab Algorithms 的热方程 Schrödingerization
实现。本项目提供：

- 物理量到无量纲参数的映射；
- 有保存证据的精确量子参数档案；
- CPU/GPU 设备路由与路由记录；
- 温度场提取和 SI 尺度恢复；
- 独立参考求解器与数值审计。

每次完整运行比较：

1. 连续解析解；
2. 中心差分半离散系统的精确演化；
3. 同参数 Schrödingerization 恢复；
4. Trotter 量子线路结果。

该分层在同一结果包中呈现空间离散、辅助恢复和 Trotter 演化带来的差异。

## 物理审计

审计覆盖：

- 温度场有限性；
- 零 Dirichlet 边界补全；
- 温度范围与最大值原理；
- 一阶模态衰减；
- 经典有限差分稳定性；
- 解析、经典和量子误差指标；
- CPU/GPU 温度场一致性；
- SUPA 与 NumPy 指标一致性。

## 参考文献与实现

1. S. Jin and N. Liu, “Analog quantum simulation of partial differential
   equations,” *Physical Review Letters* 130, 080401 (2023).
   <https://doi.org/10.1103/PhysRevLett.130.080401>
2. S. Jin, N. Liu, and Y. Yu, “Quantum simulation of partial differential
   equations via Schrödingerisation,” arXiv:2212.13969.
   <https://arxiv.org/abs/2212.13969>
3. S. Jin, N. Liu, and Y. Yu, “Quantum simulation of partial differential
   equations: Applications and detailed analysis,” arXiv:2303.13088.
   <https://arxiv.org/abs/2303.13088>
4. [UnitaryLab Algorithms](https://github.com/unitarylab/unitarylab_algorithms)
   提供本项目调用的热方程 Schrödingerization 实现。
