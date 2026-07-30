# Input Protocol

## Structured schema

```json
{
  "task": "heat_equation_1d",
  "length_m": 0.01,
  "thermal_diffusivity_m2_s": 1e-6,
  "initial_amplitude_k": 100.0,
  "duration_s": 0.1,
  "spatial_points": 32,
  "time_steps": 50,
  "boundary": "dirichlet_zero",
  "initial_condition": "sine_mode_1",
  "device": "gpu",
  "seed": 42
}
```

Required physical values are positive SI numbers:

- `length_m`
- `thermal_diffusivity_m2_s`
- `initial_amplitude_k`
- `duration_s`

Accepted configuration values:

- `task = heat_equation_1d`
- `boundary = dirichlet_zero`
- `initial_condition = sine_mode_1`
- `device = cpu | gpu`
- `spatial_points` is a power of two from 4 through 256
- `time_steps` is an integer from 1 through 100000

## Natural-language units

Recognize:

- metre, millimetre, centimetre;
- second, millisecond;
- kelvin or Celsius temperature difference;
- square metre, square millimetre, or square centimetre per second.

Convert every accepted value to SI before execution and record the original
text and conversion source.

## Derived values

Compute:

```text
Fo = thermal_diffusivity_m2_s * duration_s / length_m²
dx = length_m / (spatial_points + 1)
r  = thermal_diffusivity_m2_s * dt / dx²
```

Use `Fo + spatial_points` to query the exact validated quantum profile.
