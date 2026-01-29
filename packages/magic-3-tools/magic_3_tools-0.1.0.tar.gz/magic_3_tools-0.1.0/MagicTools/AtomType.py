import numpy as np

from . import Atom
from .object_magictools import ObjectMagicTools


class AtomType(ObjectMagicTools):
    """Class representing an atom type.

    Attributes:
        System (:obj:`MagicTools.System`): The system which the Atom Type belongs to
        Number (int): Serial number of the atom type
        Atoms: List of Atoms belonging to this AtomType
        Charge(float): Charge of the atom-type as average over charges of all atoms of the type in a.u.
        Mass(float): Mass of the atom-type as average over masses of all atoms of the type in a.u.

    Methods:
        WriteAsRDFinp(): Return a string for RDF.inp file representing the AtomType
        AddAtom(atom): Add atom to the AtomType

    """

    def __init__(
        self,
        Name,
        System,
        Mass=None,
        ID=None,
        Number=None,
        Charge=None,
        Atoms=None,
    ):
        """Creates an AtomType. Name of the AtomType and reference of the parent System must be specified."""
        super().__init__()
        self.Name = Name
        self._Atoms = []
        if Atoms is not None:
            for atom_ in Atoms:
                self.AddAtom(atom_)
        self._System = System
        self._ID = ID
        self._number = Number if Number else None
        self._cached = dict.fromkeys(["Mass", "Charge"])
        self._cached["Mass"] = Mass
        self._cached["Charge"] = Charge

        self.System.AddAtomType(self)  # Update list of atom types for the system

    @property
    def System(self):
        """Reference to the system which the Atom Type belongs to."""
        return self._System

    @property
    def Number(self):
        """Serial number of the atom type."""
        if self._number is not None:
            return self._number
        if self.System:
            return self.System.AtomTypes.index(self) + 1
        return None

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._number = value

    @property
    def ID(self):
        # TODO: Check if this property can be removed, since it is nearly identical to self.Number
        if self._ID:
            return self._ID
        if self.System:
            return self.System.AtomTypes.index(self) + 1
        return None

    @ID.setter
    def ID(self, value):
        assert isinstance(value, int)
        self._ID = value

    @property
    def Mass(self):
        """Mass of the atom-type as average over masses of all atoms of the type in a.u."""
        if self.Atoms:
            self._cached["Mass"] = np.mean([atom.Mass for atom in self.Atoms])
        return self._cached["Mass"]

    @Mass.setter
    def Mass(self, value):
        assert isinstance(value, float)
        assert value >= 0, "Mass usually has non negative value"
        self._cached["Mass"] = value

    @property
    def Charge(self):
        """Charge of the atom-type as average over charges of all atoms of the type in a.u."""
        if self.Atoms:
            self._cached["Charge"] = np.mean([atom.Charge for atom in self.Atoms])
        return self._cached["Charge"]

    @Charge.setter
    def Charge(self, value):
        assert isinstance(value, float)
        self._cached["Charge"] = value

    @property
    def Atoms(self):
        """List of Atoms belonging to this AtomType."""
        return self._Atoms

    @property
    def Sites(self):
        """List of Sites belonging to this AtomType."""
        return [site for site in self.System.Sites if site.AtomType == self]

    def AddAtom(self, atom):
        """Add atom to the AtomType."""
        assert isinstance(atom, Atom.Atom), "Expecting an object of class Atom"
        self._Atoms.append(atom)
        atom.AtomType = self

    def WriteAsRDFinp(self):
        """Return a string for RDF.inp file representing the AtomType."""
        return "{0}:{1}".format(self.Name, " ".join([atom.Name for atom in self.Sites]))
