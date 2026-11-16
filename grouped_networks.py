"""
Multilayer Network Simplification: Detailed to Grouped Layers
==============================================================

Author: Eszter Bokanyi, e.bokanyi@liacs.leidenuniv.nl
Date: November 18, 2025
Project: PLANET-NL

Description:
-----------
This script processes population-scale multilayer networks by simplifying detailed layer types 
into 5 broad social context categories: household, school, neighbor, work, and family.

The transformation includes:
1. Filtering out specific relationship types (see Excluded Layers below)
2. Grouping detailed CBS layer types into broader categories based on the 'group' column
3. Converting directed edges to undirected by symmetrizing the adjacency matrix
4. Preserving all node attributes from the original network

Input:
------
- Compressed multilayer network in MLN format (from the output of the compressed_population_scale_network_nl repository)
- Input network must contain a layers.csv with a 'group' column for layer aggregation
- Binary-encoded adjacency matrix with detailed layer types

Output:
-------
- Simplified 5-layer undirected network in MLN format
- Binary encodings: household=1, school=2, neighbor=4, work=8, family=16
- Same node set and attributes as input network
- Compressed sparse matrix representation

Excluded Layers:
---------------
- CBS layer 102: Sampled neighbor links (random neighborhood connections)
- CBS layers 320-322: By-partnership family members (non-reciprocated kin ties)
- CBS layer 402: Institutional household members (only same-address residents retained)

Usage:
------
python grouped_networks.py <input_folder> <output_folder> <year>

Arguments:
    input_folder  : Path to directory containing year subdirectories with MLN format networks
    output_folder : Path where simplified networks will be saved (year subdirectories created)
    year          : Year to process (integer, e.g., 2009)

Example:
--------
python grouped_networks.py H:\\ODISSEI_portal_A H:\\ODISSEI_portal_B 2009

Notes:
------
- Requires mlnlib library for loading/saving MLN format
- Uses sparse matrix operations for memory efficiency
- Processing time depends on network size (typically minutes to hours for population-scale)
- The target encoding is read from layers.csv located next to this script

"""

import sys
import os

import pandas as pd

import gc
from time import time
import json

from mlnlib.mln import MultiLayerNetwork
from scipy.sparse import csr_matrix

from warnings import filterwarnings
filterwarnings("ignore")

# ==============================================================================
# COMMAND LINE ARGUMENTS
# ==============================================================================

input_folder = sys.argv[1]   # Source directory with detailed MLN networks
output_folder = sys.argv[2]  # Destination directory for simplified networks
year = int(sys.argv[3])      # Year to process

# ==============================================================================
# STEP 1: LOAD AND FILTER LAYER DEFINITIONS
# ==============================================================================

# Load the detailed layer table from the input network
# This table contains the mapping from detailed CBS layer types to broader groups
layer_to_binary = pd.read_csv(os.path.join(input_folder, str(year), "layers.csv"))

# Identify layers to exclude from the simplified network
# These are filtered out due to data quality or analytical considerations

# Layer 102: Sampled neighbor links (random neighborhood sample, not actual proximity)
sampled_neighbor_layer = layer_to_binary[layer_to_binary["layer"] == 102].index.tolist()

# Layers 320-322: By-partnership family members (indirect kin via spouse, often non-reciprocated)
by_partnership_family_layers = layer_to_binary[layer_to_binary["layer"].isin([320, 321, 322])].index.tolist()

# Layer 402: Institutional household members (nursing homes, prisons, etc. - not true co-residence)
institutional_household_layer = layer_to_binary[layer_to_binary["layer"] == 402].index.tolist()

# Combine all exclusion indices and remove from layer table
indices_to_drop = sampled_neighbor_layer + by_partnership_family_layers + institutional_household_layer
print("Layers to exclude from simplified network:")
print(layer_to_binary.loc[indices_to_drop])
layer_to_binary.drop(indices_to_drop, inplace=True)

# ==============================================================================
# STEP 2: CREATE GROUPED LAYER MAPPINGS
# ==============================================================================

# Group detailed layers by their 'group' column and sum their binary encodings
# This creates a mapping from group name (e.g., 'family') to combined binary value
layer_to_binary = layer_to_binary.groupby("group").sum()["binary"].to_dict()

# Calculate total binary encoding (sum of all layer encodings)
# This represents the complete network with all included layers
total_binnum = 0
for k, v in layer_to_binary.items():
    total_binnum += v

print("\nGrouped layer binary encodings (from detailed network):")
print(json.dumps(layer_to_binary, indent=4))

# Create output directory structure if it doesn't exist
output_year_path = os.path.join(output_folder, str(year))
if not os.path.exists(output_year_path):
    os.mkdir(output_year_path)

# Load the target binary encoding scheme for the simplified network
# This defines the new encoding: household=1, school=2, neighbor=4, work=8, family=16
new_layers = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "layers.csv"))
layer_to_new_binary = new_layers.set_index("label")["binary"].to_dict()

print("\nTarget layer binary encodings (for simplified network):")
print(json.dumps(layer_to_new_binary, indent=4))

# ==============================================================================
# STEP 3: LOAD NETWORK AND INITIALIZE STRUCTURES
# ==============================================================================

print(f"\nLoading network for year {year}...")
tic = time()
popnet = MultiLayerNetwork(
    load_from_library=True,
    library_path=os.path.join(input_folder, str(year)),
    use_polars=True  # Use polars for faster data loading if available
)
toc = time()
print(f"Network loaded in {toc-tic:.1f}s (N={popnet.N} nodes)")

# ==============================================================================
# STEP 4: SYMMETRIZE AND GROUP LAYERS
# ==============================================================================

print("\nSymmetrizing and grouping network layers...")
tic = time()

# Initialize empty sparse matrix for the new adjacency matrix
A = csr_matrix((popnet.N, popnet.N), dtype="uint8")

# Process each grouped layer
for layer, bin in layer_to_binary.items():
    print(f"\n  Processing layer: {layer}")
    
    # Extract edges for this layer using bitwise AND with the layer's binary encoding
    print("    - Filtering adjacency matrix...")
    temp = popnet.A.copy()
    temp.data = temp.data & bin  # Bitwise AND to isolate this layer's edges
    temp.eliminate_zeros()        # Remove zeros for memory efficiency
    
    # Symmetrize: combine both directions to create undirected edges
    # (A & bin)^T == A^T & bin, so the transpose of the filtered matrix gives the reverse direction
    # (temp + temp^T) > 0 creates a binary matrix where edge exists if present in either direction
    print("    - Creating symmetric (undirected) layer matrix...")
    temp = ((temp + temp.T) > 0).astype("uint8") * layer_to_new_binary[layer]
    
    # Add this layer to the cumulative adjacency matrix
    A += temp
    del temp
toc = time()

# Clean up memory
gc.collect()

print(f"\nSymmetrization complete in {toc-tic:.1f}s")
print(f"Total undirected edges in simplified network: {(A.nnz + A.diagonal().astype(bool).sum()) // 2:,}")

# ==============================================================================
# STEP 5: UPDATE NETWORK OBJECT AND SAVE
# ==============================================================================

# Build a new network object with the simplified, undirected adjacency matrix and the 5-layer table
# This preserves the node set and all node attributes, and lets mlnlib rebuild its internal layer lookups
popnet = MultiLayerNetwork(nodes=popnet.nodes, edges=A, layers=new_layers, codebook=popnet.codebook, use_polars=popnet.use_polars)

# Save the simplified network in MLN format
print(f"\nSaving simplified network to {output_year_path}...")
tic = time()
popnet.save(output_year_path, overwrite=True)
toc = time()

print(f"Network saved successfully in {toc-tic:.1f}s")
print(f"\n{'='*60}")
print(f"Processing complete for year {year}")
print(f"{'='*60}")