# Instance Generator for JSP & FJSP (Energy‑aware)

## Description

Instance generator for the **Job Shop Scheduling Problem (JSP)** and the **Flexible Job Shop Scheduling Problem (FJSP)** with speed‑scaling and optional release/due dates. The generator produces instances in **JSON**, **MiniZinc DZN**, and **Taillard-like text** formats, and it is designed for reproducible experiments via a random seed.

### Key features

- Supports **JSP** and **FJSP** (`instance_type="JSP"` or `instance_type="FJSP"`).
- **Energy‑aware speed scaling**: each operation can be executed at one of several speeds; processing time and energy consumption are linked per speed.
- **Release/Due date modes** (`ReleaseDateDueDate`): `0` (none), `1` (per job), `2` (per operation).
- Multiple output formats: **JSON**, **DZN** (MiniZinc templates), **Taillard-style** text.
- **Distributions** for data generation: `uniform`, `normal`, `exponential`.
- Reproducibility via **seed**.
- **FJSP** adds a per‑job binary vector of **available machines**.

> **About value ranges & scaling**
>
> - With the **uniform** distribution, base operation costs are sampled within **[10, 100]**.
> - Initial *release times* are sampled from **[0, 100]** (in steps of 10) and then normalized to start at 0.
> - **Energy consumption** values are normalized into **[1, 100]** by construction.
> - **Processing times** are derived from base costs and speed scaling and **are not capped** at 100 (they can exceed 100), especially with `normal`/`exponential` draws.
>
> As a result, energy values and the initial release‑date seeds are within 0–100; if you need strict 0–100 ranges for *all* fields, set an external rescaling on the produced arrays or constrain generation to `distribution="uniform"` and adjust your post‑processing accordingly.

---

## Python API

### Generator initialization

```python
from IGJSP.generador import Generator

gen = Generator(
    json=False,                 # write JSON files
    dzn=False,                  # write DZN files (MiniZinc)
    taillard=False,             # write Taillard-like txt
    savepath="./output",        # base output directory/template
    single_folder_output=False  # put artifacts in a single folder
)
```

### Instance creation

```python
obj = gen.generate_new_instance(
    jobs=10, machines=4,
    speed=1,                      # number of speed levels
    ReleaseDateDueDate=0,         # 0 (none), 1 (per job), 2 (per operation)
    distribution="uniform",       # 'uniform' | 'normal' | 'exponential'
    seed=1,
    tpm=[],                       # optional per-machine time scale
    instance_type="JSP",          # 'JSP' (default) or 'FJSP'
    size=1                        # how many instances to emit (looped)
)
```

If all three output flags (`json`, `dzn`, `taillard`) are `False`, the function returns the in‑memory instance object (`JSP` or `FJSP`). Otherwise, it writes files under `savepath` and returns the last instance created.

---

## Generating a JSP problem instance

To generate an instance of the problem, use the `Generator` class (module `Generador`). Initialize it and then call `generate_new_instance` with the parameters below.

### Parameters (generation)

1. **Jobs:** `jobs` — number of jobs. Default: `10`
2. **Machines:** `machines` — number of machines. Default: `4`
3. **Release and Due Date:** `ReleaseDateDueDate`
   - `0`: neither jobs nor operations have release/due times (default)
   - `1`: each job has a release and due date
   - `2`: each operation has a release and due date
4. **Speeds:** `speed` — number of speed levels. Default: `1`
5. **Distribution:** `distribution` — `uniform`, `normal`, or `exponential`. Default: `normal`
6. **Seed:** `seed` — random seed for reproducibility. Default: `1`

### Parameters (output)

- **JSON:** `json` (bool) — write JSON file(s). Default: `False`
- **DZN:** `dzn` (bool) — write MiniZinc DZN file(s). Default: `False`
- **Taillard:** `taillard` (bool) — write Taillard-like text file. Default: `False`
- **Save Path:** `savepath` (str) — base path/template for outputs. Default: `./output`
- **Single folder:** `single_folder_output` (bool) — whether to write all artifacts into a single folder. Default: `False`

### Example (JSP)

```python
from IGJSP.generador import Generator
generator = Generator(json=True, savepath="output")
generator.generate_new_instance(
    jobs=4, machines=2,
    ReleaseDateDueDate=2,
    distribution="exponential",
    seed=53
)
```

### Example of JSON generated (JSP)

```json
{
    "nbJobs": [
        0,
        1
    ],
    "nbMchs": [
        0,
        1,
        2,
        3
    ],
    "speed": 1,
    "timeEnergy": [
        {
            "jobId": 0,
            "operations": {
                "0": {
                    "speed-scaling": [
                        {
                            "procTime": 8,
                            "energyCons": 92
                        }
                    ],
                    "release-date": 30,
                    "due-date": 41
                },
                "2": {
                    "speed-scaling": [
                        {
                            "procTime": 17,
                            "energyCons": 84
                        }
                    ],
                    "release-date": 41,
                    "due-date": 77
                },
                "3": {
                    "speed-scaling": [
                        {
                            "procTime": 3,
                            "energyCons": 97
                        }
                    ],
                    "release-date": 77,
                    "due-date": 80
                },
                "1": {
                    "speed-scaling": [
                        {
                            "procTime": 7,
                            "energyCons": 93
                        }
                    ],
                    "release-date": 80,
                    "due-date": 88
                }
            },
            "release-date": 30,
            "due-date": 88
        },
        {
            "jobId": 1,
            "operations": {
                "1": {
                    "speed-scaling": [
                        {
                            "procTime": 4,
                            "energyCons": 96
                        }
                    ],
                    "release-date": 0,
                    "due-date": 5
                },
                "3": {
                    "speed-scaling": [
                        {
                            "procTime": 3,
                            "energyCons": 97
                        }
                    ],
                    "release-date": 5,
                    "due-date": 9
                },
                "2": {
                    "speed-scaling": [
                        {
                            "procTime": 1,
                            "energyCons": 99
                        }
                    ],
                    "release-date": 9,
                    "due-date": 10
                },
                "0": {
                    "speed-scaling": [
                        {
                            "procTime": 6,
                            "energyCons": 94
                        }
                    ],
                    "release-date": 10,
                    "due-date": 17
                }
            },
            "release-date": 0,
            "due-date": 17
        }
    ],
    "minMakespan": 35,
    "minEnergy": 752,
    "maxMinMakespan": 14,
    "maxMinEnergy": 0
}
```

---

## Generating an FJSP problem instance

Set `instance_type="FJSP"` to enable flexible routing. In the JSON output, each job includes an `available_machines` binary vector of length `nbMchs`, indicating where the job's operations can be processed (`1` = available, `0` = not available).

### Example (FJSP)

```python
from IGJSP.generador import Generator
generator = Generator(json=True, savepath="output")
generator.generate_new_instance(
    jobs=3, machines=3,
    speed=1,
    ReleaseDateDueDate=0,
    distribution="uniform",
    seed=7,
    instance_type="FJSP"
)
```

### Example of JSON generated (FJSP)

Abridged example to illustrate the additional `available_machines` field:

```json
{
  "nbJobs": [0,1,2],
  "nbMchs": [0,1,2],
  "speed": 1,
  "timeEnergy": [
    {
      "jobId": 0,
      "available_machines": [1,0,1],
      "operations": {
        "0": { "speed-scaling": [ { "procTime": 12, "energyCons": 90 } ] },
        "2": { "speed-scaling": [ { "procTime": 18, "energyCons": 84 } ] },
        "1": { "speed-scaling": [ { "procTime": 11, "energyCons": 89 } ] }
      }
    },
    {
      "jobId": 1,
      "available_machines": [1,1,0],
      "operations": {
        "2": { "speed-scaling": [ { "procTime": 7, "energyCons": 93 } ] },
        "0": { "speed-scaling": [ { "procTime": 5, "energyCons": 95 } ] },
        "1": { "speed-scaling": [ { "procTime": 13, "energyCons": 88 } ] }
      }
    }
  ],
  "minMakespan": 123,
  "minEnergy": 456,
  "maxMinMakespan": 78,
  "maxMinEnergy": 90
}
```

---

## Notes on outputs

- **JSON**: Contains `nbJobs`, `nbMchs`, `speed`, and a `timeEnergy` list with per‑job `operations`. For `ReleaseDateDueDate=1` (per job) or `2` (per operation), `release-date`/`due-date` fields are added accordingly.
- **DZN**: The generator writes `.dzn` files using templates located inside generator packages, parameterized by the selected RD mode and speed levels.
- **Taillard-like**: Writes textual matrices for processing times, energy consumption, and the job‑specific machine order; the FJSP variant also appends an `Available machines:` section (binary rows per job).

---

## Reproducibility & scaling tips

- Use a fixed `seed` to reproduce instances exactly.
- For tighter value ranges (e.g., unit testing), prefer `distribution="uniform"` and post‑scale arrays if you require strict bounds (e.g., map processing times to `[1,100]` after generation). Energy values are already normalized to `[1,100]` by design.
