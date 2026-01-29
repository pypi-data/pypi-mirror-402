from . import Bond
from .object_magictools import ObjectMagicTools


class BondType(ObjectMagicTools):
    """Class representing a Bond Type.

    The BondType is a group of bonds (pairwise or angle-bending), which are belonging to the same molecular type and
    described by the same interactions potential

    Attributes:
        MolType: Molecular Type the BondType belongs to
        Name: Bond Type name for text representation
        ID: Serial number of the Bond Type within all BondTypes of the System
        Number: Serial number of the BondType within all BondTypes of the MolecularType
        Bonds: List of Bonds belonging to this BondType
        AtomGroups: List of atom groups (duplets/triplets), each group represents one bond of the BondType

    Methods:
        AddBond(bond): Add bond to the BondType
        Write2MCM(stream): Write the bond type to the output-stream in mcm-file format.
        WriteAsRDFinp(): Print the BondType as line for RDF.inp file. Useful when writing script generating RDF.inp

    """

    def __init__(
        self,
        MolType,
        ID=None,
        Number=None,
        AtomGroups=None,
        Bonds=None,
        Name=None,
        Comment=None,
        BType=Bond.Bond,
    ):
        super(BondType, self).__init__()
        self._ID = ID
        self._number = Number
        self._MolType = MolType
        self._Bonds = Bonds if Bonds else []
        self.Name = Name
        self._AtomGroups = AtomGroups
        self._comment = Comment if Comment else ""
        self._BondStyleLAMMPS_ = None  # Bond style for LAMMPS, can be either None (tabulated by default), harmonic or none
        self.MolType.BondTypes = self.MolType.BondTypes + [self]

        if not self.Name and self.MolType:
            self.Name = str(self)

        self.__init_bonds(BType)
        self._cached = dict.fromkeys(["AtomGroups"])

    def __init_bonds(self, BType=Bond.Bond):
        if not self._Bonds and self._AtomGroups:  # Create bonds by AtomGroups
            self._Bonds = [
                BType(BondType=self, Atoms=AG, Molecule=self.MolType._dummy_molecule)
                for AG in self.AtomGroups
            ]

    def __str__(self):
        """Return string in format MolType:BondNumber."""
        return f"{self.MolType.Name}:{self.Number}"

    def _delete(self):
        print(f"Deleting bond type: {self.Name}")
        for molecule_ in self.MolType.Molecules:
            for bond_ in self.Bonds:
                molecule_.Bonds.remove(bond_)
            for atom in molecule_.Atoms:
                atom._clear_cached()

        self.MolType.BondTypes = [bt_ for bt_ in self.MolType.BondTypes if bt_ != self]
        del self._Bonds
        self._clear_cached()

    def WriteAsRDFinp(self):
        """Print the BondType as line for RDF.inp file. Usefull when writing script generating RDF.inp file."""
        str_atom_groups = ", ".join(
            [" ".join([str(a_) for a_ in grp_]) for grp_ in self.AtomGroups],
        )
        return f"add: {self!s}: {str_atom_groups}"

    @property
    def AtomGroups(self):
        """List of atom groups (duplets/triplets), each group represents one bond of the BondType."""
        if self._AtomGroups is not None:
            return self._AtomGroups
        if self._cached["AtomGroups"] is None:
            self._cached["AtomGroups"] = [bond.Atoms for bond in self.Bonds]
        return self._cached["AtomGroups"]

    @AtomGroups.setter
    def AtomGroups(self, value):
        self._AtomGroups = value

    @property
    def MolType(self):
        """Molecular Type the BondType belongs to."""
        return self._MolType

    @property
    def Bonds(self):
        """List of Bonds belonging to this BondType."""
        return self._Bonds

    def AddBond(self, bond):
        """Add bond to the BondType."""
        assert isinstance(bond, Bond.Bond)
        assert bond.BondType == self, "The bond does not have same bondtype as this one"
        if bond not in self.Bonds:
            self._Bonds.append(bond)
            self._clear_cached()

    @property
    def Number(self):
        """Serial number of the BondType within all BondTypes of the MolecularType."""
        if self._number is not None:
            return self._number
        if self.MolType:
            return self.MolType.BondTypes.index(self) + 1
        return None

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._number = value

    @property
    def ID(self):
        """Serial number of the Bond Type within all BondTypes of the System."""
        if self._ID is not None:
            return self._ID
        if self.MolType:
            if self.MolType.System:
                if self.MolType.System.BondTypes:
                    return self.MolType.System.BondTypes.index(self) + 1
        return None

    @ID.setter
    def ID(self, value):
        assert isinstance(value, int)
        self._ID = value

    def __trunc__(self):
        return self.Number

    @property
    def PairBonds(self):
        return [bond for bond in self.Bonds if isinstance(bond, Bond.PairBond)]

    @property
    def AngleBonds(self):
        return [bond for bond in self.Bonds if isinstance(bond, Bond.AngleBond)]

    def Write2MCM(self, stream):
        """Write the bond type to the mcm-stream."""
        stream.write(f"{len(self.AtomGroups)}\n")
        for atom_group in self.AtomGroups:
            # stream.write('{0[0]:d} {0[1]:d}\n'.format([atom.Number for atom in atom_group]))
            stream.write(" ".join([str(atom_.Number) for atom_ in atom_group]) + "\n")


class PairBondType(BondType):
    __doc__ = BondType.__doc__

    def __init__(
        self,
        MolType,
        ID=None,
        Number=None,
        AtomGroups=None,
        Bonds=None,
        Name=None,
        Comment=None,
    ):
        super(PairBondType, self).__init__(
            MolType,
            ID=ID,
            Number=Number,
            AtomGroups=AtomGroups,
            Bonds=Bonds,
            Name=Name,
            Comment=Comment,
            BType=Bond.PairBond,
        )

    # def Write2MCM(self, stream):
    #     stream.write('{0}\n'.format(len(self.AtomGroups)))
    #     for atom_group in self.AtomGroups:
    #         stream.write('{0[0]:d} {0[1]:d}\n'.format([atom.Number for atom in atom_group]))


# TODO: Can we merge these two methods?


class AngleBondType(BondType):
    __doc__ = BondType.__doc__

    def __init__(
        self,
        MolType,
        ID=None,
        Number=None,
        AtomGroups=None,
        Bonds=None,
        Name=None,
        Comment=None,
    ):
        super(AngleBondType, self).__init__(
            MolType,
            ID=ID,
            Number=Number,
            AtomGroups=AtomGroups,
            Bonds=Bonds,
            Name=Name,
            Comment=Comment,
            BType=Bond.AngleBond,
        )

    # def Write2MCM(self, stream):
    #     stream.write('{0}\n'.format(len(self.AtomGroups)))
    #     for atom_group in self.AtomGroups:
    #         stream.write('{0[0]:d} {0[1]:d} {0[2]:d}\n'.format([atom.Number for atom in atom_group]))
