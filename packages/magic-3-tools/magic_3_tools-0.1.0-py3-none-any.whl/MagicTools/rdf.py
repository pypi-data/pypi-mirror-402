#!/usr/bin/env python
# -------------------------------------------------------------------------------
# Main

import glob
import re
import sys
import time

import numpy as np

from . import DF, Atom, AtomType, BondType, DFset, MolType, System, Trajectory
from . import MTException as MTE
from .object_magictools import ObjectMagicTools


def __clean_and_up(s):
    s = s.replace("'", "").replace('"', "").strip().strip(",")
    if s.startswith("&"):
        s = s.upper()
    return s


def _prepare_lines(lines):
    lines = [__clean_and_up(l) for l in lines]
    lines = [l for l in lines if not l.startswith(("!", "#"))]
    lines = [l for l in lines if l != ""]
    return lines


def _try_file(file_name):
    try:
        with open(file_name) as ifile:
            lines = ifile.readlines()
        print("Detecting format of the input file")
        lines = _prepare_lines(lines)
        if "&PARAMETERS" not in lines:
            print(
                "Can not detect file format! Please ensure that you are using MagiC-2 RDF input format.",
            )
            raise MTE.GeneralError(
                "Can not detect file format! Please ensure that you are "
                "using MagiC-2 RDF input format.  Old format is deprecated since MagiC-2.3",
            )
    except OSError:
        raise MTE.GeneralError("Unable to open file:" + file_name)
    print("file " + file_name + " succesfully opened for reading")


def _read_prop(knd, lines, old=None, must=True, default=None):
    query = list(
        filter(lambda x: re.search(f"^{knd}|{old} *=", x, re.IGNORECASE), lines),
    )
    if query:
        return query[0].split("=")[1].strip()
    if must:
        raise MTE.InputValueError("Error: No " + knd + " value provided")
    return default


def _check_tag(tag, lines, must_be_present=True):
    if lines.count(tag) > 1:
        raise MTE.InputValueError(f"too many {tag} tags in the file")
    if lines.count(tag) == 1:
        return lines.index(tag)
    if (lines.count(tag) == 0) and (not must_be_present):
        return 0
    raise MTE.InputValueError("Can not find " + tag + " tag in the file")


def _check_tags(tag, lines, must_be_present=True):
    return (
        _check_tag("&" + tag, lines, must_be_present=must_be_present),
        _check_tag("&END" + tag, lines, must_be_present=must_be_present),
    )


class RDFCalculator(ObjectMagicTools):
    """Worker class for RDF calculation."""

    def __init__(self, inputfile, skip_trj_check=False, opt_memory_use=False):
        """Read input file and initialize the class."""
        super(RDFCalculator, self).__init__()
        self._input_file_name = inputfile
        self.RDFs = []
        self.ADFs = []
        self.System = System.System()
        self.__rdf_output_file = None
        self.__skip_trj_check__ = skip_trj_check
        self._opt_memory_use = opt_memory_use
        _try_file(self._input_file_name)
        self.__read_input_file()

        # estimate number of atoms and if too big, switch to opt_memory_use = True
        if (
            max([moltype_._nmol * moltype_.NAtoms for moltype_ in self.System.MolTypes])
            > 5000
        ):
            print(
                "Warning: It seems that the system is large, so we turn on memory optimization mode.",
            )
            self._opt_memory_use = True

    @property
    def MolTypes(self):
        return self.System.MolTypes

    @property
    def AtomTypes(self):
        return self.System.AtomTypes

    @property
    def Box(self):
        return self.System.Box

    @Box.setter
    def Box(self, box):
        self.System.Box = box

    @property
    def RDFs_NB(self):
        return [rdf_ for rdf_ in self.RDFs if isinstance(rdf_, DF.RDF_NB)]

    @property
    def RDFs_B(self):
        return [rdf_ for rdf_ in self.RDFs if isinstance(rdf_, DF.RDF_PairBond)]

    @property
    def RDFs_A(self):
        return [rdf_ for rdf_ in self.RDFs if isinstance(rdf_, DF.RDF_AngleBond)]

    def __read_input_file(self):
        # Read input file, remove comments and empties, capitalize keywords and tags
        with open(self._input_file_name) as ifile:
            all_lines = ifile.readlines()
        all_lines = _prepare_lines(all_lines)

        # Reading parameters
        i_traj_start, i_traj_end = _check_tags("PARAMETERS", all_lines)
        lines = all_lines[i_traj_start:i_traj_end]

        print("Reading Parametrs section")
        # Analyzing Molecular Types
        try:
            names_mol_type = _read_prop("NAMEMTYPE", lines, old="NAMOL")
            names_mol_type = names_mol_type.replace("'", "").replace(" ", "").split(",")
            for name_mol_type in names_mol_type:
                if name_mol_type.endswith((".mcm", ".mmol")):
                    MolType.MolType(name_mol_type, self.System)
                else:
                    print(
                        "No types of the molecular file descritions were provided: detecting them automatically",
                    )
                    ls = [
                        l
                        for l in glob.glob(name_mol_type + ".mcm")
                        + glob.glob(name_mol_type + ".mmol")
                    ]
                    if len(ls) == 1:
                        MolType.MolType(ls[0], self.System)
                    elif len(ls) == 2:
                        print(
                            f"Two molecular description files are detected for the type {name_mol_type}",
                        )
                        print("MMOL file will be used.")
                        MolType.MolType(
                            [l for l in ls if l.endswith(".mmol")][0],
                            self.System,
                        )
                    else:
                        raise MTE.InputValueError(
                            f"No or too few molecular description files are detected for the type {name_mol_type} {ls}",
                        )
        except MTE.InputValueError:
            raise MTE.RDFReadError("Unable to read MolecularType descriptions")

        # Dump all bondtypes and bond_types which could be read from mcm-file.
        for mol_type in self.MolTypes:
            mol_type._BondTypes = []
            for molecule in mol_type.Molecules:
                molecule._Bonds = []
                for atom_ in molecule.Atoms:
                    atom_._clear_cached()

        # self._enumerate_atoms()         # Global enumaration of atoms in Molecular types.
        print(f"NameMType={[mol_type.Name for mol_type in self.MolTypes]}")
        print(f"Number of Molecular types detected={len(self.MolTypes)}")
        # Number of molecules of each type: _nmolmtype
        nmolmtype = _read_prop("NMOLMTYPE", lines, old="NSPEC")
        try:
            nmolmtype = nmolmtype.replace(" ", "").split(",")
            nmolmtype = [int(n_atoms) for n_atoms in nmolmtype]
        except:
            raise MTE.RDFReadError(
                f"Unable to read number of molecule values from the file: got {nmolmtype} instead of an integer array",
            )
        if len(nmolmtype) != len(self.MolTypes):
            raise MTE.RDFReadError(
                f"Number of molecular types ({len(self.MolTypes)}) differs from the size of nmolmtype ({len(nmolmtype)})",
            )
        for mt_, nmol_ in zip(self.MolTypes, nmolmtype):
            mt_._nmol = nmol_
            # ----------------------------------------------------------------------------------

        # Trajectory file and format
        try:
            traj_file_name = (
                _read_prop("TRAJFILE", lines, old="FNAME")
                .replace("'", "")
                .replace('"', "")
            )
        except:
            raise MTE.RDFReadError("Unable to read trajectory file name")
        print(f"TrajFile={traj_file_name}")
        try:
            traj_file_start = int(
                _read_prop("BEGINFILE", lines, old="NFBEG", must=False, default=1),
            )
            traj_file_stop = int(
                _read_prop("ENDFILE", lines, old="NFEND", must=False, default=1),
            )
            traj_file_step = int(
                _read_prop("STEP", lines, old="NFBEG", must=False, default=1),
            )
            # Analyze extension of the file:
            if traj_file_name.upper().endswith((".XMOL", ".TRR", ".XTC")):
                traj_file_type = traj_file_name.split(".")[-1]
                traj_file_name = ".".join(traj_file_name.split(".")[0:-1])
            else:
                traj_file_type = _read_prop("NFORM", lines, old="NFORM").strip("'")
        except:
            raise MTE.RDFReadError(
                "Error while reading trajectory parameters NFBEG, NFEND, ISTEP, NFORM from the file",
            )
        print(f"Trajectory File Format ={traj_file_type}")

        # get total number of atoms in the system:
        n_atoms = sum(
            [len(mol_type.Atoms) * mol_type._nmol for mol_type in self.MolTypes],
        )

        # Here we init trajectory object
        try:
            if traj_file_type.upper() == "XMOL":
                self.Trajectory = Trajectory.XMOL_Trajectory(
                    traj_file_name,
                    traj_file_type,
                    traj_file_start,
                    traj_file_stop,
                    traj_file_step,
                    n_atoms,
                )
            elif traj_file_type.upper() in ("XTC", "TRR"):
                self.Trajectory = Trajectory.Gromacs_Trajectory(
                    traj_file_name + "." + traj_file_type,
                    traj_file_type,
                    traj_file_start,
                    traj_file_stop,
                    traj_file_step,
                    n_atoms,
                )
            else:
                raise MTE.RDFReadError(
                    f"Undefined type of the trajectory file: {traj_file_type.upper()} instead of a XMOL, XTC or TRR",
                )
        except:
            raise MTE.TrajError(
                f"Can not initialize trajectory: {traj_file_name}.{traj_file_type}",
            )

        # Reading periodic box size from input file. it will be used if nothing stated in trajectory
        try:
            box = _read_prop("BOX", lines, must=False)
            if box:
                box = box.replace(",", "")
                if len(box.split()) == 3:
                    self.Box = np.array([float(i) for i in box.split()])
                    print(f"BOX={self.Box}")
            else:
                print(
                    "No periodic box size provided: It will be averaged from the trajectory.",
                )
        except:
            raise MTE.RDFReadError(
                "Error while reading periodic box size BOX from the file",
            )

        # Now reading RDF related specifications form input
        # Reading Output filename

        self.__rdf_output_file = _read_prop("OUTPUTFILE", lines, old="FOUTRDF")
        if not (self.__rdf_output_file.endswith(".rdf")):
            self.__rdf_output_file + ".rdf"
        print(f"RDF will be written to file {self.__rdf_output_file}")

        # Reading max distance of intermolecular RDFs
        try:
            rmax = float(_read_prop("RMAXNB", lines, old="RDFCUT"))
        except:
            raise MTE.RDFReadError(
                "Unable to read RDFCUT value: got {0} instead of a real number".format(
                    _read_prop("RMAXNB", lines, old="RDFCUT"),
                ),
            )
        print(f"RMaxNB={rmax}")
        # Reading r-resolution of intermolecular RDFs
        try:
            resol = float(_read_prop("RESOLNB", lines, old="DELTAR"))
        except:
            raise MTE.RDFReadError(
                "Unable to read ResolNB value: got {0} instead of a real number".format(
                    _read_prop("RESOLNB", lines, old="DELTAR"),
                ),
            )
        print(f"ResolNB={resol}")
        # Reading r-resolution of intramolecular RDFs
        try:
            resoli = float(_read_prop("RESOLB", lines, old="DELTARI"))
        except:
            raise MTE.RDFReadError(
                "Unable to read ResolB value: got {0} instead of a real number".format(
                    _read_prop("RESOLB", lines, old="DELTARI"),
                ),
            )
        print(f"ResolB={resoli}")
        # Reading r-resolution of intramolecular RDFs
        try:
            resolphi = float(
                _read_prop("RESOLA", lines, old="DELTAPHI", default=1.0, must=False),
            )
        except:
            raise MTE.RDFReadError(
                "Unable to read ResolA value: got {0} instead of a real number".format(
                    _read_prop(
                        "RESOLA",
                        lines,
                        old="DELTAPHI",
                        default=1.0,
                        must=False,
                    ),
                ),
            )
        print(f"ResolA={resolphi}")
        # Reading max distance of intramolecular RDFs
        try:
            rmaxi = float(_read_prop("RMAXB", lines, old="RMAX"))
        except:
            raise MTE.RDFReadError(
                "Unable to read RMaxB value: got {0} instead of a real number".format(
                    _read_prop("RMAXB", lines, old="RMAX"),
                ),
            )
        print(f"RMaxB={rmaxi}")

        # Reading exclusion-rules if any
        def _read_exclusion_parameters(prop_name_, defval_):
            try:
                npairbondsexclude_ = _read_prop(
                    prop_name_,
                    lines,
                    must=False,
                    default=defval_,
                )
                npairbondsexclude_ = npairbondsexclude_.replace(" ", "").split(",")
                npairbondsexclude_ = [int(record_) for record_ in npairbondsexclude_]
            except:
                raise MTE.RDFReadError(
                    f"Unable to read NPairBondsExclude values from the file: got {npairbondsexclude_} instead of an integer array",
                )
            if (
                len(npairbondsexclude_) == 1
            ):  # if only one value given, broadcast it to the all molecular types
                npairbondsexclude_ = npairbondsexclude_ * len(self.MolTypes)
            if len(npairbondsexclude_) != len(self.MolTypes):
                raise MTE.RDFReadError(
                    f"Number of molecular types ({len(self.MolTypes)}) differs from the size of {prop_name_} ({len(npairbondsexclude_)})",
                )
            return npairbondsexclude_

        _npairbondsexclude = _read_exclusion_parameters(
            "NPAIRBONDSEXCLUDE",
            ",".join(["1"] * len(self.MolTypes)),
        )
        _nanglebondsexclude = _read_exclusion_parameters(
            "NANGLEBONDSEXCLUDE",
            ",".join(["1"] * len(self.MolTypes)),
        )

        self.exclusions_B = {
            mt_: _npairbondsexclude[i_mt_] for i_mt_, mt_ in enumerate(self.MolTypes)
        }
        self.exclusions_A = {
            mt_: _nanglebondsexclude[i_mt_] for i_mt_, mt_ in enumerate(self.MolTypes)
        }
        self.__exclusions_file = _read_prop(
            "EXCLUSIONS",
            lines,
            must=False,
            default="exclusions.dat",
        )
        # ----------------------------------------------------------------------------------------------------------------
        # Reading CGAtomType Names
        print("\n READING CG-atom types definitions")
        iATypeStart, iATypeEnd = _check_tags("CGTYPES", all_lines)
        #        lines = all_lines[iATypeStart + 1:iATypeEnd]

        for i, l in enumerate(
            all_lines[iATypeStart + 1 : iATypeEnd],
        ):  # Analyze lines for CG-atom type definitions
            if len(l.split(":")) != 2:
                raise MTE.RDFReadError(
                    f"Error while reading list of CG-atom types: line {l}",
                )
            atom_type_name = l.split(":")[0].strip()
            atom_names = l.split(":")[1].split()
            atom_type = AtomType.AtomType(atom_type_name, System=self.System)
            for atom_name in atom_names:
                atoms = [
                    atom
                    for MT in self.MolTypes
                    for atom in MT.Atoms
                    if atom.Name == atom_name
                ]  # Search for atom matches by name
                if not atoms:
                    raise MTE.RDFReadError(
                        f"Error while reading list of CG-atoms : atom {atom_name} is not present"
                        " in molecular topology files (mcm-files)",
                    )
                for atom in atoms:
                    atom_type.AddAtom(atom)  # populate list if atoms for the atom_type
                    atom.AtomType = atom_type  # set atomtype tor the atom

        # Print atom-type summary:
        for AT in self.AtomTypes:
            print(f"{AT.Name}:{[atom_type.Name for atom_type in AT.Atoms]}")
        print("\n")

        # noinspection PyShadowingNames
        def _clean_atoms_container(container, line, atom_group_length, title, MT=None):
            MTs = self.MolTypes if not MT else [MT]
            if not all(
                [len(atom_group) == atom_group_length for atom_group in container],
            ):
                raise MTE.RDFReadError(
                    f"Error in the list of {title} stated in line: {line}",
                )
            if all(
                [
                    isinstance(atom, Atom.Atom)
                    for atom_group in container
                    for atom in atom_group
                ],
            ):
                pass  # Correct type - do nothing
            elif all(
                [
                    isinstance(atom, str)
                    for atom_group in container
                    for atom in atom_group
                ],
            ):
                Atoms = [atom for mol_type in MTs for atom in mol_type.Atoms]
                container = [
                    [
                        atom
                        for atom_str in atom_group
                        for atom in Atoms
                        if atom.Name == atom_str
                    ]
                    for atom_group in container
                ]

                if any(
                    [len(atom_group) != atom_group_length for atom_group in container],
                ):
                    raise MTE.RDFReadError(
                        f"Can not find some of the stated Atoms in the system: {line}\nSystem atoms:{[atom.Name for atom in Atoms]}",
                    )
            return container

        def Add_NB_APairs(atom_types, atom_pairs, line):
            atom_types = self.System._GetAtomTypesPair(atom_types, line)
            atom_pairs = _clean_atoms_container(atom_pairs, line, 2, "AtomGroups")
            # Check if RDF with Types ATypes already exist, if not we create it
            rdflst = [
                rdf
                for rdf in self.RDFs_NB
                if (set(rdf.AtomTypes) == set([at.Name for at in atom_types]))
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one NB RDF with types {[atom_type.Name for atom_type in atom_types]} found: ",
                )
            if len(rdflst) == 0:  # if we found no RDF: Create a new one
                trdf = DF.RDF_NB(
                    Name=atom_types[0].Name + "-" + atom_types[1].Name,
                    Min=0.0,
                    Max=rmax,
                    Npoints=int(rmax / resol),
                    _AtomGroups_=[],
                    AtomTypes=[atom_type.Name for atom_type in atom_types],
                )
                self.RDFs.append(trdf)
            elif len(rdflst) == 1:
                trdf = rdflst[0]
            # At this point we only have a single RDF in the list, which already exist or just has been created.

            # Add pairs which are not present there (check for the order of pairs!)
            _original_set_ = set(
                [
                    tuple(sorted([a, b], key=lambda x: x.ID))
                    for a, b in trdf._AtomGroups_
                ],
            )
            _additional_set_ = set(
                [tuple(sorted([a, b], key=lambda x: x.ID)) for a, b in atom_pairs],
            )
            trdf._AtomGroups_ = [
                sorted([a, b], key=lambda x: x.ID)
                for a, b in _original_set_.union(_additional_set_)
            ]
            print(
                "Added NB RDF: {0}-{1}: Atoms: {2}".format(
                    atom_types[0].Name,
                    atom_types[1].Name,
                    ["-".join([i.Name for i in AP]) for AP in atom_pairs],
                ),
            )

        def Del_NB_APairs(atom_types, atom_pairs, line):
            atom_types = self.System._GetAtomTypesPair(atom_types, line)
            atom_pairs = _clean_atoms_container(atom_pairs, line, 2, "AtomGroups")
            # Check if RDF with Types ATypes already exists
            rdflst = [
                rdf
                for rdf in self.RDFs_NB
                if (set(rdf.AtomTypes) == set([at.Name for at in atom_types]))
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one NB RDF with types {[AT.Name for AT in atom_types]} found: ",
                )
            if len(rdflst) == 0:  # if we found no RDF
                print(
                    f"Warning: No NB-RDF with types {[AT.Name for AT in atom_types]} found: Nothing to delete, no action taken.",
                )
            elif len(rdflst) == 1:
                trdf = rdflst[0]
                # Find pairs in the RDF
                for atom_pair in atom_pairs:
                    aplist = [
                        AP for AP in trdf._AtomGroups_ if set(atom_pair) == set(AP)
                    ]
                    if len(aplist) > 0:
                        for ap_ in aplist:
                            trdf._AtomGroups_.remove(ap_)
                    else:
                        print(
                            f"Warning: No atom pair {[atom_pair[0].Name, atom_pair[1].Name]} found in the rdf: Nothing to delete, no action taken.",
                        )
                if len(trdf._AtomGroups_) == 0:
                    self.RDFs.remove(trdf)
                print(
                    "Removed pairs from NB RDF: {0}-{1}: Atoms: {2}".format(
                        atom_types[0].Name,
                        atom_types[1].Name,
                        ["-".join([i.Name for i in AP]) for AP in atom_pairs],
                    ),
                )

        def Add_NB_ATypes(atom_types, line):
            atom_types = self.System._GetAtomTypesPair(atom_types, line)
            # Generate list of pairs

            # make set of atom_pairs (each pair is sorted, so atom1.ID<atom2.ID) and no duplicates
            set_of_pairs = set(
                tuple(sorted([a, b], key=lambda x: x.ID))
                for a in atom_types[0].Atoms
                for b in atom_types[1].Atoms
            )
            # make list based on the set
            # TODO: Do we actually need to have these ugly list-based structures? Can't we convert them to sets?
            atom_pairs = [pair_ for pair_ in set_of_pairs]
            # Call ADD_NB_APair:
            print(
                f"Add All atom pairs to NB RDF: {atom_types[0].Name}-{atom_types[1].Name}",
            )
            Add_NB_APairs(atom_types, atom_pairs, line)

        def Del_NB_ATypes(atom_types, line):
            atom_types = self.System._GetAtomTypesPair(atom_types, line)
            rdflst = [
                rdf
                for rdf in self.RDFs_NB
                if (set(rdf.AtomTypes) == set([at.Name for at in atom_types]))
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one NB RDF with types {[AT.Name for AT in atom_types]} found: ",
                )
            if len(rdflst) == 0:  # if we found no RDF: Create a new one
                print(
                    f"Warning: No NB-RDF with types {[AT.Name for AT in atom_types]} found: Nothing to delete, no action taken.",
                )
            elif len(rdflst) == 1:
                trdf = rdflst[0]
                self.RDFs.remove(trdf)
                print(f"Removed NB RDF: {atom_types[0].Name}-{atom_types[1].Name}")

        def Add_NB_All():
            # Generate list of pairs
            lpairs = ([ia, ja] for ia in self.AtomTypes for ja in self.AtomTypes)
            # Now the identical record shall be removed from list
            ATPairs = []
            for p in lpairs:
                if set(p) not in [set(AP) for AP in ATPairs]:
                    ATPairs.append(p)
            # Call Add_NB_AType for each pair
            print("Add All possible NB RDFs:")
            for p in ATPairs:
                Add_NB_ATypes(p, None)

                # Detecting lines

        print("\nReading NB-RDF section")
        iNBStart, iNBEnd = _check_tags("RDFSNB", all_lines)
        lines = all_lines[iNBStart + 1 : iNBEnd]

        for l in lines:
            action = l.split(":")[0].strip()
            if action.upper() not in ["ADD", "DEL"]:
                raise MTE.RDFReadError(
                    f"Unknown command in NB-RDF definition. Line:{l}",
                )

            if len(l.split(":")) > 1:
                if len(l.split(":")) == 2:  # 3 Separators - All or AtomTypes
                    if l.split(":")[1].strip().upper() == "ALL":
                        if action.upper() == "ADD":
                            Add_NB_All()
                    else:  # AtomTypes
                        ATypes = l.split(":")[1].replace(" ", "").split("--")
                        if action.upper() == "ADD":
                            Add_NB_ATypes(ATypes, l)
                        elif action.upper() == "DEL":
                            Del_NB_ATypes(ATypes, l)
                elif len(l.split(":")) == 3:  # 3 separators - Atom Pairs
                    ATypes = l.split(":")[1].replace(" ", "").split("--")
                    APairs = [i.split() for i in l.split(":")[2].strip().split(",")]
                    if action.upper() == "ADD":
                        Add_NB_APairs(ATypes, APairs, l)
                    elif action.upper() == "DEL":
                        Del_NB_APairs(ATypes, APairs, l)
                else:  # Too many separators
                    raise MTE.RDFReadError(
                        f"Can't read AtomPairs in NB-RDF definition. Too many ':' separators. \nLine:{l}",
                    )
            else:  # Only one separator - error
                raise MTE.RDFReadError(
                    f"Can't read AtomTypes in NB-RDF definition. Line:{l}",
                )

                # Reading intramolecular Bond RDFs

        def Add_B_APairs(MType, BNumber, APairs, line):
            MType = self.System.GetMolType(MType, line)
            APairs = _clean_atoms_container(APairs, line, 2, "AtomPairs", MT=MType)
            # Check if the atoms belong to the stated Type
            for atom in [atom for atom_group in APairs for atom in atom_group]:
                assert atom in MType.Atoms, (
                    f"Error: Atom {atom.Name} have to belong to the MolType {MType.Name}, but it does not"
                )
            print(
                "Add atom pairs to B-RDF: {0}:{1}:{2}".format(
                    MType.Name,
                    BNumber,
                    ["-".join([i.Name for i in AP]) for AP in APairs],
                ),
            )
            # Check if RDF with Type and BondNumber already exist, if not we create it
            rdflst = [
                rdf
                for rdf in self.RDFs_B
                if rdf.BondNumber == BNumber and rdf.MolTypeName == MType.Name
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one B RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            if (
                len(rdflst) == 0
            ):  # if we found no RDF: Create a new bond type and new RDF
                BondType.PairBondType(MolType=MType, ID=BNumber, AtomGroups=APairs)
                trdf = DF.RDF_PairBond(
                    Name=APairs[0][0].AtomType.Name + "-" + APairs[0][1].AtomType.Name,
                    Min=0.0,
                    Max=rmaxi,
                    Npoints=int(rmaxi / resoli),
                    _AtomGroups_=[],
                    AtomGroups=[],
                    MolTypeName=MType.Name,
                    BondNumber=BNumber,
                )
                self.RDFs.append(trdf)
            elif len(rdflst) == 1:  # one RDF found -> update bond and RDF records
                print("The RDF and Bond already exist: just add extra atom pairs")
                trdf = rdflst[0]
            # At this point we only have a single RDF in the list, which already exist or just has been created.
            # Add pairs which are not present there (check for the order of pairs!)
            for ap in (
                APairs
            ):  # Here we add one pair at a time to avoid adding double records.
                if set(ap) not in [set(AP) for AP in trdf._AtomGroups_]:
                    trdf._AtomGroups_.append(ap)
                    trdf.AtomGroups.append([i.Number for i in ap])

        def Add_A_ATriplets(MType, BNumber, ATriplets, line):
            MType = self.System.GetMolType(MType, line)
            ATriplets = _clean_atoms_container(
                ATriplets,
                line,
                3,
                "AtomTriplets",
                MT=MType,
            )
            # Check that atoms in the triplet are not already bonded to each other
            for triplet_ in ATriplets:
                if triplet_[0].IsBonded(triplet_[-1]):
                    print(
                        f"Atoms {triplet_[0]}-{triplet_[2]} are already bonded: Skip them",
                    )
            ATriplets = [
                triplet_
                for triplet_ in ATriplets
                if not triplet_[0].IsBonded(triplet_[-1])
            ]

            if ATriplets == []:
                return ATriplets
            print(
                "Add atom triplets to A-RDF: {0}:{1}:{2}".format(
                    MType.Name,
                    BNumber,
                    [["-".join([i.Name for i in AP])] for AP in ATriplets],
                ),
            )

            # Check if the atoms belong to the stated Type
            for atom in [atom for atom_group in ATriplets for atom in atom_group]:
                assert atom in MType.Atoms, (
                    f"Error: Atom {atom.Name} have to belong to the MolType {MType.Name}, but it does not"
                )
            # Check if RDF with Type and BondNumber already exist, if not we create it
            rdflst = [
                rdf
                for rdf in self.ADFs
                if (
                    rdf.Type == "A"
                    and rdf.BondNumber == BNumber
                    and rdf.MolTypeName == MType.Name
                )
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one A RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            if len(rdflst) == 0:  # if we found no RDF: Create a new bond and new RDF
                BondType.AngleBondType(MolType=MType, ID=BNumber, AtomGroups=ATriplets)
                trdf = DF.RDF_AngleBond(
                    Name="-".join([i.AtomType.Name for i in ATriplets[0]]),
                    Min=0.0,
                    Max=180.0,
                    Npoints=int(180.0 / (resolphi)),
                    _AtomGroups_=[],
                    AtomGroups=[],
                    MolTypeName=MType.Name,
                    BondNumber=BNumber,
                )
                self.ADFs.append(trdf)
            elif len(rdflst) == 1:  # one RDF found -> update bond and RDF records
                trdf = rdflst[0]
                # bond = [b for b in MType.Bonds if b.ID == BNumber][0]
            # At this point we only have a single RDF in the list, which already exist or just has been created.
            # Add pairs which are not present there (check for the order of pairs!)
            for ap in (
                ATriplets
            ):  # Here we add one pair at a time to avoid adding double records.
                if ap not in trdf._AtomGroups_:
                    trdf._AtomGroups_.append(ap)
                    trdf.AtomGroups.append([i.Number for i in ap])
                    # trdf.AtomGroups.append([atom.Molecule.MolType.Atoms.index(atom)+1 for atom in ap])
            return ATriplets

        def Add_A_MTypeAll(MType, line):
            MType = self.System.GetMolType(MType, line)
            print(f"Add all possible A-RDFs in Molecule: {MType.Name}")
            CrossList = []
            for A in MType.Atoms:
                BondTypeList = [
                    (A, AG, BT.ID)
                    for BT in MType.PairBondTypes
                    for AG in BT.AtomGroups
                    if (A in AG)
                ]
                if len(BondTypeList) >= 2:  # Make cross-list
                    CrossList = CrossList + [
                        [A, [k for k in i[1] + j[1] if k != A], (i[2], j[2])]
                        for i in BondTypeList
                        for j in BondTypeList
                        if i != j and i[2] <= j[2]
                    ]

            BondTypeIDs = set([BT.ID for BT in MType.PairBondTypes])
            uBondIDPairs = [(i, j) for i in BondTypeIDs for j in BondTypeIDs if i <= j]

            iBondType = len(MType.BondTypes)
            for IDPair in uBondIDPairs:
                lTriplets = [
                    [l[1][0], l[0], l[1][1]] for l in CrossList if l[2] == IDPair
                ]
                lTriplets = [
                    l
                    for il, l in enumerate(lTriplets)
                    if all([k[0] != l[2] for ik, k in enumerate(lTriplets) if ik < il])
                ]
                if len(lTriplets) > 0:
                    iBondType += 1
                    lTriplets = Add_A_ATriplets(MType, iBondType, lTriplets, line)
                    if lTriplets != []:
                        print(
                            "Added Angle-Bond:{0} {1} {2}\n".format(
                                MType.Name,
                                iBondType,
                                ["-".join([a.Name for a in t]) for t in lTriplets],
                            ),
                        )
                    else:
                        iBondType -= 1

        def Add_A_All(line):
            print(
                f"Add all possible A-RDFs for all Molecular Types:{[MT.Name for MT in self.MolTypes]}",
            )
            for MT in self.MolTypes:
                Add_A_MTypeAll(MT, line)

        def Del_A_ATriplets(MType, BNumber, APairs, line):
            MType = self.System.GetMolType(MType, line)
            APairs = _clean_atoms_container(APairs, line, 3, "AtomTriplets")
            print(
                "Remove atom triplets {2} from Bond and A-RDF: {0}:{1}".format(
                    MType.Name,
                    BNumber,
                    [["-".join([i.Name for i in AP])] for AP in APairs],
                ),
            )

            # Check if RDF with Type and BondNumber already exist
            rdflst = [
                rdf
                for rdf in self.ADFs
                if (
                    rdf.Type == "A"
                    and rdf.BondNumber == BNumber
                    and rdf.MolTypeName == MType.Name
                )
            ]
            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one A RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            if len(rdflst) == 0:
                raise MTE.RDFReadError(
                    f"Error: No A-RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            bond_types = [BT for BT in MType.AngleBondTypes if BNumber == BT.ID]
            if len(bond_types) != 1:
                raise MTE.RDFReadError(
                    f"Error: No bond_types or more than one bond with BondNumber {BNumber} found in MolType {MType.Name}: ",
                )

            bond_type = bond_types[0]
            if (
                len(
                    [
                        AG
                        for AG in bond_type.AtomGroups
                        if (
                            ([AG[0], AG[1], AG[2]] in APairs)
                            or ([AG[2], AG[1], AG[0]] in APairs)
                        )
                    ],
                )
                == 0
            ):
                raise MTE.RDFReadError(
                    f"Error: No AtomTriplets{[[a.Name for a in AP] for AP in APairs]} found in the bond type {bond_type}: ",
                )
            bond_type.AtomGroups = [
                AG
                for AG in bond_type.AtomGroups
                if not (
                    ([AG[0], AG[1], AG[2]] in APairs)
                    or ([AG[2], AG[1], AG[0]] in APairs)
                )
            ]
            trdf = rdflst[0]
            # At this point we only have a single RDF in the list, which already exist or just has been created.
            # Add pairs which are not present there (check for the order of pairs!)
            bond_type.AtomGroups = [
                AG
                for AG in bond_type.AtomGroups
                if not (
                    ([AG[0], AG[1], AG[2]] in APairs)
                    or ([AG[2], AG[1], AG[0]] in APairs)
                )
            ]
            trdf._AtomGroups_ = [
                AG
                for AG in trdf._AtomGroups_
                if not (
                    ([AG[0], AG[1], AG[2]] in APairs)
                    or ([AG[2], AG[1], AG[0]] in APairs)
                )
            ]
            trdf.AtomGroups = [[i.Number for i in AG] for AG in trdf._AtomGroups_]

            if len(bond_type.AtomGroups) == 0:
                print(
                    f"No more atom triplets left in A-BondType {bond_type} - Remove it",
                )
                bond_type._delete()
            if len(trdf.AtomGroups) == 0:
                print(
                    f"No more atom triplets left in A-RDF {MType.Name}{BNumber} - Remove it",
                )
                self.ADFs.remove(trdf)

        def Del_A_BondNumber(MType, BNumber, line):
            MType = self.System.GetMolType(MType, line)
            print(f"Remove bond and A-RDF from Moltype:{MType.Name} Bond:{BNumber}")
            rdflst = [
                rdf
                for rdf in self.ADFs
                if (
                    rdf.Type == "A"
                    and rdf.BondNumber == BNumber
                    and rdf.MolTypeName == MType.Name
                )
            ]

            if len(rdflst) > 1:  # if we found more than one RDF:
                raise MTE.RDFReadError(
                    f"Error: More than one A RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            if len(rdflst) == 0:  # if we found no RDF: Throw exception
                raise MTE.RDFReadError(
                    f"Error: No A-RDF with MolType {MType.Name} and BondNumber {BNumber} found: ",
                )
            bond_types = [BT for BT in MType.AngleBondTypes if BNumber == BT.ID]
            if len(bond_types) != 1:
                raise MTE.RDFReadError(
                    f"Error: No bond_types or more than one bond with BondNumber {BNumber} found in MolType {MType.Name}: ",
                )
            bond_types[0]._delete()
            self.ADFs.remove(rdflst[0])

        def Del_A_MTypeAll(MType, line):
            MType = self.System.GetMolType(MType, line)
            print(f"Remove all A-bond types and A-RDFs from MolType:{MType.Name}")
            for i in [BT.ID for BT in MType.AngleBondTypes]:
                Del_A_BondNumber(MType, i, line)

                # ----------------------------------------------------------------------------

        print("\nReading pairwise Bond-RDF section")
        iBStart, iBEnd = _check_tags("RDFSB", all_lines)
        lines = all_lines[iBStart + 1 : iBEnd]

        for l in lines:
            action = l.split(":")[0].strip()
            if action.upper() not in ["ADD"]:
                raise MTE.RDFReadError(
                    "Unknown command in B-RDF definition. "
                    f"Only Add:MolType:N_Bond: A1 A2, A2 A3 are supported \nLine:{l}",
                )

            if len(l.split(":")) == 4:
                BMType = l.split(":")[
                    1
                ].strip()  # Name of moleular type the bond belongs to
                try:
                    BNumber = int(l.split(":")[2].strip())
                except:
                    raise MTE.RDFReadError(
                        f"Can not read bond number in B-RDF definition. Line:{l}",
                    )
                APairs = [i.split() for i in l.split(":")[3].strip().split(",")]
                Add_B_APairs(BMType, BNumber, APairs, l)
            else:  # Only one separator - error
                raise MTE.RDFReadError(f"Can't read B-RDF definition. Line:{l}")

        print("\nReading angle bending Bond-RDF section")
        iBStart, iBEnd = _check_tags("RDFSA", all_lines)
        lines = all_lines[iBStart + 1 : iBEnd]

        for l in lines:
            splt = l.split(":")
            if len(splt) == 1:
                raise MTE.RDFReadError(f"Unknown command in A-RDF definition. Line:{l}")
            # len >1
            action = splt[0].strip().upper()
            if action not in ["ADD", "DEL"]:
                raise MTE.RDFReadError(f"Unknown command in A-RDF definition. Line:{l}")
            mol_types = splt[1].strip()

            if (action) == "ADD" and mol_types.upper() == "ALL":
                Add_A_All(l)
            else:
                BNumber = splt[2].strip()
                if BNumber.upper() == "ALL":
                    if action == "ADD":
                        Add_A_MTypeAll(mol_types, l)
                    if action == "DEL":
                        Del_A_MTypeAll(mol_types, l)
                else:
                    try:
                        BNumber = int(BNumber)
                    except:
                        raise MTE.RDFReadError(
                            f"Can not read bond number in A-RDF definition. Line:{l}",
                        )
                    if len(splt) == 3 and action == "DEL":
                        Del_A_BondNumber(mol_types, BNumber, l)
                    elif len(splt) == 4:
                        ATriplets = [i.split() for i in splt[3].strip().split(",")]
                        if action == "ADD":
                            Add_A_ATriplets(mol_types, BNumber, ATriplets, l)
                        if action == "DEL":
                            Del_A_ATriplets(mol_types, BNumber, ATriplets, l)

            if len(splt) > 4:  # Too many separators
                raise MTE.RDFReadError(
                    f"Can't read AtomPairs in A-RDF definition. Too many ':' separators. \nLine:{l}",
                )

        self.DFset = DFset.DFset(
            Name=None,
            AtomTypes=[i.Name for i in self.AtomTypes],
            Min=0,
            Max=rmax,
            Npoints=int(rmax / resol),
            DFs=self.RDFs + self.ADFs,
            NPairBondsExclude={
                str(moltype_): self.exclusions_B[moltype_]
                for moltype_ in self.System.MolTypes
            },
            NAngleBondsExclude={
                str(moltype_): self.exclusions_A[moltype_]
                for moltype_ in self.System.MolTypes
            },
            check=False,
        )
        print(
            "\n Reindex all the B- and A- bond types in the system, to keep consistency in case "
            "if some automatically generated bond types were deleted.",
        )
        for MT in self.MolTypes:
            DFsetBA = [iDF for iDF in self.DFset if iDF.Type != "NB"]
            Bs = [iDF for iDF in DFsetBA if iDF.MolTypeName == MT.Name]
            for B in Bs:
                B.BondNumber = Bs.index(B) + 1

        print("\nSUMMARY: Following RDFs will be generated:")
        print("NB-RDFs:")
        for rec in [
            " : ".join(
                [
                    RDF.Name,
                    ", ".join(
                        [
                            " ".join([atom_type.Name for atom_type in AG])
                            for AG in RDF._AtomGroups_
                        ],
                    ),
                ],
            )
            for RDF in self.DFset.DFs_NB
        ]:
            print(rec)

        print("\nB-RDFs:")
        for rec in [
            " : ".join(
                [
                    RDF.MolTypeName,
                    str(RDF.BondNumber),
                    ", ".join(
                        [
                            " ".join([atom_type.Name for atom_type in AG])
                            for AG in RDF._AtomGroups_
                        ],
                    ),
                ],
            )
            for RDF in self.DFset.DFs_B
        ]:
            print(rec)

        print("\nA-RDFs:")
        for rec in [
            " : ".join(
                [
                    RDF.MolTypeName,
                    str(RDF.BondNumber),
                    ", ".join(
                        [
                            " ".join([atom_type.Name for atom_type in AG])
                            for AG in RDF._AtomGroups_
                        ],
                    ),
                ],
            )
            for RDF in self.DFset.DFs_A
        ]:
            print(rec)

        self.__read_input_sameasbond(all_lines)
        if not self.__skip_trj_check__:
            self._check_atom_names_trajectory()

    def __read_input_sameasbond(self, all_lines):
        print("\nReading SameAsBond section")
        iNBStart, iNBEnd = _check_tags("SAMEASBOND", all_lines, must_be_present=False)
        lines = all_lines[iNBStart + 1 : iNBEnd]

        def __parse_record(line_):
            before_eq, after_eq = [l_.strip() for l_ in line_.split("=")]
            ref_bond = self.System.GetBondType(before_eq)
            linked_bonds = [
                self.System.GetBondType(str_) for str_ in after_eq.split(",")
            ]
            return ref_bond, linked_bonds

        def __get_df_for_bond(bond_, dfset_):
            list_ = [
                df_
                for df_ in (self.DFset.DFs_A + self.DFset.DFs_B)
                if (df_.MolTypeName == bond_.MolType.Name)
                and (df_.BondNumber == bond_.Number)
            ]
            assert len(list_) > 0, (
                "Can not find a Bond_RDF corresponding to " + bond_fmt.format(bond_)
            )
            assert len(list_) == 1, (
                "Found more than one Bond_RDF corresponding to "
                + bond_fmt.format(bond_)
            )
            return list_[0]

        self.__ref2linked = dict()

        if lines != []:  # if there are records
            for line_ in lines:
                ref_bond, linked_bonds = __parse_record(line_)
                assert len(linked_bonds) == len(set(linked_bonds)), (
                    "Non-unique bond-records in line " + line_
                )
                self.__ref2linked[ref_bond] = linked_bonds
        for ref_bond in self.__ref2linked.keys():
            if (
                self.__ref2linked[ref_bond].count(ref_bond) != 0
            ):  # The bond is present both in ref and linked
                self.__ref2linked[ref_bond].remove(ref_bond)

        print(f"{len(self.__ref2linked)} SameAsBond records found:")
        bond_fmt = "{0.MolType.Name}:{0.Number}"
        for ref_, linked_ in self.__ref2linked.items():
            print(
                bond_fmt.format(ref_)
                + "="
                + ", ".join([bond_fmt.format(bond_) for bond_ in linked_]),
            )

        print("Linking distributions corresponding to the SameAs records")
        self.__refdf2linkeddf = dict()
        for ref_bond, linked_bonds in self.__ref2linked.items():
            ref_df = __get_df_for_bond(ref_bond, self.DFset)
            self.__refdf2linkeddf[ref_df] = []
            for bond_ in linked_bonds:
                linked_df = __get_df_for_bond(bond_, self.DFset)
                # put SameAs record in the DFs
                linked_df.SameAsBond = bond_fmt.format(ref_bond)
                self.__refdf2linkeddf[ref_df].append(linked_df)

    def _write_exclusions_to_file(self, exclfile="exclusions.dat"):
        with open(exclfile, "w") as ofile:
            ofile.writelines([l_ + "\n" for l_ in self.DFset._get_exclusions_records()])
            for i_atom, atom_key in enumerate(self.System.Sites):
                atoms_val = self.exclusions[atom_key]
                ofile.write(
                    "{0}:{1}\n".format(
                        atom_key.ID,
                        ",".join(
                            [
                                str(atom_.ID)
                                for atom_ in sorted(atoms_val, key=lambda x: x.ID)
                            ],
                        ),
                    ),
                )

    def _make_prefix(self):
        self._prefix = {
            mt: sum(
                [
                    mol_type._nmol * len(mol_type.Atoms)
                    for mol_type in self.System.MolTypes[0:i_mt]
                ],
            )
            for i_mt, mt in enumerate(self.System.MolTypes)
        }

    def _create_RDF_NB_pairs_matrix(self):
        # Creating list of pairs from configurations using the generator below. Speeds up the code execution
        # for moderate size systems
        for rdf in self.DFset.DFs_NB:
            rdf._pairslist = [
                np.concatenate(list(self._RDF_NB_pairs_matrix_generator(rdf)), axis=1),
            ]

    # @profile
    def _RDF_NB_pairs_matrix_generator(self, rdf):
        # Generate list of pairs from configuration to be analyzed for certain RDF
        _cache_moltype_atoms = {
            moltype_: moltype_.NAtoms for moltype_ in self.System.MolTypes
        }

        for atom1, atom2 in rdf._AtomGroups_:  # Over all pairs of atoms of the RDF
            moltype1, moltype2 = atom1.Molecule.MolType, atom2.Molecule.MolType
            moltype1_natoms = _cache_moltype_atoms[moltype1]
            moltype2_natoms = _cache_moltype_atoms[moltype2]
            a_array = (
                np.arange(0, moltype1._nmol) * moltype1_natoms
                + self._prefix[moltype1]
                + atom1.Number
                - 1
            )
            b_array = (
                np.arange(0, moltype2._nmol) * moltype2_natoms
                + self._prefix[moltype2]
                + atom2.Number
                - 1
            )
            a_x_b = np.array(
                np.meshgrid(a_array, b_array, indexing="ij"),
                dtype=np.uint16,
            ).T
            if atom1 == atom2:  # same atoms
                a_x_b = a_x_b[
                    np.invert(
                        np.triu(np.ones((moltype1._nmol, moltype1._nmol), dtype=bool)),
                    )
                ]  # avoid duplicates
            elif (
                atom2 in self.exclusions[atom1] or atom1 in self.exclusions[atom2]
            ):  # excluded pair of atoms
                a_x_b = a_x_b[np.invert(np.eye(moltype1._nmol, dtype=bool))]
            a_x_b = a_x_b.reshape(-1, 2)
            a_x_b.sort()  # sort the inner pairs
            yield a_x_b.T

    def _create_Pair_RDF_pairs_matrix(self):
        for rdf in self.DFset.DFs_B:
            list_ = []

            for atom_pair in rdf._AtomGroups_:  # Over all pairs of atoms of the RDF
                moltype1, moltype2 = [a_.Molecule.MolType for a_ in atom_pair]
                if moltype1 != moltype2:
                    raise MTE.RDFCalculatorError(
                        f"intramolecular RDF:{self.DFset.DFs.index(rdf)} has atoms which belong to different molecular types",
                    )

                # Loop over all molecules of moltype1
                _arrays = [
                    np.arange(0, moltype1._nmol) * moltype1.NAtoms
                    + atom.Number
                    - 1
                    + self._prefix[moltype1]
                    for atom in atom_pair
                ]
                list_.append(np.stack(_arrays, axis=1))
            rdf._pairslist = [
                np.concatenate(list_, axis=0).T,
            ]  # incapsulated in the list, to mimick chunked structure as in NB-pairslists

    def _create_ADF_pairs_matrix(self):
        for adf in self.ADFs:
            if adf.Type == "A":  # intramolecular ADF
                list_ = []
                for (
                    atom_triplet
                ) in adf._AtomGroups_:  # Over all triplets of atoms of the ADF
                    for i, atom in enumerate(atom_triplet):
                        atom_count = int(
                            sum(
                                [
                                    mol_type.Atoms.count(atom)
                                    for mol_type in self.MolTypes
                                ],
                            ),
                        )
                        if atom_count != 1:
                            raise MTE.RDFCalculatorError(
                                f"atom {i} of triplet is presented in {atom_count} moltypes\n",
                            )
                    moltype1, moltype2, moltype3 = tuple(
                        [atom.Molecule.MolType for atom in atom_triplet],
                    )
                    if any(
                        [
                            moltype_ != moltype1
                            for moltype_ in (moltype1, moltype2, moltype3)
                        ],
                    ):
                        raise MTE.RDFCalculatorError(
                            f"intramolecular ADF:{self.ADFs.index(adf)} has atoms which belong to different molecular types",
                        )

                    # Loop over all molecules of moltype1
                    _arrays = [
                        np.arange(0, moltype1._nmol) * moltype1.NAtoms
                        + atom.Number
                        - 1
                        + self._prefix[moltype1]
                        for atom in atom_triplet
                    ]
                    list_.append(np.stack(_arrays, axis=1))
                adf._pairslist = np.concatenate(list_, axis=0).T

    def create_DFs_pairs_matrixes(self):
        self._make_prefix()
        self.exclusions = self.System._create_excluded_atom_pairs_list(
            exclusions_A=self.exclusions_A,
            exclusions_B=self.exclusions_B,
        )
        self._write_exclusions_to_file(exclfile=self.__exclusions_file)
        if not self._opt_memory_use:
            self._create_RDF_NB_pairs_matrix()
        self._create_Pair_RDF_pairs_matrix()
        self._create_ADF_pairs_matrix()

    def RDFs_Accumulate(self):
        RDFs_ = self.DFset.DFs_NB + self.DFset.DFs_B
        if len(RDFs_) > 0:
            # Loop over trajectory configurations, counting pairs
            self.Trajectory.GetAtomNames()

            self.Trajectory.Connect(restart=True)
            eof = self.Trajectory.ReadConf()
            for rdf in RDFs_:
                rdf._ghist = np.zeros(len(rdf._ghist))
            box_ac = np.zeros(3, dtype=float)
            if self.Trajectory.box is not None:
                box = self.Trajectory.box
            elif self.Box is not None:
                box = self.Box
            else:
                raise MTE.RDFCalculatorError(
                    "Error: Periodic box size is not provided neither in the input file nor in the trajectory.",
                )
            self._conf_count = 0

            while eof == 0:
                box_ac += box
                for rdf in RDFs_:
                    c = self.Trajectory.conf
                    if self._opt_memory_use and isinstance(rdf, DF.RDF_NB):
                        rdf._pairslist = self._RDF_NB_pairs_matrix_generator(rdf)
                    for chunk_ in rdf._pairslist:
                        dr = c[chunk_[1]] - c[chunk_[0]]
                        dr = np.abs(dr)
                        if isinstance(rdf, DF.RDF_NB):
                            dr = np.abs(dr - np.round(np.divide(dr, box), 0) * box)
                        drr = np.sqrt(np.sum(np.square(dr), axis=1))
                        drr[drr < rdf.Min] = 0.0
                        drr[drr >= rdf.Max] = 0.0
                        i = (drr / rdf.Resol).astype(int)
                        rdf._ghist += np.bincount(i, minlength=len(rdf._ghist))[
                            0 : len(rdf._ghist)
                        ]
                print(f"Configuration: {self._conf_count} analyzed", end="\r")

                eof = self.Trajectory.ReadConf()
                if self.Trajectory.box is not None:
                    box = self.Trajectory.box
                self._conf_count += 1
            print("\n")
            if self._conf_count > 0:
                box_ac = box_ac / self._conf_count
            else:
                raise MTE.RDFCalculatorError(
                    "No configurations were analyzed during RDF calculation! Check your settings",
                )
            print("\n")
            if np.any(self.Box != box_ac):
                print(
                    f"Box stated in input: {self.Box} does not agree with trajectory averaged value {box_ac}.\n"
                    "The program continues with averaged box size",
                )
                self.Box = box_ac

    def ADFs_Accumulate(self):
        if len(self.DFset.DFs_A) > 0:
            # self.Create_ADF_pairs_matrix()  # Create matrix of triplets for ADFs
            for adf in self.DFset.DFs_A:
                adf._ghist = np.zeros(len(adf._ghist))
            self.Trajectory.Connect(restart=True)
            eof = self.Trajectory.ReadConf()
            conf = 1
            while eof == 0:
                for adf in self.DFset.DFs_A:
                    c = self.Trajectory.conf
                    r21 = c[adf._pairslist[1]] - c[adf._pairslist[0]]
                    r23 = c[adf._pairslist[1]] - c[adf._pairslist[2]]
                    cosphi = np.sum(np.multiply(r21, r23), axis=1) / np.sqrt(
                        np.sum(np.multiply(r21, r21), axis=1)
                        * np.sum(np.multiply(r23, r23), axis=1),
                    )
                    cosphi = np.where(
                        np.abs(cosphi) > 1.0,
                        np.sign(cosphi),
                        cosphi,
                    )  # to avoid numerical errors when cosphi>1.0 due to rounding errors
                    phi = np.arccos(cosphi) * 179.9999 / np.pi
                    i = ((phi) / adf.Resol).astype(int)
                    adf._ghist += np.bincount(i, minlength=len(adf._ghist))
                print(f"Configuration: {self._conf_count} analyzed", end="\r")
                eof = self.Trajectory.ReadConf()
                conf += 1
            print("\n")

    def _gather_sameasbonds_hist(self):
        """Merge histograms collected for all bonds which suppose to be the same."""
        for df_ref, dfs_linked in self.__refdf2linkeddf.items():
            ghist_sum = np.sum([df_._ghist for df_ in dfs_linked + [df_ref]], axis=0)
            df_ref._ghist = ghist_sum

    def _broadcast_sameasbonds_rdf(self):
        for df_ref, dfs_linked in self.__refdf2linkeddf.items():
            for df_ in dfs_linked:
                df_.g = df_ref.g

    def _check_atom_names_trajectory(self):
        """Check consistency of atom names in the system and in the trajectory."""
        atoms_trj = self.Trajectory.GetAtomNames()
        atoms_system = [
            name_
            for moltype in self.System.MolTypes
            for name_ in [atom.Name for atom in moltype.Atoms] * moltype._nmol
        ]
        if atoms_trj is None:
            print(
                "Warning!!! Can not read atom-names from this trajectory file. Proceed as is.",
            )
            return
        for i, (atom_trj, atom_system) in enumerate(zip(atoms_trj, atoms_system)):
            if atom_trj != atom_system:
                print(
                    f"""Error in trajectory: atom names are not consistent: between system and trajectory
Atom: {i + 1}, Name in system {atom_system} in trajectory {atom_trj}
Check your input
To skip this check (i.e. if you are using LAMMPS-trajectory) run rdf.py --force""",
                )
                raise (
                    ValueError(
                        "Error in the trajectory: atom names are not consistent:",
                    )
                )
        return

    def Normalize(self, DFs):
        if len(self.Box) == 3:
            vol = self.Box.prod()
        else:
            vol = 1.0
        for df in DFs:
            df.Normalize(vol)

    def Smooth(self, DFs):
        for df in DFs:
            df.Smooth()

    def Trim(self, DFs, tolerance=None):
        for df in DFs:
            df.Trim(tolerance=tolerance)

    def DFs_SaveForMagic(self):
        if self.DFset.DFs_NB == []:
            raise MTE.RDFError("Error: No intermolecular RDF calculated:")
        try:
            self.DFset.Write(self.__rdf_output_file)
        except MTE.RDFError:
            raise MTE.RDFError(
                "Error:Unable to write RDF output file:" + self.__rdf_output_file,
            )

    def Calculate(self, tolerance=(None, None), smooth=True, trim=True, nProc=0):
        if nProc == 0:
            self.RDFs_Accumulate()
            self.ADFs_Accumulate()
        else:
            self.RDFs_Accumulate_Parallel(nProc)
            self.ADFs_Accumulate_Parallel(nProc)
        self._gather_sameasbonds_hist()
        self.Normalize(self.DFset.DFs)
        if smooth:
            self.Smooth(self.DFset.DFs)
        if trim:
            self.Trim(self.DFset.DFs_NB + self.DFset.DFs_B, tolerance=tolerance[0])
            self.Trim(self.DFset.DFs_A, tolerance=tolerance[1])
        self.DFset.reNormalize()

        self._broadcast_sameasbonds_rdf()

    def WriteBox(self):
        """Write periodic box dimentions at the end of the RDF file."""
        if len(self.Box) > 0:
            print(f"Box size: {self.Box[0]} {self.Box[1]} {self.Box[2]}")
            with open(self.__rdf_output_file, "a") as ofile:
                ofile.write(
                    f"Box size: {self.Box[0]:8.4f} {self.Box[1]:8.4f} {self.Box[2]:8.4f} A\n",
                )

    def RDFs_Accumulate_Parallel(self, Np):
        if len(self.DFset.DFs) > 0:
            import multiprocessing

            import DFs_Accumulator_Process

            Trajectories = self.Trajectory.Split(Np)
            queue = multiprocessing.Queue(maxsize=Np)
            self.__processes = [
                DFs_Accumulator_Process.RDFs_Accumulator_Process(
                    T,
                    self.DFset.DFs_NB + self.DFset.DFs_B,
                    iNP,
                    queue,
                    RDFcalculator=self,
                    Box=self.Box,
                )
                for iNP, T in enumerate(Trajectories)
            ]
            for p in self.__processes:
                p.start()
            results = [queue.get() for p in self.__processes]  # get results
            for p in self.__processes:
                p.join()

            # reduce results
            for irdf, RDF in enumerate(self.DFset.DFs_NB + self.DFset.DFs_B):
                RDF._ghist = RDF._ghist + np.sum([p[0][irdf] for p in results], axis=0)

            box_ac = np.sum((p[1] for p in results), axis=0)
            conf = np.sum(p[2] for p in results)
            box_ac = box_ac / float(conf)
            print(
                f"RDF histogram accumulation: Analyzed {conf} configurations in total\n",
            )
            if np.any(self.Box != box_ac):
                print(
                    f"Box stated in the input: {self.Box} does not agree with trajectory averaged value {box_ac}.\n"
                    "The program continues with the averaged box size",
                )
                self.Box = box_ac

    def ADFs_Accumulate_Parallel(self, Np):
        if len(self.ADFs) > 0:
            import multiprocessing

            import DFs_Accumulator_Process

            for adf in self.ADFs:
                adf._ghist = np.zeros(len(adf._ghist))

            Trajectories = self.Trajectory.Split(Np)
            queue = multiprocessing.Queue(maxsize=Np)
            self.__processes = [
                DFs_Accumulator_Process.ADFs_Accumulator_Process(
                    T,
                    self.ADFs,
                    iNP,
                    queue,
                )
                for iNP, T in enumerate(Trajectories)
            ]
            for p in self.__processes:
                p.start()
            results = [queue.get() for p in self.__processes]  # get results
            for p in self.__processes:
                p.join()

            # reduce results
            for iadf, ADF in enumerate(self.ADFs):
                ADF._ghist = ADF._ghist + np.sum([p[0][iadf] for p in results], axis=0)
            conf = np.sum(p[1] for p in results)
            print(
                f"ADF histogram accumulation: Analyzed {conf} configurations in total",
            )


def main():
    """Main entry point for the RDF calculator command-line interface."""
    import logging

    logging.basicConfig(filename="rdf.err", level=logging.DEBUG)

    try:
        # Reading the command line arguments
        input_file_type = None
        parallel = False
        np_ = 0  # default
        input_file_name = "rdf.inp"
        skip_trj_check = False
        trim = True
        opt_memory_use = False
        while len(sys.argv) > 1:
            option = sys.argv[1]
            del sys.argv[1]
            if option == "-i":
                input_file_name = sys.argv[1]
                del sys.argv[1]
            elif option == "-np":
                parallel = True
                np_ = int(sys.argv[1])
                del sys.argv[1]
                print(f"run parallel on {np_} cores")
            elif option == "--force":
                skip_trj_check = True
            elif option == "--opt_memory_use":
                opt_memory_use = True
            elif option == "--notrim":
                trim = True
            else:
                print("invalid input parameter:" + option)
                raise MTE.GeneralError
        # Checking if all important input parameters are read.
        print("Opening input file:" + input_file_name)
        # Here we create "RDFCalculator" object
        calculator = RDFCalculator(
            input_file_name,
            skip_trj_check=skip_trj_check,
            opt_memory_use=opt_memory_use,
        )
        e0 = time.time()
        c0 = time.process_time()
        calculator.create_DFs_pairs_matrixes()  # Create matrix of pairs for RDFs
        calculator.Calculate(
            smooth=True,
            trim=trim,
            nProc=np_,
        )  # , tolerance=(1.0e-3, 1.0e-5))
        calculator.DFs_SaveForMagic()
        calculator.System.WriteMCMs()
        calculator.WriteBox()
        print(f"Elasped time:{time.time() - e0}, CPU time:{time.process_time() - c0}")

    except MTE.GeneralError:
        logging.exception("Got exception on main handler")
        print("Error Happened while executing the code, see traceback in rdf.err")
        print(" magic-rdf -i input.inp [-np Nproc] [--force]")


# Script executing RDF calculation class
if __name__ == "__main__":
    main()
