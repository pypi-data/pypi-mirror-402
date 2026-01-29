from . import Atom, Bond
from . import MolType as ClassMolType
from .object_magictools import ObjectMagicTools


class Molecule(ObjectMagicTools):
    """Class representing a single molecule.

    Attributes:
        MolType: Molecular Type of the molecule
        Name: Name of the molecule, either user-provided or generated from MolecularType name and molecule number
        Number: Serial number of the molecule within all molecules of the corresponding molecular type
        ID: Serial number of the molecule within all molecules of the system
        Atoms: List of atoms belonging to the molecule
        Bonds (also PairBonds and AngleBond): List of Bonds belonging to the Molecule

    Methods:
        AddAtom(atom): Add the atom to the molecule
        AddBond(bond): Add the bond to the molecule


    """

    def __init__(
        self,
        MolType,
        Name=None,
        Number=None,
        Atoms=None,
        Bonds=None,
        ID=None,
    ):
        super(Molecule, self).__init__()
        self._Name = Name
        assert isinstance(MolType, ClassMolType.MolType), (
            "Expecting object of class MolType"
        )
        self._MolType = MolType
        self._MolType.AddMolecule(self)
        self._number = Number
        self._ID = ID
        self._Atoms = Atoms if Atoms else []
        self._Bonds = Bonds if Bonds else []

    @property
    def Name(self):
        """Name of the molecule, either user-provided or generated from MolecularType name and molecule number."""
        if self._Name is not None:
            return self._Name
        return f"{self.MolType}:{self.Number}"

    @property
    def Number(self):
        """Serial number of the molecule within all molecules of the corresponding molecular type."""
        if self._number is not None:
            return self._number
        if self.MolType:
            return self.MolType.Molecules.index(self) + 1
        return None

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._number = value

    @property
    def ID(self):
        """Serial number of the molecule within all molecules of the system."""
        if self._ID is None:
            if self.MolType:
                if self.MolType.System:
                    self._ID = self.MolType.System.Molecules.index(self) + 1
        return self._ID

    @ID.setter
    def ID(self, value):
        assert isinstance(value, int)
        self._ID = value

    @property
    def PairBonds(self):
        """List of Pairwise Bonds belonging to the Molecule."""
        return [B for B in self.Bonds if isinstance(B, Bond.PairBond)]

    @property
    def AngleBonds(self):
        """List of Angle bending Bonds belonging to the Molecule."""
        return [B for B in self.Bonds if isinstance(B, Bond.AngleBond)]

    @property
    def MolType(self):
        """Molecular Type of the molecule."""
        return self._MolType

    @property
    def Atoms(self):
        """List of Atoms belonging to the molecule."""
        return self._Atoms

    def AddAtom(self, atom):
        """Add the atom to the molecule."""
        assert isinstance(atom, Atom.Atom)
        if atom not in self.Atoms:
            self._Atoms.append(atom)

    @property
    def Bonds(self):
        """List of Bonds belonging to the molecule."""
        return self._Bonds

    def AddBond(self, bond):
        """Add the bond to the molecule."""
        assert isinstance(bond, Bond.Bond)
        if bond not in self.Bonds:
            self._Bonds.append(bond)
            for atom in self.Atoms:
                atom._clear_cached()
