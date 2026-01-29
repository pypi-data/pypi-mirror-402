from . import Atom, AtomType, Bond, BondType, Molecule
from . import MTException as MTE
from .object_magictools import ObjectMagicTools


class MolType(ObjectMagicTools):  # TODO: Init from tpr-dump file
    """Class representing topology of a single molecular type.

    Attributes:
        Name (str): The molecular type name
        System (:obj:`MagicTools.System`): The system which the Molecular Type belongs to
        Molecules (:obj:`list` of :obj:`MagicType.Molecule`): Molecules of the Molecular Type
        BondTypes (also PairBondTypes and AngleBondTypes): List of BondTypes belonging to the Molecular Type
        Bonds (also PairBonds and AngleBond): List of Bonds belonging to the Molecular Type
        Atoms: List of atoms belonging to molecules of the molecular type

    Methods:
        AddMolecule: Add molecule to the MolType
        Write2MCM: Write the molecular file to a mcm-file

    """

    def __init__(
        self,
        Name,
        System,
        Number=None,
        Molecules=None,
        BondTypes=None,
        quiet=False,
    ):
        """Create a molecular type instance with given name and assigns it to the system.

        If a mcm-file with name "Name.mcm" is found, the molecular type topology will be read from it,
        otherwise an stub molecular type will be created.
        When the molecular type is read from file, it automatically gets one corresponding molecule assigned.

        Args:
            Name: Name of the molecular type
            System: The system, where the molecular type belongs
            Molecules: (opt) List of molecules, which will be added to the molecular type once it is created.
            BondTypes: (opt) List of bond types, which will be added to the molecular type once it is created.
            quiet: opt() Suppress output
            Number: (opt) Number of the molecular type

        Examples::
            moltype_DNA = MagicTools.MolType("DNA.CG", system)  # Read molecular type from file
            moltype_stub = MagicTools.MolType("stub", system)  # Create a stub

        """
        super(MolType, self).__init__()
        # File type not stated - detect from the name
        try:
            if "." in Name:
                type_ = Name.strip().split(".")[-1]
                Name = ".".join(Name.strip().split(".")[0:-1])
            else:
                type_ = "dummy"
        except:
            print(
                "Can not detect the type of input file for MolType construction. \nWill use a stub.",
            )
            type_ = "dummy"
        self._filetype = type_  # Type of the file describing moltype
        self.Name = Name  # Name of the type
        self._number = Number
        self._Molecules = Molecules if Molecules else []
        self._BondTypes = BondTypes if BondTypes else []
        self._System = System
        # Create a dummy molecule: instance of molecule which represents the molecular type
        self._dummy_molecule = Molecule.Molecule(MolType=self)

        if self._filetype == "mmol":
            filename = f"./{self.Name}.mmol"
            self._read_moltype_from_mmol_file(filename, quiet=quiet)
        elif self._filetype == "mcm":
            filename = f"./{self.Name}.mcm"
            self.__read_moltype_from_mcm_file(filename, quiet=quiet)
        elif self._filetype == "dummy":
            # Create a dummy Molecular Type, which will be manually constructed
            pass
        else:
            print(f"Unknown type of the file: {self._filetype} \nWill create a stub.")

        self.System.AddMolType(self)

    @property
    def System(self):
        return self._System

    @property
    def Molecules(self):
        """List of molecules having this molecular type."""
        return self._Molecules

    def AddMolecule(self, molecule):
        """Add molecule to the MolType."""
        assert isinstance(molecule, Molecule.Molecule), (
            "Expecting object of class Molecule"
        )
        if molecule not in self._Molecules:
            if molecule.MolType is None:
                molecule._MolType = self
            assert molecule.MolType == self, (
                f"Molecular type of the molecule ({molecule.MolType.Name}) is different from this molecular type ({self.Name})"
            )
            self._Molecules.append(molecule)
            # call back to System, to clear cache
            self.System._clear_cached()

    @property
    def BondTypes(self):
        """List of Bond Types (pair and angle) belonging to the Molecular Type."""
        return self._BondTypes

    @BondTypes.setter
    def BondTypes(self, values):
        assert isinstance(values, list), "Expecting a list"
        assert all([isinstance(v, BondType.BondType) for v in values]), (
            "Expecting list of BondType objects"
        )
        for v in values:
            if v.MolType is None:
                v.MolType = self
            assert v.MolType == self, (
                f"Molecular type of the BondType ({v.MolType.Name}) is different from this molecular type ({self.Name})"
            )
        self._BondTypes = values
        self._clear_cached()

    @property
    def Number(self):
        # TODO: Check if we actually need it
        if self._number:
            return self._number
        if self.System:
            return self.System.MolTypes.index(self) + 1
        return None

    @Number.setter
    def Number(self, value):
        assert isinstance(value, int)
        self._number = value

    @property
    def Atoms(self):
        """Return list of atoms representing the molecular type (single molecule)."""
        return self._dummy_molecule.Atoms

    @property
    def NAtoms(self):
        return len(self.Atoms)

    def _read_moltype_from_mmol_file(self, filename, quiet=False):
        from MagicTools import _read_and_clean_lines

        if not quiet:
            print(f"Reading Molecular type from mmol-file: {filename}")
        lines = _read_and_clean_lines(filename)

        try:
            natoms = int(lines[0].strip())
        except:
            raise MTE.MolTypeError(
                f"Unable to read number of atoms in file:{filename} got: {lines[0].strip()}",
            )
        lines.pop(0)  # drop the first line
        try:
            for line in lines[0:natoms]:
                lineatom = line.split()
                name = lineatom[0].strip()
                x, y, z, mass, charge = [float(l_) for l_ in lineatom[1:6]]
                Atom.Atom(
                    Name=name,
                    R=(x, y, z),
                    Mass=mass,
                    Charge=charge,
                    Molecule=self._dummy_molecule,
                )
                print(
                    f"Atom added: ;{name:s}; {x:5.3f} {y:5.3f} {z:5.3f} {mass:5.2f} {charge:5.3f}",
                )
            print("\n")
        except:
            raise MTE.MolTypeError(
                f"Unable to read atom records in file: {filename} line:{line}\n",
            )

    def __read_atomtypes_from_mcm_lines(self, lines):
        # Detect AtomTypes in the file, check if they already exist, if not initialize them.
        try:
            atomtypes = set([(int(line.split()[6]), line.split()[7]) for line in lines])
            # print(atomtypes)
            atom_type_names = set([at[1] for at in atomtypes])
            atom_type_IDs = set([at[0] for at in atomtypes])

            if (
                len(atom_type_names) != len(atomtypes)
                or len(atom_type_IDs) != len(atomtypes)
                or len(atom_type_IDs) != len(atom_type_names)
            ):
                raise MTE.MolTypeError(
                    f"Inconsistent atom type names and IDs:\n{atomtypes}",
                )

            atomtypes = sorted(list(atomtypes), key=lambda x: x[0])
            for atom_type_ID, atomtype in atomtypes:
                if atomtype not in self.System.AtomTypesDict.keys():
                    # Check for other types with the same number
                    filter = [
                        AT.Name
                        for AT in self.System.AtomTypesDict.values()
                        if atom_type_ID == AT.Number
                    ]
                    if filter != []:
                        raise MTE.MolTypeError(
                            f"More than one atom type:{filter} has the same number {atom_type_ID}.\nCheck your mcm-files. ",
                        )
                    AtomType.AtomType(atomtype, System=self.System, Number=atom_type_ID)
        except MTE.MCMError:
            raise MTE.MolTypeError("Error while reading atomtypes")

    def __read_moltype_from_mcm_file(self, filename, quiet=False):
        from MagicTools import _read_and_clean_lines

        def __read_bond_type(moltype, iBond, lines, order, Type):
            try:
                n_atomgroups = int(lines[0])
                atomgroups = [
                    [int(line_.split()[o]) for o in order]
                    for line_ in lines[1 : n_atomgroups + 1]
                ]

            except MTE.MolTypeError:
                raise MTE.MolTypeError(
                    f"Error in mcm-file {filename}. Can not read definition of BondType {iBond + 1}.",
                )
            if len(atomgroups) != n_atomgroups:
                raise MTE.MolTypeError(
                    f"Error in mcm-file {filename}. BondType {iBond + 1}. Number of atom groups stated for the bondtype {n_atomgroups},"
                    f" differs from the actual number of provided groups {atomgroups}",
                )

            return Type(
                ID=len(self.BondTypes),
                Number=len(self.BondTypes) + 1,
                AtomGroups=[
                    [self.Atoms[i - 1] for i in atomgroup] for atomgroup in atomgroups
                ],
                MolType=moltype,
            )

        if not quiet:
            print(f"Reading Molecular type from mcm-file: {filename}")
        lines = _read_and_clean_lines(filename)

        # Read the atom-list part of the mcmfile
        try:
            natoms = int(lines[0])
        except:
            raise MTE.MolTypeError(
                f"Unable to read number of atoms in file:{filename} got: {lines[0].strip()}",
            )

        self.__read_atomtypes_from_mcm_lines(lines[1 : natoms + 1])

        try:
            for line in lines[1 : natoms + 1]:
                atom_name = line.split()[0]
                atom_coord = [float(k) for k in line.split()[1:4]]
                atom_mass = float(line.split()[4])
                atom_charge = float(line.split()[5])
                atom_type_name = line.split()[7]

                Atom.Atom(
                    Name=atom_name,
                    R=atom_coord,
                    Mass=atom_mass,
                    Charge=atom_charge,
                    AtomType=self.System.AtomTypesDict[atom_type_name],
                    Molecule=self._dummy_molecule,
                )
        except MTE.MolTypeError:
            raise MTE.MolTypeError(
                f"Unable to read atom records in file: {filename} \nline:{line}\n",
            )

        # Read pairwise-bonds
        nbonds = int(lines[natoms + 1])
        i_line = natoms + 1
        self._BondTypes = []
        i_line += 1
        for iBond in range(nbonds):
            bond_type = __read_bond_type(
                self,
                iBond,
                lines[i_line:],
                order=[0, 1],
                Type=BondType.PairBondType,
            )
            i_line += len(bond_type.AtomGroups) + 1

        # Read angle-bending bonds
        # Check the order in atom-triplets
        if "Order=1-2-3" in lines[i_line]:
            flag_new_order = True
            lines[i_line] = lines[i_line].replace("Order=1-2-3", "")
        else:
            flag_new_order = False
        nangles = int(lines[i_line])
        i_line += 1
        for iBond in range(nbonds, nbonds + nangles):
            bond_type = __read_bond_type(
                self,
                iBond,
                lines[i_line:],
                [0, 1, 2] if flag_new_order else [0, 2, 1],
                Type=BondType.AngleBondType,
            )
            i_line += len(bond_type.AtomGroups) + 1

    @property
    def PairBondTypes(self):
        return [
            bond for bond in self.BondTypes if isinstance(bond, BondType.PairBondType)
        ]

    @property
    def AngleBondTypes(self):
        return [
            bond for bond in self.BondTypes if isinstance(bond, BondType.AngleBondType)
        ]

    @property
    def Bonds(self):
        """List of Bonds (pair and angle) belonging to molecules of the Molecular Type."""
        return [bond for bond_type in self.BondTypes for bond in bond_type.Bonds]

    @property
    def PairBonds(self):
        return [B for B in self.Bonds if isinstance(B, Bond.PairBond)]

    @property
    def AngleBonds(self):
        return [B for B in self.Bonds if isinstance(B, Bond.AngleBond)]

    def MakeMolecule(self, Name=None, Number=None):
        """Create new molecule of the molecular type and add it to the list of molecules.

        Args:
            Name: (opt) Name of the new molecule
            Number: (opt) Number of the new molecule

        """
        new_molecule = Molecule.Molecule(Name=Name, MolType=self, Number=Number)
        for atom in self._dummy_molecule.Atoms:
            atom.CopyAtom(Molecule=new_molecule)

        for bond in self._dummy_molecule.Bonds:
            atom_indexes = [
                self._dummy_molecule.Atoms.index(atom) for atom in bond.Atoms
            ]
            atoms = [new_molecule.Atoms[i] for i in atom_indexes]
            obj = bond.__class__
            obj(Molecule=new_molecule, BondType=bond.BondType, Atoms=atoms)
        return new_molecule

    def Write2MCM(self, ofilename=None):
        """Write the molecular file to a mcm-file.

        Args:
            ofilename: Name of the file. If not given, name of the molecular type will be used

        """
        if ofilename is None:
            ofilename = self.Name + ".mcm"
        with open(ofilename, "w") as ofile:
            ofile.write(f"{len(self._dummy_molecule.Atoms)}\n#\n")

            # Writing atoms description line by line
            for atom in self.Atoms:
                atom.Write2MCM(ofile)
            # Writing pairwise bonds
            ofile.write(f"{len(self.PairBondTypes)}\n")
            for b in self.PairBondTypes:
                b.Write2MCM(ofile)
            # Writing Angle-Bonds
            ofile.write(f"{len(self.AngleBondTypes)}  Order=1-2-3 \n")
            for b in self.AngleBondTypes:
                b.Write2MCM(ofile)
