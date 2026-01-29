# MagicTools

A Python library for molecular dynamics analysis and Radial Distribution Function (RDF) calculations.

## Description

MagicTools provides a comprehensive set of tools for analyzing molecular dynamics simulations, with a focus on:

- **Radial Distribution Functions (RDF)**: Calculate and analyze pair distribution functions
- **Angular Distribution Functions (ADF)**: Analyze angular correlations
- **Molecular System Manipulation**: Build and modify molecular systems
- **Trajectory Processing**: Read and process molecular dynamics trajectories
- **Visualization**: Plot distribution functions with customizable settings

## Installation

### From PyPI

```bash
pip install magictools
```

### From source

```bash
git clone https://github.com/mposysoev/MagicTools.git
cd magictools
pip install -e .
```

## Requirements

- Python >= 3.10
- numpy >= 1.20.0
- pandas >= 1.3.0
- matplotlib >= 3.3.0

### Optional dependencies

For trajectory reading support:
```bash
pip install magictools[trajectory]
```

## Quick Start

### Using as a Library

```python
import magictools as mt

# Create a system
system = mt.System()

# Load data and calculate RDF
# ... your code here ...

# Plot results
mt.OnePlot(rdf_data, title="My RDF Analysis")
```

### Using the Command-Line Tool

The package provides a `magic-rdf` command-line tool for RDF calculations:

```bash
magic-rdf -i input.inp
```

#### Command-line options:

- `-i <file>`: Input file (default: rdf.inp)
- `-np <n>`: Run in parallel using n cores
- `--force`: Skip trajectory checks
- `--opt_memory_use`: Enable memory optimization for large systems
- `--notrim`: Disable automatic trimming

#### Example:

```bash
# Run RDF calculation with custom input file
magic-rdf -i my_system.inp

# Run in parallel on 4 cores
magic-rdf -i my_system.inp -np 4

# Run with memory optimization
magic-rdf -i large_system.inp --opt_memory_use
```

## Input File Format

The `magic-rdf` tool uses MagiC-2 RDF input format. See documentation for detailed format specification.

Example input file:
```
&PARAMETERS
TRAJECTORY = trajectory.xyz
FORMAT = XYZ
...
&ENDPARAMETERS
```

## Main Classes

- **`System`**: Top-level object representing the entire molecular system
- **`MolType`**: Molecular type definitions and topology
- **`Atom`, `AtomType`**: Atom representations and atom type definitions
- **`Bond`, `BondType`**: Bond representations and bond type definitions
- **`DF`, `DFset`**: Distribution functions and sets of distribution functions
- **`Trajectory`**: Trajectory file handling and processing
- **`RDFCalculator`**: Main calculator for RDF analysis

## Main Functions

- **`OnePlot()`**: Plot distribution functions on a single plot
- **`MultPlot()`**: Create multiple plots for distribution function analysis
- **`ReadMagic()`**: Read MagiC format files

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).
See the [LICENSE](LICENSE) file for details.

## Citation

If you use MagicTools in your research, please cite:

```
TODO: Add citation information
```

## Contact

- **Author**: Alexander Lyubartsev
- **Email**: alexander.lyubartsev@su.se
- **GitHub**: https://github.com/mposysoev/MagicTools
