# Compressed Population Scale Network NL – Simplified

Scripts that turn the detailed, directed multilayer population network of the Netherlands into a **simplified, undirected 5-layer network**.

Part of the **PLANET-NL** project pipeline for population-scale social network data from CBS (Statistics Netherlands). The input is produced by [compressed_population_scale_network_nl](https://github.com/planet-nl/compressed_population_scale_network_nl).

```
compressed_population_scale_network_nl        this repository                      output
┌──────────────────────────────┐      ┌──────────────────────────────┐      ┌──────────────────────────────┐
│ detailed multilayer network  │ ───▶ │ drop selected layer types    │ ───▶ │ 5 layers: household, school, │
│ many CBS layer types         │      │ group by 'group' column      │      │ neighbor, work, family       │
│ directed edges               │      │ symmetrize (undirected)      │      │ undirected, same node set    │
└──────────────────────────────┘      └──────────────────────────────┘      └──────────────────────────────┘
```

## What the script does

1. **Drops** selected relationship types (see [Excluded relationships](#excluded-relationships)).
2. **Groups** the remaining detailed CBS layers into 5 social contexts, using the `group` column of the input `layers.csv`.
3. **Symmetrizes** every grouped layer: an undirected edge exists if the directed edge exists in either direction.
4. **Keeps** the node set and all node attributes of the input network.

## Output layers

| `layer_id` | `layer` | `label`   | `binary` | Description                |
|-----------:|--------:|-----------|---------:|----------------------------|
| 0          | 1       | household | 1        | Co-residence relationships |
| 1          | 2       | school    | 2        | Educational connections    |
| 2          | 3       | neighbor  | 4        | Neighborhood proximity     |
| 3          | 4       | work      | 8        | Workplace relationships    |
| 4          | 5       | family    | 16       | Kinship ties               |

Each adjacency-matrix entry is the sum of the binary codes of the layers an edge belongs to. For example, `17 = 16 + 1` means a tie that is both *family* and *household*. The matrix is stored as `uint8` (maximum value 31). This table is defined in [`layers.csv`](layers.csv).

### Excluded relationships

| CBS layer     | Relationship                    | Reason                                             |
|---------------|---------------------------------|----------------------------------------------------|
| 102           | Sampled neighbor links          | Random neighborhood sample, not actual proximity   |
| 320, 321, 322 | By-partnership family members   | Indirect kin via a partner, often non-reciprocated |
| 402           | Institutional household members | Only people living at the same address are kept    |

## Repository structure

```
.
├── 00_run_all.sh         # Batch processing over a range of years
├── grouped_networks.py   # Simplifies one year's network
├── layers.csv            # Target 5-layer definition and binary encoding
└── README.md
```

`grouped_networks.py` reads the target encoding from the `layers.csv` **next to the script**, so keep the two files together.

## Requirements

- Python 3.10+
- `pandas`, `scipy`, `polars`, `mlnlib==0.2.39`

```bash
pip install pandas scipy polars mlnlib==0.2.39
```

## Usage

### One year

```bash
python grouped_networks.py <input_folder> <output_folder> <year>
```

| Argument        | Meaning                                                                        |
|-----------------|--------------------------------------------------------------------------------|
| `input_folder`  | Directory with one MLN subdirectory per year (output of the upstream pipeline) |
| `output_folder` | Directory to write to; a `<year>` subdirectory is created                      |
| `year`          | Year to process, e.g. `2009`                                                   |

```bash
python grouped_networks.py H:\\ODISSEI_portal_A H:\\ODISSEI_portal_B 2009   # CBS Remote Access (Windows)
python grouped_networks.py /data/detailed /data/simplified 2009             # Linux / macOS
```

### Several years

Edit the variables at the top of [`00_run_all.sh`](00_run_all.sh), then run it from any directory:

```bash
bash 00_run_all.sh
```

| Variable        | Default               |
|-----------------|-----------------------|
| `input_folder`  | `H:\\ODISSEI_portal_A` |
| `output_folder` | `H:\\ODISSEI_portal_B` |
| `start_year`    | `2009`                |
| `end_year`      | `2023`                |

The script processes the years in order, each in its own Python process. It writes timestamped `log_messages_*.log` (stdout) and `log_error_*.log` (stderr) files to `output_folder`. The Python interpreter path in the script (`/c/mambaforge/envs/9629/python.exe`) is specific to the CBS RA environment; change it for other environments.

## Data format

Input and output both use the **MLN (MultiLayerNetwork) library format** of `mlnlib`: one directory per year containing

| File            | Content                                                     |
|-----------------|-------------------------------------------------------------|
| `nodes.csv.gz`  | Node attributes                                             |
| `layers.csv`    | Layer definitions (`layer`, `label`, `binary`, …)           |
| `edges.npz`     | Sparse adjacency matrix with binary-encoded layer types     |

In the **input**, the edges are directed and `layers.csv` must have a `group` column whose values match the `label` values of this repository's `layers.csv`. In the **output**, the adjacency matrix is symmetric.

## Notes

- **Edge counts.** The log reports the number of *undirected* edges. Because the matrix is symmetric, `A.nnz` is about twice that number.
- **Memory.** The full population network is held in memory, together with one filtered copy per grouped layer while that layer is processed. Make sure enough RAM is available.
- **Paths.** Paths are built with `os.path.join`, so the script runs on both Windows (CBS RA) and Linux/macOS.

## Troubleshooting

| Problem                       | Check                                                                                         |
|-------------------------------|-----------------------------------------------------------------------------------------------|
| Input files not found         | `input_folder/<year>/` contains `nodes.csv.gz`, `layers.csv` and `edges.npz`                  |
| `KeyError` on a group name    | Every `group` value in the input `layers.csv` appears as a `label` in this repo's `layers.csv` |
| `layers.csv` not found        | `layers.csv` sits in the same directory as `grouped_networks.py`                              |
| Out of memory                 | Run on a machine with more RAM; years already run in separate processes                       |

## Author

**Eszter Bokanyi** · e.bokanyi@liacs.leidenuniv.nl · PLANET-NL · November 2025

## Related projects

- [compressed_population_scale_network_nl](https://github.com/planet-nl/compressed_population_scale_network_nl): upstream pipeline that generates the detailed networks.
