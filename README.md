# Simplified Compressed Population-scale Network Netherlands 2009-2023 in MLN format

Scripts that turn the detailed, directed 33-layer population network of the Netherlands ([doi:10.34894/8575OP](https://doi.org/10.34894/8575OP)) into a **simplified, undirected 5-layer network** in the compressed MLN format of [`mlnlib`](https://github.com/planet-nl/mlnlib).

| | |
|---|---|
| **Dataset** | Simplified Compressed Population-scale Network Netherlands 2009-2023 in MLN format |
| **DOI** | forthcoming |
| **Content** | One network per year: 5 layers (household, school, neighbor, work, family), undirected edges |
| **Years** | 2009–2023 |
| **Access** | CBS Microdata environment, CBS project 9629 |

The input is produced by [compressed_population_scale_network_nl](https://github.com/planet-nl/compressed_population_scale_network_nl). This is one of three related datasets, see [Related datasets](#related-datasets).


## Overview

```
compressed_population_scale_network_nl        this repository                      output
┌──────────────────────────────┐      ┌──────────────────────────────┐      ┌──────────────────────────────┐
│ detailed multilayer network  │ ───▶ │ drop selected layer types    │ ───▶ │ 5 layers: household, school, │
│ 33 CBS layer types           │      │ group by 'group' column      │      │ neighbor, work, family       │
│ directed edges               │      │ symmetrize (undirected)      │      │ undirected, same node set    │
└──────────────────────────────┘      └──────────────────────────────┘      └──────────────────────────────┘
```

The script:

1. **Drops** selected relationship types (see [Excluded relationships](#excluded-relationships)).
2. **Groups** the remaining detailed CBS layers into 5 social contexts, using the `group` column of the input `layers.csv`.
3. **Symmetrizes** every grouped layer: an undirected edge exists if the directed edge exists in either direction.
4. **Keeps** the node set and the node table (`nodes.csv.gz`) of the input network unchanged.

### Output layers

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


## Data format

Input and output both use the **MLN (MultiLayerNetwork) format** of `mlnlib`: one directory per year containing

| File            | Content                                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------------------------|
| `nodes.csv.gz`  | Node table, 9 columns: `label, id, active, gender, birth_year, migrant_generation, number_of_parents_from_abroad, missing_mother, missing_father` |
| `layers.csv`    | Layer definitions: `layer_id, layer, label, binary` (output); input also has `group`                        |
| `edges.npz`     | Sparse N × N adjacency matrix with binary-encoded layer types; symmetric `uint8` in the output              |

In the **input**, the edges are directed and `layers.csv` must have a `group` column whose values match the `label` values of this repository's `layers.csv`. In the **output**, the adjacency matrix is symmetric. `id` is the row/column index in `edges.npz`, the same in every year and in all three related datasets.


## Requirements

- Python 3.10+
- `pandas`, `scipy`, `polars`, `mlnlib`

The published data were produced with `mlnlib` 0.2.39; 0.3.0 should work as well.

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

### All years with `00_run_all.sh`

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

Paths are joined with `os.path.join`, so the scripts run both in the CBS RA (Windows) and on Linux/macOS. The script processes the years in order, each in its own Python process. It writes timestamped `log_messages_*.log` (stdout) and `log_error_*.log` (stderr) files to `output_folder`. The Python interpreter path in the script (`/c/mambaforge/envs/9629/python.exe`) is specific to the CBS RA environment; change it for other environments.


## Repository structure

```
.
├── 00_run_all.sh         # Runs grouped_networks.py for a range of years
├── grouped_networks.py   # Simplifies one year's network
├── layers.csv            # Target 5-layer definition, read from the script's own directory
└── README.md
```


## Related datasets

The three datasets cover 2009–2023 and share the same nodes: every person has the same `id` and `label` (RINPERSOON) in all of them, and the yearly population (`active`) is defined on 1 January. The `nodes.csv.gz` of the two network datasets holds the first 9 columns of the node attribute tables. All three are available in the CBS Microdata environment (CBS project 9629) and can be read with [`mlnlib`](https://github.com/planet-nl/mlnlib) ([PyPI](https://pypi.org/project/mlnlib/)).

| Dataset | Content | DOI | Code |
|---|---|---|---|
| Compressed Population-scale Network Netherlands 2009-2023 in MLN format | 33 layers, directed | [10.34894/8575OP](https://doi.org/10.34894/8575OP) | [compressed_population_scale_network_nl](https://github.com/planet-nl/compressed_population_scale_network_nl) |
| Simplified Compressed Population-scale Network Netherlands 2009-2023 in MLN format | 5 layers, undirected | forthcoming | [compressed_population_scale_network_nl_simplified](https://github.com/planet-nl/compressed_population_scale_network_nl_simplified) |
| Detailed Node Attributes for Compressed Population-scale Network Netherlands 2009-2023 | Yearly node attribute tables | forthcoming | [compressed_population_scale_network_nl_detailed_node_files](https://github.com/planet-nl/compressed_population_scale_network_nl_detailed_node_files) |


## How to cite

Please cite the dataset(s) you use:

> Bokányi, E., Kazmina, Y., Heemskerk, E. M., & Takes, F. W. (2025). *Compressed Population-scale Network Netherlands 2009-2023 in MLN format* [Data set]. ODISSEI Portal. https://doi.org/10.34894/8575OP

> Bokányi, E., Kazmina, Y., Heemskerk, E. M., & Takes, F. W. (2026). *Simplified Compressed Population-scale Network Netherlands 2009-2023 in MLN format* [Data set]. ODISSEI Portal. DOI forthcoming.

> Bokányi, E., Kazmina, Y., Heemskerk, E. M., & Takes, F. W. (2026). *Detailed Node Attributes for Compressed Population-scale Network Netherlands 2009-2023* [Data set]. ODISSEI Portal. DOI forthcoming.

and the paper describing the network:

> Bokányi, E., Heemskerk, E. M., & Takes, F. W. (2023). The anatomy of a population-scale social network. *Scientific Reports*, 13, 9209. https://doi.org/10.1038/s41598-023-36324-9


## Authors and contact

Eszter Bokányi (Leiden University), Yuliia Kazmina (University of Amsterdam), Eelke M. Heemskerk (University of Amsterdam), Frank W. Takes (Leiden University), and the PLANET-NL team (https://planetnl.org).

For questions, contact the PLANET-NL team: info@planetnl.org
