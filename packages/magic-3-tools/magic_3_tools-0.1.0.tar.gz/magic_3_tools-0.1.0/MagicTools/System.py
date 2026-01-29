from collections import OrderedDict, defaultdict

import numpy as np

from . import AtomType, Bond, BondType, DFset, MolType
from . import MTException as MTE
from .object_magictools import ObjectMagicTools


class System(ObjectMagicTools):
    """System - Top level object representing the whole molecular system.

    Properties:
       * MolTypes - Molecular types of the system
       * Molecules - Molecules belonging to the system
       * BondTypes - Bond types (both pairwise and angle-bending) belonging to the system
       * PairBondTypes - Pairwise bond types belonging to the system
       * AngleBondTypes - Angle-bending bond types belonging to the system
       * Bonds - Bonds (both pairwise and angle-bending) belonging to the system
       * PairBonds - Pairwise bonds belonging to the system
       * AngleBonds - Angle-bending bonds belonging to the system
       * AtomTypes - List of atom types defined in the system
       * Atoms - List of atoms belonging to the system
       * Sites - List of sites, i.e. atoms belonging to molecular types of the system

    Methods Overview:

    Construct and populate the system
        * AddMolType - Add molecular type to the system
        * AddAtomType - Add atom type to the system
        * ReadGeometry - Read system's geometry from XMOL file
        * SetExclusions - Set exclusion rules for the system
        * ImputeSameAsBond - Update BondTypes in the system according to the provided set of potentials/RDFs


    Write to files
        * WriteLAMMPSData - Write the system's topology to LAMMPS data file
        * WriteGromacsTopology - Write the system's topology to GROMACS-topology file topfile.top
        * WriteGALAMOSTxml - Write the system's topology to GALAMOST XML format and
                            write records for the tabulated potentials as GALAMOST python script
        * WriteGALAMOSTExclusions - Create a set of two exclusion files for GALAMOST
        * WriteMCMs - Save all molecular types of the system to corresponding MCM-files
        * WriteGeometryGRO - Write system's geometry as .gro file
        * WriteAsRDFinp - Print the system as lines for RDF.inp file. Useful when writing script generating RDF.inp file

    Search and resolve names to objects:
        * GetBondType - Find bond type by MolTypeName:BondNumber
        * GetAtomType - Find atom type by it's name
        * GetMolType - Find molecular type by it's name

        * IsSystemMatchRDFs - Check if current geometry of the system matches the given set of RDFs

    """

    def __init__(
        self,
        input=None,
        NMolMType=None,
        mcmfile=None,
        Box=None,
        dfset=None,
        geometry=None,
        **kwargs,
    ):
        """Create the System (top-level topology structure).

        System can be empty or created using MagiC.core input file, such as magic.inp, or
        user can specify exact list of molecular type names (mcmfile) and number of molecules of each type (NMolMType)
        and box size (Box)

        Args:
            input (str): MagiC.core input file, such as magic.inp
            mcmfile ([str, str]): List of molecular types in the system, corresponding mcm-files shall be in the same folder.
            NMolMType ([int, int]): Number of molecules of every molecular type, in same order as molecular types
            Box ([float, float, float]): Dimensions of the periodic box. [Lx, Ly, Lz]
            dfset (DFset): Optional. Set of potentials/RDFs with SameAs-records, if provided, in topology the SameAsBonds will be described by same bond-type.
            geometry (str): xmol-file with coordinates of system's atoms

        Examples ::
            system0 = System()  # empty system
            system1 = System(input="magic.inp")  # same system as specified in MagiC.Core input file
            system2 = System(mcmfile=["MT1.CG", "MT2.CG"], NMolMType=[10, 10], Box=[10.0, 10.0, 10.0])
            system3 = System(input="magic.inp", dfset="potentials.pot", geometry="start.xmol")

        """
        super(System, self).__init__()
        if NMolMType:
            print("NMolMtype provided")
            if isinstance(NMolMType, int):
                NMolMType = [NMolMType]
            assert isinstance(NMolMType, list) or isinstance(NMolMType, tuple)
            for N in NMolMType:
                assert isinstance(N, int)
            print(f"NMolMType:{NMolMType}")

        if mcmfile:
            if not (isinstance(mcmfile, type([])) or isinstance(mcmfile, type(()))):
                mcmfile = [mcmfile]
            for mcm in mcmfile:
                assert isinstance(mcm, str)
            mcmfile = [mcm.strip().replace(".mcm", "") for mcm in mcmfile]
            print(f"mcmfile:{mcmfile}")

        if input:  # automatically detect input to build the system
            try:  # Try to read the input file as magic input file
                print("Try to read the input file as magic input")
                (_mcmfile, n_mol_of_mol_type, _box) = self.__parseInputMagic(input)
                print(
                    f"MolTypes={_mcmfile}, _n_mol_mtype={n_mol_of_mol_type}, Box={_box}",
                )
                NMolMType = n_mol_of_mol_type if not NMolMType else NMolMType
                mcmfile = mcmfile if mcmfile else _mcmfile
                Box = Box if Box else _box
            except:
                print("it is not a magic input. Perhaps an mcm-file(s).")
                if not (isinstance(input, type([])) or isinstance(input, type(()))):
                    input = [input]
                mcmfile = mcmfile if mcmfile else [s.replace(".mcm", "") for s in input]
        self.__dfset = dfset
        self.Box = Box
        self._MolTypes = []
        self._AtomTypesDict = OrderedDict()
        self._BondTypes = None
        self.exclusions_EL = {"exclusions_A": None, "exclusions_B": None}
        self.exclusions_SR = {"exclusions_A": None, "exclusions_B": None}

        if mcmfile:  # if we have some input - construct the system
            if not NMolMType:
                NMolMType = [1] * len(mcmfile)
            assert len(NMolMType) == len(mcmfile), (
                "Error: Inconsistent length of MolType-list and Number of Molecules list"
            )
            # Read list of molecular types
            print("Reading Molecular Types from mcm-files")

            for str_mol_type in mcmfile:
                try:
                    # print(str_mol_type)
                    MolType.MolType(str_mol_type + ".mcm", System=self)
                except MTE.MCMError:
                    raise MTE.MCMError(
                        f"Error: Can not read Molecular Type {str_mol_type} from mcm file",
                    )

            # Creating molecules
            for n_mol, MT in zip(NMolMType, self.MolTypes):  # over MolTypes
                for iMol in range(1, n_mol):
                    # Add extra-molecules (beyond 1st, which is automatically created in MolType constructor
                    MT.MakeMolecule()
        self._cached = dict.fromkeys(
            ["Bonds", "Atoms", "Molecules", "AngleBonds", "PairBonds"],
        )
        if self.__dfset is not None:
            self.ImputeSameAsBondsFromPotential()
        # backwards compatibility with 'xmol'-parameter
        if ("xmol" in kwargs) and (geometry is None):
            geometry = kwargs["xmol"]
        if geometry is not None:
            self.ReadGeometry(geometry)

    @property
    def AtomTypes(self):
        """List all atom-types belonging to the system."""
        return list(self._AtomTypesDict.values())

    @property
    def Atoms(self):
        """List all atoms belonging to the system."""
        if self._cached["Atoms"] is None:
            self._cached["Atoms"] = [
                atom
                for MT in self.MolTypes
                for molecule in MT.Molecules
                for atom in molecule.Atoms
            ]
        return self._cached["Atoms"]

    @property
    def Sites(self):
        """List all sites belonging to the system."""
        # TODO: Correct the implementation. And test!
        return [
            atom for moltype_ in self.MolTypes for atom in moltype_.Molecules[0].Atoms
        ]

    @property
    def BondTypes(self):
        """List all bond types belonging to the system."""
        if self._BondTypes is None:
            return [
                bond_type
                for mol_type in self.MolTypes
                for bond_type in mol_type.BondTypes
            ]
        return self._BondTypes

    @property
    def PairBondTypes(self):
        """List all pairwise bond types belonging to the system."""
        return [
            bond_type
            for bond_type in self.BondTypes
            if isinstance(bond_type, BondType.PairBondType)
        ]

    @property
    def AngleBondTypes(self):
        """List all angle-bending bond types belonging to the system."""
        return [
            bond_type
            for bond_type in self.BondTypes
            if isinstance(bond_type, BondType.AngleBondType)
        ]

    @property
    def Bonds(self):
        """List all bonds (both angle and pairwise) belonging to the system."""
        if self._cached["Bonds"] is None:
            self._cached["Bonds"] = [
                bond for moltype in self.MolTypes for bond in moltype.Bonds
            ]
        return self._cached["Bonds"]

    @property
    def PairBonds(self):
        """List all pairwise bonds belonging to the system."""
        if self._cached["PairBonds"] is None:
            self._cached["PairBonds"] = [
                bond for bond in self.Bonds if isinstance(bond, Bond.PairBond)
            ]
        return self._cached["PairBonds"]

    @property
    def AngleBonds(self):
        """List all angle-bending bonds belonging to the system."""
        if self._cached["AngleBonds"] is None:
            self._cached["AngleBonds"] = [
                bond for bond in self.Bonds if isinstance(bond, Bond.AngleBond)
            ]
        return self._cached["AngleBonds"]

    @property
    def Molecules(self):
        """List all molecules belonging to the system."""
        if self._cached["Molecules"] is None:
            self._cached["Molecules"] = [
                molecule
                for mol_type in self.MolTypes
                for molecule in mol_type.Molecules
            ]
        return self._cached["Molecules"]

    @property
    def MolTypes(self):
        """List of all molecular types of the system."""
        return self._MolTypes

    def AddMolType(self, moltype):
        """Add Molecular type to the system.

        Args:
            moltype (MolType): The molecular type to add

        """
        assert isinstance(moltype, MolType.MolType), "Expecting object of class MolType"
        if moltype not in self._MolTypes:
            self._MolTypes.append(moltype)
            self._clear_cached()

    def __set_IDs_to_molecules(self):
        for i, mol in enumerate(self.Molecules):
            mol.ID = i + 1

    def __set_IDs_to_atoms(self):
        for i, atom in enumerate(self.Atoms):
            atom._ID = i + 1

    def ImputeSameAsBondsFromPotential(self, dfset=None):
        """Update BondTypes in the system according to the provided set of potentials/RDFs.

        Use before exporting topology to external MD format.
        By default the system is build from mcm-files, where no SameAs records are present.

        Args:
            dfset: Set of potentials/RDFs, having SameAs records.
            Default None, use potentials provided with the constructor

        """
        if dfset is None:
            dfset = self.__dfset
        assert (dfset is None) or isinstance(dfset, DFset.DFset), (
            "Expecting to get a DFset-object"
        )
        bondtypes = [bt_ for bt_ in self.BondTypes]
        self._BondTypes = []
        for bondtype in bondtypes:
            newbondtype = self._getSameBond(bondtype, dfset=dfset)
            if newbondtype == bondtype:
                self._BondTypes.append(bondtype)
            else:
                for bond in bondtype.Bonds:
                    bond._BondType = newbondtype

    def _getSameBond(self, bondtype, dfset=None):
        """Find corresponding SameAsBond for the given BondType. If nothing is found, return the original BondType.

        Args:
            bondtype (BondType): The provided BondType
            dfset (DFset): DFset with SameAsBond records, if not explicitly given, system.__dfset will be used

        Returns: (BondType)

        """
        newbondtype = bondtype
        if dfset is None:
            dfset = self.__dfset
        if dfset is not None:
            df = dfset.FindBondDF(bondtype.MolType.Name, bondtype.Number)
            if df is None:
                print("Can't find record for this bond:" + bondtype.Name)
            elif df.SameAsBond is not None:
                newbondtype = self.GetBondType(df.SameAsBond)
        return newbondtype

    def WriteLAMMPSData(self, outfile, hybrid=False, Box=None, sortnames=False):
        """Writes topology of the system to LAMMPS topology data file.

        Args:
            outfile (str):  Name of LAMMPS data file
            hybrid (bool):  If hybrid = True, (i.e. few bond types are used) it adds explicit bond-types to the topology file
            Box (): Periodic box. Can be set as (Lx, Ly, Lz) or as [(x_lo, x_hi), (y_lo, y_hi), (z_lo, z_hi)]
            sortnames (bool): Whether to put names of atom in alphabetical order when specifying interactions. False.

        """
        self._clear_cached()
        ofile = open(outfile, "w")
        outfile_inc = outfile + ".run.inc"
        ofile_inc = open(outfile_inc, "w")
        #        Generate header of LAMMPS.data file
        # write the header
        ofile.write("LAMMPS $NAME_OF_YOUR_SYSTEM\n")
        ofile.write("\n")
        ofile.write(
            f"{len(self.Atoms):d}  atoms\n{len(self.PairBonds):d}  bonds\n{len(self.AngleBonds):d}  angles\n{0:d}  dihedrals\n{0:d}  impropers\n\n",
        )

        ofile.write(
            f"{len(self.AtomTypes):d}  atom types\n"
            f"{len(self.PairBondTypes):d}  bond types\n"
            f"{len(self.AngleBondTypes):d}  angle types\n"
            f"{0:d}  dihedral types\n"
            f"{0:d}  improper types\n\n",
        )

        if not Box:
            Box = [[-0.5 * lbox, 0.5 * lbox] for lbox in self.Box]
        if isinstance(Box, float):
            Box = [Box] * 3
        if isinstance(Box, list):
            if len(Box) == 3:
                if isinstance(Box[0], float):
                    Box = [[-0.5 * lbox, 0.5 * lbox] for lbox in Box]
            else:
                raise ValueError("Periodic box size is missing or wrong!")
        else:
            raise ValueError("Periodic box size is missing or wrong!")

        ofile.write(f"{Box[0][0]:11.5f} {Box[0][1]:11.5f} xlo xhi\n")
        ofile.write(f"{Box[1][0]:11.5f} {Box[1][1]:11.5f} ylo yhi\n")
        ofile.write(f"{Box[2][0]:11.5f} {Box[2][1]:11.5f} zlo zhi\n")

        # Write Masses
        ofile.write("\n Masses\n\n")
        ofile.writelines(
            f"{iAType.Number:d} {iAType.Mass:9.5f}\n" for iAType in self.AtomTypes
        )

        # Write PairIJ-coeff - specify tabulated interactions:
        # will be written to a file incluided to LAMMPS input script
        ofile_inc.write("\n #PairIJ Coeffs\n\n")
        ofile_inc.write("pair_coeff * * coul/long\n")
        for iAT in self.AtomTypes:
            for jAT in [i for i in self.AtomTypes if i.Number >= iAT.Number]:
                atom_type_pair = (
                    tuple(sorted([iAT.Name, jAT.Name]))
                    if sortnames
                    else (iAT.Name, jAT.Name)
                )
                ofile_inc.write(
                    "pair_coeff {0:d} {1:d} table {2}_{3}.table {2}_{3}\n".format(
                        iAT.Number,
                        jAT.Number,
                        *atom_type_pair,
                    ),
                )
        # Write Atoms:
        ofile.write("\n Atoms\n\n")
        self.__set_IDs_to_molecules()
        self.__set_IDs_to_atoms()
        ofile.writelines(
            f"{iAtom.ID:d} {iAtom.Molecule.ID:d} {iAtom.AtomType.Number:d} {iAtom.Charge:11.5f} {iAtom.R[0]:11.5f} {iAtom.R[1]:11.5f} {iAtom.R[2]:11.5f}\n"
            for iAtom in self.Atoms
        )
        # Write Bonds:
        if len(self.PairBonds) > 0:
            ofile.write("\n Bonds\n\n")
        ofile.writelines(
            f"{bond.Number:d} {self.PairBondTypes.index(bond.BondType) + 1:d} {bond.Atoms[0].ID:d} {bond.Atoms[1].ID:d}\n"
            for bond in self.PairBonds
        )

        # Write Angles:
        if len(self.AngleBonds) > 0:
            ofile.write("\n Angles\n\n")
        ofile.writelines(
            f"{bond.Number:d} {self.AngleBondTypes.index(bond.BondType) + 1:d} {bond.Atoms[0].ID:d} {bond.Atoms[1].ID:d} {bond.Atoms[2].ID:d}\n"
            for bond in self.AngleBonds
        )

        def __write_bond_coeff_lammps(bond_types, bond_type_string):
            """Type=Angle or Bond."""
            ofile_inc.write(f"\n #{bond_type_string:s} Coeffs\n\n")
            for iBT, BT in enumerate(bond_types):
                line = f"{bond_type_string.lower()}_coeff "

                if BT._BondStyleLAMMPS_ == "zero":
                    line = line + "{0:d} {1}".format(
                        bond_types.index(BT) + 1,
                        "zero " if hybrid else "",
                    )
                elif BT._BondStyleLAMMPS_ == "harmonic":
                    if hasattr(BT, "_Kforce_"):  # if the bond type is harmonic
                        line = line + "{0:d} {1} {2:g} {3:g} ".format(
                            bond_types.index(BT) + 1,
                            "harmonic " if hybrid else "",
                            BT._Kforce_,
                            BT._Requil_,
                        )
                elif BT._BondStyleLAMMPS_ is None:  # if tabulated bond type
                    line = line + "{0:d} {1} {2:s}.table {2:s} ".format(
                        bond_types.index(BT) + 1,
                        "table " if hybrid else "",
                        BT.Name.replace(":", "."),
                    )
                if BT._comment:
                    line = line + "# " + BT._comment
                ofile_inc.write(line + "\n")

        # Write Angle Coeffs:
        __write_bond_coeff_lammps(self.AngleBondTypes, "Angle")
        # Write Bond Coeffs:
        __write_bond_coeff_lammps(self.PairBondTypes, "Bond")
        ofile.close()
        ofile_inc.close()
        print(
            "!!! Do not forget to adjust your LAMMPS input script: (LAMMPS.run.inp)\n"
            "You need to specify number of points in the tabulated potentials, Rcut for electrostatics.\n"
            " Refer to the lines below:\n"
            "1. pair_style hybrid/overlay table linear <Npoints> coul/long <Ecutel>\n"
            + "2. bond_style {0} table linear <Npoints>\n".format(
                "hybrid harmonic" if hybrid else "",
            )
            + "3. angle_style table linear <Npoints>\n"
            + f"4. read_data {outfile}\n"
            + f"5. include {outfile_inc}\n",
        )

    def WriteGALAMOSTxml(
        self,
        eps,
        outfile="topology.xml",
        Box=None,
        pyfile="tables.inc.py",
    ):
        """Writes the system's topology in GALAMOST XML format and records for the tabulated potentials as GALAMOST python script.

        Args:
            eps (float):  dielectric permittivity, required for charge conversion into GALAMOST internal units
            outfile (str):  file to write XML topology
            pyfile (str): file to write python commands
            Box ([float, float, float]): PBC box size for the system [Lx, Ly, Lz]

        """
        from math import sqrt

        self._clear_cached()
        header_ = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<galamost_xml version="1.3">\n'
        )
        footer_ = "</configuration>\n</galamost_xml>\n"

        with open(outfile, "w") as ofile:
            # write the XML header
            ofile.write(header_)
            # write number of atoms
            ofile.write(
                f'<configuration time_step="0" dimensions="3" natoms="{len(self.Atoms)}" >\n',
            )
            # write box dimensions
            if not Box:
                Box = self.Box
            Box = np.asarray(Box)
            ofile.write(
                f'<box lx="{(Box * 0.1)[0]:<.5f}" ly="{(Box * 0.1)[1]:<.5f}" lz="{(Box * 0.1)[2]:<.5f}"/>\n',
            )

            # write atom coordinates
            ofile.write(f'<position num="{len(self.Atoms)}">\n')
            ofile.writelines(
                f"{((atom_.R - 0.5 * Box) * 0.1)[0]:11.5f} {((atom_.R - 0.5 * Box) * 0.1)[1]:11.5f} {((atom_.R - 0.5 * Box) * 0.1)[2]:11.5f}\n"
                for atom_ in self.Atoms
            )
            ofile.write("</position>\n")

            # write atom masses
            ofile.write(f'<mass num="{len(self.Atoms)}">\n')
            ofile.writelines(f"{atom_.Mass:11.5f}\n" for atom_ in self.Atoms)
            ofile.write("</mass>\n")

            # write atom types
            ofile.write(f'<type num="{len(self.Atoms)}">\n')
            ofile.writelines(f"{atom_.AtomType.Name}\n" for atom_ in self.Atoms)
            ofile.write("</type>\n")

            # write atom charges
            ofile.write(f'<charge num="{len(self.Atoms)}">\n')
            ofile.writelines(
                f"{atom_.Charge * sqrt(138.935 / float(eps)):11.5f}\n"
                for atom_ in self.Atoms
            )
            ofile.write("</charge>\n")

            # write pairwise bonds
            if len(self.PairBonds) > 0:
                ofile.write("<bond>\n")
                ofile.writelines(
                    f"{bond_.BondType.Name} {[atom_.ID - 1 for atom_ in bond_.Atoms][0]} {[atom_.ID - 1 for atom_ in bond_.Atoms][1]}\n"
                    for bond_ in self.PairBonds
                )
                ofile.write("</bond>\n")

            # write angle bonds
            if len(self.AngleBonds) > 0:
                ofile.write("<angle>\n")
                ofile.writelines(
                    f"{bond_.BondType.Name} {[atom_.ID - 1 for atom_ in bond_.Atoms][0]} {[atom_.ID - 1 for atom_ in bond_.Atoms][1]} {[atom_.ID - 1 for atom_ in bond_.Atoms][2]}\n"
                    for bond_ in self.AngleBonds
                )
                ofile.write("</angle>\n")

            # write footer
            ofile.write(footer_)

        # write file with tabulated interaction records, which shall be included in galamost.gala
        with open(pyfile, "w") as ofile:
            # pairwise intractions
            ofile.write(
                "pairs = galamost.PairForceTable(all_info, neighbor_listSR,  npoints_in_table)\n",
            )
            for i, i_atomtype in enumerate(self.AtomTypes):
                ofile.writelines(
                    "pairs.setPotential('{0[0]}','{0[1]}', 'table_{0[0]}-{0[1]}.dat', 0 ,1)\n".format(
                        sorted([i_atomtype.Name, j_atomtype.Name]),
                    )
                    for j_atomtype in self.AtomTypes[i:]
                )
            ofile.write("app.add(pairs)\n")

            # pair-bonds
            if len(self.PairBonds) > 0:
                ofile.write(
                    "bonds = galamost.BondForceTable(all_info, npoints_in_table)\n",
                )
                ofile.writelines(
                    f"bonds.setPotential('{bondtype.Name}', 'table_{bondtype.MolType.Name:<}-{bondtype.Number:<d}.dat', 0 ,1)\n"
                    for bondtype in self.PairBondTypes
                )
                ofile.write("app.add(bonds)\n")

            # angle-bonds
            if len(self.AngleBonds) > 0:
                ofile.write(
                    "angles = galamost.AngleForceTable(all_info, npoints_in_table-1)\n",
                )
                ofile.writelines(
                    f"angles.setPotential('{bondtype.Name}', 'table_{bondtype.MolType.Name:<}-{bondtype.Number:<d}.dat', 0 ,1)\n"
                    for bondtype in self.AngleBondTypes
                )
                ofile.write("app.add(angles)\n")

    def WriteGALAMOSTExclusions(self, name="exclusions"):
        """Create a set of two exclusion files for GALAMOST: One for short-range and one for electrostatic interactions.

        Args:
            name (str): Prefix-name of the file, Default 'exclusions'

        Example::

            MT.WriteGALAMOSTExclusions(name='exclusions', exclusions_EL='exclusions.dat', exclusions_SR='RDFref.rdf')
            or
            MT.WriteGALAMOSTExclusions(name='exclusions',
                                        exclusions_EL={'exclusions_A': {DMPC: 1, Chol: 2 },
                                                       'exclusions_B': {DMPC: 1, Chol:-1} } )

        """
        if (
            self.exclusions_EL == self.exclusions_SR
        ):  # if exclusions are same only write one exclusion file
            self._writeGALAMOSTExclusions(
                name=name,
                type="SR",
                exclusions_B=self.exclusions_SR["exclusions_B"],
                exclusions_A=self.exclusions_SR["exclusions_A"],
            )
            with open(name + "EL" + ".inc.py", "w") as ofile:
                ofile.write("neighbor_listEL = neighbor_listSR\n")
        else:
            # write short-range exclusions
            self._writeGALAMOSTExclusions(
                name=name,
                type="SR",
                exclusions_B=self.exclusions_SR["exclusions_B"],
                exclusions_A=self.exclusions_SR["exclusions_A"],
            )
            # write electrostatics exclusions
            self._writeGALAMOSTExclusions(
                name=name,
                type="EL",
                exclusions_B=self.exclusions_EL["exclusions_B"],
                exclusions_A=self.exclusions_EL["exclusions_A"],
            )

    def _writeGALAMOSTExclusions(
        self,
        name="exclusions",
        type="SR",
        exclusions_A=None,
        exclusions_B=None,
    ):
        """Create a python file for GALAMOST which will define exclusions as in the system.

        Args:
            name (str): name of both output file and variable for GALAMOST neighbor-list. Default: exclusions
            exclusions_A: dictionary defining exclusions based on angle bonds: ``{MolType1: Nexcl, MolType2: Nexcl }``
            exclusions_B: dictionary defining exclusions based on pair bonds:  ``{MolType1: Nexcl, MolType2: Nexcl }``

        """
        if exclusions_B is None:
            exclusions_B = dict.fromkeys(self.MolTypes, 1)
        if exclusions_A is None:
            exclusions_A = dict.fromkeys(self.MolTypes, 1)

        flag_addFromBonds = all(
            [nexcl != 0 for nexcl in exclusions_B.values()],
        )  # If we exclude direct bonds in all moltypes
        flag_addFromAngles = all(
            [nexcl != 0 for nexcl in exclusions_A.values()],
        )  # If we exclude direct angles in all moltypes

        with open(name + type + ".inc.py", "w") as ofile:
            neighbor_list = f"neighbor_list{type}"
            ofile.write(
                neighbor_list + " = galamost.NeighborList(all_info, rcut, rbuffer)\n",
            )

            if flag_addFromBonds:
                ofile.write(neighbor_list + ".addExclusionsFromBonds()\n")
            if flag_addFromAngles:
                ofile.write(neighbor_list + ".addExclusionsFromAngles()\n")

            # check if we need to do specific exclusions at all:
            if not (
                all([(0 <= nexcl <= 1) for nexcl in exclusions_B.values()])
                and all([(0 <= nexcl <= 1) for nexcl in exclusions_A.values()])
            ):
                # create dictionary of atom exclusions
                excl_atom_dict = self._create_excluded_atom_pairs_list(
                    exclusions_B=exclusions_B,
                    exclusions_A=exclusions_A,
                )
                for the_atom, other_atoms in excl_atom_dict.items():
                    for other_atom in other_atoms:
                        if the_atom.ID < other_atom.ID:  # avoid duplicates
                            assert the_atom.Molecule == other_atom.Molecule, (
                                "Excluded atoms do not belong to same molecule!"
                            )
                            # if we already excluded all FromBonds or FromAngles corresponding atom-pairs will be ignored
                            if not (
                                (
                                    flag_addFromBonds
                                    and the_atom.IsBonded(other_atom, kind="pair")
                                )
                                or (
                                    flag_addFromAngles
                                    and the_atom.IsBonded(other_atom, kind="angle")
                                )
                            ):
                                ofile.write(f"#{the_atom.Name}-{other_atom.Name}\n")
                                the_atom_index = the_atom.Molecule.Atoms.index(the_atom)
                                other_atom_index = other_atom.Molecule.Atoms.index(
                                    other_atom,
                                )
                                ofile.writelines(
                                    neighbor_list
                                    + f".addExclusion({molecule.Atoms[the_atom_index].ID - 1},{molecule.Atoms[other_atom_index].ID - 1})\n"
                                    for molecule in the_atom.Molecule.MolType.Molecules
                                )

    def SetExclusions(self, inpMagiC=None, exclusions_SR=None, exclusions_EL=None):
        """Set exclusions rules for the system based on provided input. Exclusions are set for short-range and electrostatic interactions.

        Args:
            inpMagiC (str): Magic.inp file which contains records with exclusion.dat-files
            exclusions_EL (dict): Exclusion rules for electrostatics.
            exclusions_SR (dict): Exclusion rules for short-range interactions.
                Both exclusion-rules can be specified either by file having NPAIRBONDSEXCLUDE/NANGLEBONDSEXCLUDE, such as
                .rdf, .pot, exclusions.dat, magic.out or as a nested dictionary::

                        exclusions_SR = {
                            "exclusions_A": {MolType1: Nexcl, MolType2: Nexcl},
                            "exclusions_B": {MolType1: Nexcl, MolType2: Nexcl},
                        }

        NB: If nothing is specified, default exclusions will be used.

        Example::

            SetSystemExclusions(inpMagic="magic.inp")
            SetSystemExclusions(exclusions_SR="somerdf.rdf", exclusions_EL="somepot.pot")
            SetSystemExclusions(
                exclusions_SR={
                    "exclusions_A": {"DMPC.CG": 1, "CHOL.CG": 1},
                    "exclusions_B": {"DMPC.CG": 1, "CHOL.CG": -1},
                }
            )


        """
        # TODO: Consider adding to _init_
        from rdf import _read_prop

        from MagicTools import _read_and_clean_lines

        def _getExclusionsFromFile(exclusions_):
            """Parse the file and read NPAIRBONDSEXCLUDE and NANGLEBONDSEXCLUDE records from it"""
            try:
                with open(exclusions_) as ifile:
                    lines = ifile.readlines()
                    NPairBondsExclude = DFset.DFset._parse_exclusions(
                        DFset.DFset._read_prop("NPAIRBONDSEXCLUDE", lines, must=True),
                    )
                    NAngleBondsExclude = DFset.DFset._parse_exclusions(
                        DFset.DFset._read_prop("NANGLEBONDSEXCLUDE", lines, must=True),
                    )
                    exclusions_ = {
                        "exclusions_A": NAngleBondsExclude,
                        "exclusions_B": NPairBondsExclude,
                    }
            except:
                print(f"Can not read exclusion from the file:{exclusions_}")
                return None
            return exclusions_

        def _getExclusions(exclusions_):
            if isinstance(exclusions_, str):
                exclusions_ = _getExclusionsFromFile(
                    exclusions_,
                )  # Get the exclusions dictionary from the filename
            if isinstance(
                exclusions_,
                dict,
            ):  # If dictionary, resolve MolTypeNames to MolType objects
                exclusions_ = {
                    "exclusions_A": {
                        self.GetMolType(moltypename_): value_
                        for moltypename_, value_ in exclusions_["exclusions_A"].items()
                    },
                    "exclusions_B": {
                        self.GetMolType(moltypename_): value_
                        for moltypename_, value_ in exclusions_["exclusions_B"].items()
                    },
                }
            if exclusions_ is None:
                exclusions_ = {
                    "exclusions_A": dict.fromkeys(self.MolTypes, 1),
                    "exclusions_B": dict.fromkeys(self.MolTypes, 1),
                }

            return exclusions_

        if inpMagiC is not None:
            lines = _read_and_clean_lines(inpMagiC)
            exclusions_SR = _read_prop(
                "exclusionSR",
                lines,
                old="exclusionsSR",
                must=False,
                default=None,
            )
            exclusions_EL = _read_prop(
                "exclusionEL",
                lines,
                old="exclusionsEL",
                must=False,
                default=None,
            )

        self.exclusions_EL = _getExclusions(exclusions_EL)
        self.exclusions_SR = _getExclusions(exclusions_SR)

        print("Exclusions were set succesfully:")

        def __print_excl(name, dict_):
            print(name)
            print(
                "   NAngleBondsExclude={0}".format(
                    ",".join(
                        [
                            "{0}:{1}".format(moltype_, dict_["exclusions_A"][moltype_])
                            for moltype_ in sorted(
                                dict_["exclusions_A"].keys(),
                                key=lambda x: str(x),
                            )
                        ],
                    ),
                ),
            )
            print(
                "   NPairBondsExclude={0}".format(
                    ",".join(
                        [
                            "{0}:{1}".format(moltype_, dict_["exclusions_B"][moltype_])
                            for moltype_ in sorted(
                                dict_["exclusions_B"].keys(),
                                key=lambda x: str(x),
                            )
                        ],
                    ),
                ),
            )

        __print_excl(name="ExclusionsEL:", dict_=self.exclusions_EL)
        __print_excl(name="ExclusionsSR:", dict_=self.exclusions_SR)

    def WriteGromacsTopology(self, topfile="topol.top"):
        """Write the System to a GROMACS-topology file topfile.top."""
        self._clear_cached()
        assert (self.__dfset is None) or isinstance(self.__dfset, DFset.DFset)
        with open(topfile, "w") as ofile:
            # writing head to a top-file
            ofile.write(
                "; This topology file was automatically generated by MagicTools.GromacsTopology, so use it with care!\n",
            )
            ofile.write("[ defaults ]\n")
            ofile.write(
                "; nbfunc	comb-rule	gen-pairs	fudgeLJ	fudgeQQ\n   1		1		no		1.0	1.0\n",
            )
            # Writing information about atomtypes
            ofile.write(
                "[ atomtypes ]\n"
                ";!!!THIS ATOMTYPES DEFINITION ARE ARBITRARY AND STATED HERE TO COMPLY GROMACS REQUIREMENTS\n"
                "; THEY WILL BE OVERDEFINED BY ATOMS SECTION BELOW!!!\n"
                ";name  at.num      mass        charge   ptype       c6           c12\n",
            )
            iBondGlobal = 0

            ofile.writelines(
                f"{at.Name:4s} {1:4d} {1.0:8.4f} {0.0:6.3f} A  1.00  0.000\n"
                for at in self.AtomTypes
            )

            for MT in self.MolTypes:
                ofile.write("[ moleculetype ]\n; molname	nrexcl\n")
                _excl_ = 1
                if (
                    self.exclusions_SR == self.exclusions_EL
                ):  # if we have same type of exclusions in the system, we can export to GRAMCS
                    if self.exclusions_SR["exclusions_B"] is not None:
                        _excl_ = self.exclusions_SR["exclusions_B"][MT.Name]
                else:
                    print(
                        "Unfortunately GROMACS does not allow to have different exculsions for short-range interactions and for electrostatics",
                    )
                    return
                ofile.write("{0} {1}\n".format(MT.Name.replace(".CG", ""), _excl_))

                # atoms
                ofile.write(
                    "[ atoms ] \n;   nr   type  resnr residue  atom   cgnr     charge       mass\n",
                )
                ofile.writelines(
                    "{0:6d} {1:6s} {2:6d} {3:6s} {4:5s} {5:5d} {6:8.4f} {7:8.4f}\n".format(
                        A.Number,
                        A.AtomType.Name.replace(".CG", ""),
                        1,
                        MT.Name.replace(".CG", ""),
                        A.Name,
                        A.Number,
                        A.Charge,
                        A.Mass,
                    )
                    for i, A in enumerate(MT.Atoms)
                )
                # bonds
                ofile.write("[ bonds ]\n ; i	j	funct	table(bond type) k\n")
                for BT in MT.PairBondTypes:
                    sameas_bondtype = self._getSameBond(BT)
                    ofile.writelines(
                        f"{AG[0].Number:3d} {AG[1].Number:3d} {8:3d} {self.BondTypes.index(sameas_bondtype) + 1:3d} {1.0:4.2f}\n"
                        for AG in BT.AtomGroups
                    )
                # angles
                ofile.write(
                    "[ angles ]\n ; i	j   k	funct	table(bond type) k\n",
                )
                pairs = []
                for BT in MT.AngleBondTypes:
                    sameas_bondtype = self._getSameBond(BT)
                    iBondGlobal += 1
                    for AG in BT.AtomGroups:
                        ofile.write(
                            f"{AG[0].Number:3d} {AG[1].Number:3d} {AG[2].Number:3d} {8:3d} {self.BondTypes.index(sameas_bondtype) + 1:3d} {1.0:4.2f}\n",
                        )
                        pairs.append([AG[0].Number, AG[2].Number])
                        pairs.append([AG[2].Number, AG[0].Number])
                pairs.sort()
                d = defaultdict(list)  # Dictionary with exclusions
                for k, v in pairs:
                    d[k].append(v)
                ofile.write("[ exclusions ]\n")
                for i in d:
                    ofile.write(str(i) + " ")
                    ofile.writelines(str(j) + " " for j in d[i])
                    ofile.write("\n")

            ofile.write("[ system ]\n")
            ofile.write("!!! WRITE HERE THE NAME OF YOUR SYSTEM !!!\n")
            ofile.write("[ molecules ]\n")
            ofile.write("; !!! PLEASE CHECK THE NUMBER OF MOLECULES !!!\n")
            for iMT, MT in enumerate(self.MolTypes):
                try:
                    ofile.write(
                        "{0:s} {1:d}\n".format(
                            MT.Name.replace(".CG", ""),
                            len(MT.Molecules),
                        ),
                    )
                except:
                    ofile.write(
                        MT.Name + " !!! WRITE HERE THE NUMBER OF MOLECULES !!!\n",
                    )
        print(
            "Topology created sucessfully. "
            "Do not forget to manually correct the number of molecules at the end of the file.",
        )

    def ReadGeometry(self, iGeometry):
        """Read geometry of the system from given XMOL (XYZ) file. No checks of the reading order
        is preformed, so it is assumed that geometry file has consistent order of atoms.

        Args:
            iGeometry (str): Name of the *.xmol file

        """
        assert iGeometry.endswith(".xmol"), "Expecting *.xmol file as input"
        print(f"Reading system's geomtery from file XMOL: {iGeometry}")
        with open(iGeometry) as ifile:
            lines = ifile.readlines()
        natoms = int(lines[0].strip())
        if natoms != len(self.Atoms):
            raise MTE.GeneralError(
                f"Error: Number of atoms in the file {natoms} differs from the system defenition {len(self.Atoms)}",
            )
        for line, atom in zip(lines[2 : natoms + 2], self.Atoms):
            (X, Y, Z) = line.split()[1:4]
            atom.R = np.array([float(X), float(Y), float(Z)])
        # Detect Box size
        if not self.Box:
            if "BOX:" in lines[1]:
                try:
                    Box = [
                        float(l.strip()) for l in lines[1].split("BOX:")[1].split(",")
                    ]
                except:
                    try:
                        Box = [
                            float(l.strip())
                            for l in lines[1].split("BOX:")[1].strip().split()
                        ]
                    except:
                        print(
                            "Can not detect Box size from the trajectory file. "
                            "Check the second line of the file:" + lines[1],
                        )
                        return
                print(f"Box={Box}")
                self.Box = Box
            else:
                print(
                    "Can not detect BOX: record in the trajectory file. Check the second line of the file:"
                    + lines[1],
                )
                return

    def WriteMCMs(self):
        """Save all molecular types belonging to the system to MCM-files."""
        for iMType in self.MolTypes:
            iMType.Write2MCM()

    @staticmethod
    def __parseInputMagic(inpMagiC):
        """Parse MagiC.inp file and detect MolTypes and NMols and box size."""
        from MagicTools import _read_and_clean_lines

        try:
            try:
                lines = _read_and_clean_lines(inpMagiC)
            except:
                print(f"Error reading file {inpMagiC}")
                return None
            MTypes = [l for l in lines if "NAMEMTYPE" in l.upper()]
            if not MTypes:
                print(
                    f"Error reading file {inpMagiC}. Can not detect NameMType record.",
                )
                return None
            MTypes = MTypes[0].split("=")[1].replace(" ", "").split(",")
            MTypes = [MT.strip() for MT in MTypes]

            NMols = [l for l in lines if "NMOLMTYPE" in l.upper()]
            if not NMols:
                print(
                    f"Error reading file {inpMagiC}. Can not detect _n_mol_mtype record.",
                )
                return None
            NMols = NMols[0].split("=")[1].replace(" ", "").split(",")
            NMols = [int(l) for l in NMols]
            if len(NMols) != len(MTypes):
                print(
                    f"Error reading file {inpMagiC}. Number of _n_mol_mtype and NameMType records is not consistent.",
                )
                return None

            Box = [l for l in lines if "BOX" in l.upper()]
            if not Box:
                print(f"Error reading file {inpMagiC}. Can not detect BOX record.")
                return None
            Box = Box[0].split("=")[1].split(",")
            Box = [float(l) for l in Box]
            if len(Box) == 1:  # if a single value provided
                Box = [Box, Box, Box]

            if len(NMols) != len(MTypes):
                print(
                    f"Error reading file {inpMagiC}. Number of _n_mol_mtype and NameMType records is not consistent.",
                )
                return None

            return MTypes, NMols, Box
        except:
            print(
                f"Can not detect Molecular Types and Number of molecules from file {inpMagiC}",
            )
            return None

    def GetMolType(self, moltypename, line=""):
        """Return the MolType-object belonging to the system searched by it's name.

        Args:
            moltypename (str):  Name of the Molecular Type

        Return (MolType):

        """
        if isinstance(moltypename, MolType.MolType):
            if moltypename in self.MolTypes:
                return moltypename
            raise ValueError(
                f"Can not find such MolType in the system:{moltypename.Name} \n System types:{[mt.Name for mt in self.MolTypes]} \nLine {[mt.Name for mt in self.MolTypes]}",
            )
        mol_types_ = [mt for mt in self.MolTypes if mt.Name == moltypename]
        if len(mol_types_) == 0:
            raise ValueError(
                f"Can not find such MolType in the system:{moltypename} \n System types:{[mt.Name for mt in self.MolTypes]} \nLine {line}",
            )
        # Check and convert provided atom types to a Atom.AtomType instances
        if len(mol_types_) > 1:  # Check if 2 ATypes stated
            raise ValueError(
                f"Error: more than one MolType with such name ({moltypename}) exist in the system! "
                f"Something is wrong! \n line: {line}",
            )
        return mol_types_[0]

    def _GetAtomTypesPair(self, atom_types, line):
        """Check and convert provided pair of atom types to a Atom.AtomType instances."""
        # TODO: Refactor. Use GetAtomType method
        if len(atom_types) != 2:  # Check if 2 ATypes stated
            raise ValueError(f"Error in Pair of AtomTypes stated in line: {line}")
        if all(
            [isinstance(at, AtomType.AtomType) for at in atom_types],
        ):  # Correct type - do nothing
            pass
        elif all(
            [isinstance(at, str) for at in atom_types],
        ):  # Strings -> Convert to AtomTypes
            atom_types = [
                atom_type
                for atom_type_str in atom_types
                for atom_type in self.AtomTypes
                if atom_type_str == atom_type.Name
            ]
            if len(atom_types) != 2:
                raise ValueError(
                    f"Can not find such AtomTypes in the system. line: {line}\nSystem types:{[atom_type.Name for atom_type in self.AtomTypes]}",
                )
        else:
            raise ValueError(f"Error in Pair of AtomTypes stated in line: {line}")
        return atom_types

    def GetBondType(self, str_):
        """Search for a bond type in the system, which corresponds to string in format MolTypeName:BondNumber, e.g. DNA.CG:1.

        Args:
            str_ (str): Bond name, string in format MolTypeName:BondNumber, e.g. DNA.CG:1

        Return: (BondType): BondType-object

        """
        str_ = str_.strip()
        assert len(str_.split(":")) == 2, "Can not parse Bond record:" + str_
        moltype_ = self.GetMolType(str_.split(":")[0].strip(), str_)
        numbond_ = int(str_.split(":")[1].strip())
        bonds_ = [bond_ for bond_ in moltype_.BondTypes if bond_.Number == numbond_]
        assert len(bonds_) == 1, (
            f"Can not find bond type with number {numbond_} in molecular type {moltype_.Name}. \n string {str_}"
        )
        bond_ = bonds_[0]
        return bond_

    def GetAtomType(self, atom_type_name, raise_exception=False):
        """Checks if atom type with given name is present in the system and returns it, otherwise returns None or raises exception.

        Args:
            atom_type_name (str): Name of the atom type to search for
            raise_exception (bool): Raise an exception if the atom type is not found. Default False.

        Return (AtomType):

        """
        assert isinstance(atom_type_name, str)
        atom_type_name = atom_type_name.strip()
        if atom_type_name in self.AtomTypesDict.keys():
            return self.AtomTypesDict[atom_type_name]
        if raise_exception:
            raise KeyError(
                f"Atom type with name {atom_type_name} is not found among the AtomTypes of the system: {self.AtomTypesDict.keys()}",
            )
        return None

    @property
    def AtomTypesDict(self):
        """Dictionary to resolve AtomType-object by name."""
        return self._AtomTypesDict

    def AddAtomType(self, atomtype):
        """Add an AtomType to the list of atom types of the system."""
        if atomtype not in self._AtomTypesDict.values():
            self._AtomTypesDict[atomtype.Name] = atomtype
            self._clear_cached()

    def WriteAsRDFinp(self):
        """Print the system as lines for RDF.inp file. Useful when writing script generating RDF.inp file."""
        lines = []
        lines += ["&CGTypes"]
        for atomtype in self.AtomTypes:
            lines += [atomtype.WriteAsRDFinp()]
        lines += ["&EndCGTypes"]
        lines += ["&RDFsNB"]
        for iat1, at1 in enumerate(self.AtomTypes):
            for at2 in self.AtomTypes[iat1:]:
                lines += [f"Add: {at1.Name}--{at2.Name}"]
        lines += ["&EndRDFsNB"]
        lines += ["&RDFsB"]
        for bt in self.PairBondTypes:
            lines += [bt.WriteAsRDFinp()]
        lines += ["&EndRDFsB"]
        lines += ["&RDFsA"]
        for bt in self.AngleBondTypes:
            lines += [bt.WriteAsRDFinp()]
        lines += ["&EndRDFsA"]
        return lines

    def CloneLAMMPSdata(
        self,
        trj_file,
        in_data_file="LAMMPS.data~",
        out_data_file="LAMMPS.data",
    ):
        """Clone existing LAMMPS data-file by subsituting Atoms-section with atoms and coordinates read from specified trajectory file.

        Args:
            trj_file (str): Trajectory in XMOL format
            in_data_file (str): Template LAMMPS.datafile
            out_data_file (str): Output LAMMPS.data file

        """
        # read geometry
        self.ReadGeometry(trj_file)
        with open(in_data_file) as ifile:
            lines = ifile.readlines()
        first = lines.index(" Atoms\n") + 2
        last = lines.index(" Bonds\n") - 1
        # Write Atoms to new lines
        new_lines = []
        for iAtom in self.Atoms:
            new_lines.append(
                f"{iAtom.ID:d} {iAtom.Molecule.ID:d} {iAtom.AtomType.Number:d} {iAtom.Charge:11.5f} {iAtom.R[0]:11.5f} {iAtom.R[1]:11.5f} {iAtom.R[2]:11.5f}\n",
            )
        assert len(new_lines) == last - first
        lines[first:last] = new_lines
        with open(out_data_file, "w") as ofile:
            ofile.writelines(lines)

    def _create_excluded_atom_pairs_list(self, exclusions_B=None, exclusions_A=None):
        """Build a list of excluded atoms for the system, based on the bonds and the provided exclusion rules:

        Returns: dictionary {atom:[excluded_atoms]}

        """
        from collections import OrderedDict

        # check the input and convert
        excluded_pair = {
            atom_: [atom_] for moltype_ in self.MolTypes for atom_ in moltype_.Atoms
        }  # initiate the dict
        excluded_angle = {
            atom_: [atom_] for moltype_ in self.MolTypes for atom_ in moltype_.Atoms
        }
        if exclusions_B is None:
            exclusions_B = dict.fromkeys(self.MolTypes, 1)
        if exclusions_A is None:
            exclusions_A = dict.fromkeys(self.MolTypes, 1)

        print("\nExclusions in the system:")
        for moltype_ in self.MolTypes:
            print(
                f"{moltype_}: Exclusions: {exclusions_B[moltype_]}-PairBonds, {exclusions_A[moltype_]}-AngleBonds",
            )
            for level_excl in range(exclusions_B[moltype_]):
                for atom_key in excluded_pair:
                    if atom_key in moltype_.Atoms:
                        atom_values = excluded_pair[atom_key]
                        atoms_new_ = [
                            atom_
                            for atom2_ in atom_values
                            for bond_ in atom2_.Bonds
                            if isinstance(bond_, Bond.PairBond)
                            for atom_ in bond_.Atoms
                            if atom_ != atom2_
                        ]  # take the other atom from the bond
                        excluded_pair[atom_key] = atom_values + [
                            atom_ for atom_ in atoms_new_ if atom_ not in atom_values
                        ]

            for level_excl in range(exclusions_A[moltype_]):
                for atom_key in excluded_angle:
                    if atom_key in moltype_.Atoms:
                        atom_values = excluded_angle[atom_key]
                        atoms_new_ = [
                            atom_
                            for atom2_ in atom_values
                            for bond_ in atom2_.Bonds
                            if isinstance(
                                bond_,
                                Bond.AngleBond,
                            )  # and bond_.Atoms.index(atom2_) != 1
                            for atom_ in bond_.Atoms[0:3:2]
                            if atom_ != atom2_
                        ]  # take the other atom from the bond
                        excluded_angle[atom_key] = atom_values + [
                            atom_ for atom_ in atoms_new_ if atom_ not in atom_values
                        ]
            if (exclusions_B[moltype_] < 0) or (
                exclusions_A[moltype_] < 0
            ):  # Exclude all
                print(f"{moltype_}: Exclude all intramolecular pairs for")
                for atom_ in moltype_.Atoms:
                    excluded_pair[atom_] = moltype_.Atoms

        excluded_ = OrderedDict()
        for key_ in sorted(excluded_pair.keys(), key=lambda x: x.ID):
            excluded_[key_] = excluded_pair[key_] + [
                atom_
                for atom_ in excluded_angle[key_]
                if atom_ not in excluded_pair[key_]
            ]

        # remove atom from being excluded with itself (otherwise it causes troubles for single-atoms)
        for key_ in excluded_.keys():
            excluded_[key_].remove(key_)
        # remove duplicates and sort
        for key_ in excluded_.keys():
            lst_ = excluded_[key_]
            excluded_[key_] = sorted(list(set(lst_)), key=lambda x: x.ID)
        return excluded_

    def WriteGeometryGRO(self, ofilename, AtomTypesInsteadOfAtoms=False):
        """Write system's geometry as .gro file.

        Args:
            ofilename (str): File to write the geometry
            AtomTypesInsteadOfAtoms (bool): Put names of atomtypes instead of atoms, useful for creating index file for GROMACS

        """
        with open(ofilename, "w") as ofile:
            ofile.write("\n")
            ofile.write(f"{len(self.Atoms)}\n")
            i = 0
            for moltype_ in self.MolTypes:  # over types
                for mol_ in moltype_.Molecules:  # over molecules of type
                    for atom_ in mol_.Atoms:  # over all atoms ov molecule of given type
                        ofile.write(
                            "{0:>5d}{1:<5.5s}{2:>5.5s}{3:>5d}{4[0]:>8.3f}{4[1]:>8.3f}{4[2]:>8.3f}{5:8.4f}{5:8.4f}{5:8.4f}\n".format(
                                mol_.Number,
                                moltype_.Name.replace(".CG", ""),
                                atom_.AtomType.Name
                                if AtomTypesInsteadOfAtoms
                                else atom_.Name,
                                atom_.ID,
                                atom_.R * 0.1,
                                0.0,
                            ),
                        )
                        i += 1
            ofile.write(
                "{0[0]:10.5f}{0[1]:10.5f}{0[2]:10.5f}\n".format(
                    np.asarray(self.Box) * 0.1,
                ),
            )

    def IsSystemMatchRDFs(self, rdfset):
        """Check if current geometry of the system matches the provided distributions.

        Args:
            rdfset (DFset): RDF-set to match

        Returns:
            True or False. If false, also list the non-matching bonds, their values and corresponding rdf-range

        """
        assert isinstance(rdfset, DFset.DFset), "Expecting object of DFset"
        flag = True
        rdfset._SetBondNamesByMolTypeAndBondNumber()
        for bondtype in self.BondTypes:
            df = rdfset.FindBondDF(
                MolTypeName=bondtype.MolType.Name,
                BondNumber=bondtype.Number,
            )
            if df is not None:
                for bond in bondtype.Bonds:
                    if not (df.Min < bond.Value < df.Max):
                        print(
                            f"Bond: {bond.Name} has value {bond.Value:12.7f} which does not match corresponding distribution",
                        )
                        print(
                            f"{df.Name}: Min={df.Min} Max={df.Max} Atoms=({bond.Atoms})\n",
                        )
                        flag = False
        return flag
