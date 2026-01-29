import numpy as np

from . import AtomType as ClassAtomType
from . import Bond
from . import Molecule as ClassMolecule
from .object_magictools import ObjectMagicTools


class Atom(ObjectMagicTools):
    """Class representing a single atom.

    Attributes:
        AtomType(AtomType): Type of the atom
        Molecule (Molecule): The molecule where the atoms belongs to
        Name(str): Name of the atom
        Number(int): Atom's serial number within all atoms of the molecule
        ID(int): Atom's serial number within all atoms of the system
        Charge (float): Charge of the atom in electron charges
        Mass (float): Mass of the atom in a.u.
        R (np.ndarray): Coordinates of the atom (A)
        Bonds : List of bonds (Pairwise and angle) where the atom is involved
        BondedAtoms: (also PairBondedAtoms, AngleBondedAtoms) List of atoms bonded to this one.  Both angle- and pairwise bonds are taken into account

    Methods:
        IsBonded(that_atom): Check if that atom is bonded to this one
        Distance(that_atom): Calculate Euclidian Distance from that atom to this one
        PBC(): Apply periodic boundary conditions to the atom's coordinates (inplace!)
        Write2MCM(stream): Write atom to the mcmfile-stream

    """

    def __init__(
        self,
        Name,
        Molecule,
        R,
        Mass=None,
        Charge=None,
        ID=None,
        Number=None,
        AtomType=None,
    ):
        """Create an Atom.

        Args:
            Name (str): Name of the atom
            Molecule (Molecule): The molecule where the atoms belongs to
            R (np.array): Coordinates of the atom (A)

        """
        # Atom properties
        super().__init__()
        self.Name = Name
        self._R = np.array(R, dtype=float)
        self._AtomType = AtomType
        assert AtomType is None or isinstance(AtomType, ClassAtomType.AtomType), (
            "Expecting AtomType-object, or None"
        )

        # Set Charge and Mass and check that they are set successfully
        if Charge is not None:
            assert np.isreal(Charge)
            self._Charge = Charge
        elif self.AtomType is not None:
            self._Charge = self.AtomType.Charge

        if Mass is not None:
            assert np.isreal(Mass)
            self._Mass = Mass
        elif self.AtomType is not None:
            self._Mass = self.AtomType.Mass

        assert self.Mass is not None, "Atom's mass was not set"
        assert self.Charge is not None, "Atom's charge was not set"

        # Atom Type management
        if self.AtomType is not None:
            self.AtomType.AddAtom(self)

        # Molecule management
        assert isinstance(Molecule, ClassMolecule.Molecule)
        self._Molecule = Molecule
        if self.Molecule.Atoms is not None:
            self.Molecule.AddAtom(self)  # Add atom to the molecule

        # if everything went well, assign ID to the atom and update counters
        self._ID = ID
        self._Number = Number
        self._cached = dict.fromkeys(
            ["Bonds", "BondedAtoms", "AngleBondedAtoms", "PairBondedAtoms"],
        )

    @property
    def AtomType(self):
        """Type of the atom."""
        return self._AtomType

    @AtomType.setter
    def AtomType(self, atomtype):
        assert isinstance(atomtype, ClassAtomType.AtomType), (
            "Expected object of class AtomType"
        )
        self._AtomType = atomtype

    @property
    def R(self):
        """Coordinates of the atom: np.array(3): X,Y,Z."""
        return self._R

    @R.setter
    def R(self, r):
        assert len(r) == 3
        assert all([np.isreal(x) for x in r])
        self._R = r

    @property
    def Mass(self):
        """Atom's Mass."""
        return self._Mass

    @Mass.setter
    def Mass(self, value):
        assert np.isreal(value)
        self._Mass = value

    @property
    def Charge(self):
        """Atom's Charge, e."""
        return self._Charge

    @Charge.setter
    def Charge(self, value):
        assert np.isreal(value)
        self._Charge = value

    @property
    def Molecule(self):
        """Molecule this atom belongs to."""
        return self._Molecule

    @property
    def Number(self):
        """Atom's serial number within all atoms of the Molecule."""
        if self._Number is None:
            self._Number = self.Molecule.Atoms.index(self) + 1
        return self._Number

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._Number = value

    @property
    def ID(self):
        """Atom's serial number within all atoms of the system."""
        if self._ID is None and self.Molecule.MolType and self.Molecule.MolType.System:
            self._ID = self.Molecule.MolType.System.Atoms.index(self) + 1
        return self._ID

    @ID.setter
    def ID(self, value):
        assert isinstance(value, int)
        self._ID = value

    def __trunc__(self):
        return self.Number

    @property
    def Bonds(self):
        """List of bonds (Pairwise and angle) where the atom is involved."""
        # return the
        if self._cached["Bonds"] is None:
            self._cached["Bonds"] = [
                bond for bond in self.Molecule.Bonds if self in bond.Atoms
            ]
        return self._cached["Bonds"]

    @property
    def BondedAtoms(self):
        """List of atoms bonded to this one. Both angle- and pairwise bonds are taken into account."""
        if self._cached["BondedAtoms"] is None:
            self._cached["BondedAtoms"] = set(
                [a for bond in self.Bonds for a in bond.Atoms],
            )
            self._cached["BondedAtoms"].remove(self)
        return self._cached["BondedAtoms"]

    @property
    def PairBondedAtoms(self):
        """List of atoms bonded to this one. Only pairwise bonds are taken into account."""
        if self._cached["PairBondedAtoms"] is None:
            self._cached["PairBondedAtoms"] = set(
                [
                    a
                    for bond in self.Bonds
                    if isinstance(bond, Bond.PairBond)
                    for a in bond.Atoms
                ],
            )
            self._cached["PairBondedAtoms"].remove(self)
        return self._cached["PairBondedAtoms"]

    @property
    def AngleBondedAtoms(self):
        """List of atoms bonded to this one. Only angle bonds are taken into account."""
        if self._cached["AngleBondedAtoms"] is None:
            self._cached["AngleBondedAtoms"] = set(
                [
                    a
                    for bond in self.Bonds
                    if isinstance(bond, Bond.AngleBond)
                    for a in bond.Atoms
                ],
            )
            self._cached["AngleBondedAtoms"].remove(self)
        return self._cached["AngleBondedAtoms"]

    def IsBonded(self, that, kind=None):
        """Check if that atom is bonded to the given one.

        kind (optional):
        Args:
            that (Atom):
            kind (str): 'angle' or 'pair', can specify type of the bond. Default:any bond (pairwise or angle)

        Returns:
            bool: True if bonded, False if not bonded

        """
        if kind == "angle":
            return that in self.AngleBondedAtoms
        if kind == "pair":
            return that in self.PairBondedAtoms
        return that in self.BondedAtoms

    def Distance(self, that):
        """Calculate Euclidian Distance from that atom to the given one.

        Args:
            that (Atom):

        Returns:
            float: Distance

        """
        return np.linalg.norm(self.R - that.R)

    def Write2MCM(self, stream):
        """Write atom to the mcmfile-stream: Name X Y Z M Q idAType NameAType."""
        template = "{name} {x[0]} {x[1]} {x[2]} {M} {Q} {idAType} {NameAType}\n"
        if self.AtomType is not None:
            stream.write(
                template.format(
                    name=self.Name,
                    x=self.R,
                    M=self.Mass,
                    Q=self.Charge,
                    idAType=self.AtomType.Number,
                    NameAType=self.AtomType.Name,
                ),
            )

    def CopyAtom(self, Molecule=None, ID=None, Number=None):
        """Make a new atom which is copy of the given atom and assign it to the provided molecule.

        Args:
            Molecule (Molecule.Molecule): Molecule to assign the new atom
            ID (int): ID of the new atom
            Number (int): Number of the new atom

        Returns:
            Atom: New atom

        """
        return Atom(
            Name=self.Name,
            R=self.R,
            Mass=self.Mass,
            Charge=self.Charge,
            ID=ID,
            Number=Number,
            AtomType=self.AtomType,
            Molecule=Molecule,
        )

    def PBC(self, box):
        """Apply periodic boundary conditions to the atom's coordinates (inplace!).

        Args:
            box (array): periodic box: [Lx, Ly,Lz] in same units as atom coordinates (in most cases A)

        """
        import numpy as np

        self._R = np.mod(self._R, np.array(box))
