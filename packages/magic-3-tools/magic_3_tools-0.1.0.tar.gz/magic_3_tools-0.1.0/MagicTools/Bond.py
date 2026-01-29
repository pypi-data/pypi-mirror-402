from math import acos

from . import Atom
from .object_magictools import ObjectMagicTools


class Bond(ObjectMagicTools):
    """Class representing a single Bond connecting two or three atoms, depending on kind of the bond.

    Attributes:
        BondType: Bond Type of the Bond
        Molecule: Molecule the bond belongs to
        Name: Bond name for text representation
        ID: Serial number of the Bond Type within all BondTypes of the System
        Number: Serial number of the bond within all bonds in the system having the same kind (pairwise or angle-bending)
        Atoms: Pair or Triplet of atoms bonded by the bond
        Value: Distance or angle of the bond

    """

    def __init__(self, BondType, Atoms, Molecule=None, ID=None, Number=None):
        super().__init__()
        self._number = Number
        self._ID = ID

        assert all([a_.Molecule == Atoms[0].Molecule for a_ in Atoms]), (
            "Provided atoms are from different molecules"
        )
        if Molecule is None:
            Molecule = Atoms[0].Molecule
        assert Molecule == Atoms[0].Molecule, (
            f"Provided value Molecule {Molecule} is not consistent with the given atoms {Atoms[0].Molecule}"
        )
        self._Molecule = Molecule
        self._Atoms = Atoms  # pair or triplet of atoms involved in the bond
        self.Molecule.AddBond(self)
        self._BondType = BondType
        self.BondType.AddBond(self)

        # Add Bond to the list of Atom's bonds
        for atom in self.Atoms:
            assert isinstance(atom, Atom.Atom)
            if self not in atom.Bonds:
                atom.Bonds.append(self)

    @property
    def Name(self):
        return "{0}:{1}:{2}".format(
            self.BondType.Name,
            self.Number,
            "-".join([str(a_) for a_ in self.Atoms]),
        )

    @property
    def BondType(self):
        """Bond Type of the Bond."""
        return self._BondType

    @property
    def Molecule(self):
        """Molecule the bond belongs to."""
        return self._Molecule

    @property
    def Atoms(self):
        """Pair or Triplet of atoms bonded by this bond."""
        return self._Atoms

    @property
    def MolType(self):
        # print("Bond.MolType - is obsolete and will be removed. Use Bond.Molecule.MolType instead")
        return self.Molecule.MolType

    def getLength(self):
        print("Deprecated. Use Value() instead")
        return self.Value()

    @property
    def Number(self):
        """Serial number of the bond within all bonds in the system having the same kind (pairwise or angle-bending)."""
        if self._number:
            return self._number
        if self.BondType and self.BondType.MolType and self.BondType.MolType.System:
            return self.BondType.MolType.System.Bonds.index(self) + 1
        return None

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._number = value

    @property
    def ID(self):
        """Serial number of the bond within all bonds of the system."""
        if self._ID:
            return self._ID
        if self.BondType and self.BondType.MolType and self.BondType.MolType.System:
            return self.BondType.MolType.System.Bonds.index(self) + 1
        return None

    @ID.setter
    def ID(self, value):
        assert isinstance(value, int)
        self._ID = value


class PairBond(Bond):
    def __init__(self, BondType, Atoms, ID=None, Number=None, Molecule=None):
        assert len(Atoms) == 2, "Pair of atoms required"
        super(PairBond, self).__init__(
            BondType,
            Atoms,
            ID=ID,
            Number=Number,
            Molecule=Molecule,
        )

    @property
    def Number(self):
        """Serial number of the bond within all bonds in the system having the same kind (pairwise or angle-bending)."""
        if self._number:
            return self._number
        if self.BondType and self.BondType.MolType:
            if self.BondType.MolType.System and self.BondType.MolType.System.PairBonds:
                return self.BondType.MolType.System.PairBonds.index(self) + 1
        return None

    @property
    def Value(self):
        """Bond length of the given bond."""
        return self.Atoms[0].Distance(self.Atoms[1])


class AngleBond(Bond):
    def __init__(self, BondType, Atoms, ID=None, Number=None, Molecule=None):
        assert len(Atoms) == 3, "Triplet of atoms required"
        super(AngleBond, self).__init__(
            BondType,
            Atoms,
            ID=ID,
            Number=Number,
            Molecule=Molecule,
        )

    @property
    def Number(self):
        if self._number:
            return self._number
        if self.BondType:
            if self.BondType.MolType:
                if self.BondType.MolType.System:
                    if self.BondType.MolType.System.AngleBonds:
                        return self.BondType.MolType.System.AngleBonds.index(self) + 1
        return None

    @property
    def Value(self):
        """Angle of the given angle bond."""
        r12 = self.Atoms[0].Distance(self.Atoms[1])
        r13 = self.Atoms[0].Distance(self.Atoms[2])
        r23 = self.Atoms[1].Distance(self.Atoms[2])
        return acos((r12**2 + r23**2 - r13**2) / (2.0 * r12 * r23)) * 180 / 3.14159
