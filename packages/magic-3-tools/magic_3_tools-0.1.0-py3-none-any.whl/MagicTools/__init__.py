"""MagicTools - A library for molecular dynamics analysis and RDF calculations.

This package provides tools for:
- Radial Distribution Function (RDF) calculations
- Angular Distribution Function (ADF) calculations
- Molecular system analysis and manipulation
- Trajectory processing

Main classes:
    - System: Top-level object representing molecular systems
    - MolType: Molecular type definitions
    - Atom, AtomType: Atom representation and types
    - Bond, BondType: Bond representation and types
    - DF, DFset: Distribution functions and sets
    - Trajectory: Trajectory handling
    - RDFCalculator: Main calculator for RDF analysis

Main functions:
    - OnePlot: Plot distribution functions
    - MultPlot: Plot multiple distribution functions
    - ReadMagic: Read MagiC format files
"""

__version__ = "0.1.0"

# Import main classes
from .Atom import Atom
from .AtomType import AtomType
from .Bond import AngleBond, Bond, PairBond
from .BondType import AngleBondType, BondType, PairBondType
from .DF import DF
from .DFset import DFset

# Import main functions from MagicTools module
from .MagicTools import (
    MultPlot,
    OnePlot,
    PlotAllDFs,  # deprecated but kept for compatibility
)
from .Molecule import Molecule
from .MolType import MolType
from .MTException import (
    GeneralError,
    InputValueError,
)

# Import RDF calculator
from .rdf import RDFCalculator
from .System import System
from .Trajectory import Trajectory

__all__ = [
    # Version
    "__version__",
    # Main classes
    "Atom",
    "AtomType",
    "Bond",
    "AngleBond",
    "PairBond",
    "BondType",
    "AngleBondType",
    "PairBondType",
    "DF",
    "DFset",
    "MolType",
    "Molecule",
    "System",
    "Trajectory",
    # Exceptions
    "GeneralError",
    "InputValueError",
    # Functions
    "OnePlot",
    "MultPlot",
    "PlotAllDFs",
    # Calculator
    "RDFCalculator",
]
