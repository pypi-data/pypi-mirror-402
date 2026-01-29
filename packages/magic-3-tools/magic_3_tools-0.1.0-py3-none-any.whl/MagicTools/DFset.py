from collections import defaultdict
from collections.abc import Iterable

from . import DF
from . import MTException as MTE
from .object_magictools import ObjectMagicTools


class DFset(ObjectMagicTools):
    """Class representing a set of Distribution Functions (RDF, Potential, Potential correction, etc.).

    Properties:
        Name: Name of the set (will be used for legend and title generation when plotting)
        NTypes: Number of different atom types used in the set
        AtomTypes: Names of the atom types involved in the set
        Min, Max: Range of distances for non-bonded interaction functions ()
        Npoints: Number of points in non-bonded interaction functions
        DFs: List of functions (all functions) in the set
        DFs_NB: List of functions representing non-bonded interactions
        DFs_B: List of functions representing pairwise bond interactions
        DFs_A: List of functions representing angle-bending bond interactions
        NPairBondsExclude, NAngleBondsExclude: two dictionaries defining exclusions for molecular types involved in the DFset

    Methods Overview:
        DFset(): Construct the object from provided rdf/pot file (recommended way) or from the provided parameters
        Write(): Write the set of functions to the file.
        Plot(): Plot the set of functions
        Reduce(): Compare the set to the provided one and extract similar functions. Useful to extract functions related to one molecule from larger set of functions.
        SetTitle(): Set title for the DFset and for every DF of the set to have nice legends in massive plots
        AddCore(): Add repulsive core to the Non-bonded potentials and sets Rmin=0
        CutTail(RcutNB): Shorten the range of NB potentials in the set to RcutNB
        ChangeResolution(NewResol): Changes resolution of the set. NewResol - tuple of 3 values (NB, B, A).
        ExtendRange(RcutNB): Extend the range of NB potentials in the set to RcutNB
        SetPlotProperty(key,value): Set plot-related keyword property for the DFset and for every DF of the set.
            Used for fine control of the pictures in massive plots

    """

    def __init__(
        self,
        File=None,
        Name=None,
        AtomTypes=None,
        Min=None,
        Max=None,
        Npoints=None,
        DFs=None,
        Ucut=None,
        NPairBondsExclude=None,
        NAngleBondsExclude=None,
        quiet=False,
        check=False,
    ):
        super(DFset, self).__init__()
        self.NPairBondsExclude = NPairBondsExclude
        self.NAngleBondsExclude = NAngleBondsExclude
        self.Name = Name
        if File:
            self.__init_from_file(File, Ucut=Ucut, quiet=quiet)
        else:
            if AtomTypes:
                self.AtomTypes = AtomTypes
            else:

                def uniq(seq):
                    # order preserving
                    noDupes = []
                    [noDupes.append(i) for i in seq if not noDupes.count(i)]
                    return noDupes

                self.AtomTypes = uniq(
                    list(
                        [at for _DF in DFs if _DF.Type == "NB" for at in _DF.AtomTypes],
                    ),
                )
            self.NTypes = len(self.AtomTypes)
            self.Min = Min
            self.Max = Max
            self.Npoints = Npoints
            self.DFs = DFs
        for df_ in self.DFs:
            df_.DFset = self

        # Sanity check for Bond-RDFs
        if check:
            for rdf_ in self.DFs_BA:
                if isinstance(rdf_, DF.RDF):
                    if abs(rdf_.y.sum() * rdf_.Resol - 1.0) > 1e-3:
                        print(
                            f"WARNING!: RDF in {rdf_.FullName} is normalized to {rdf_.y.sum() * rdf_.Resol} instead of 1.0. Check the input file",
                        )
                        print("""
                        To correct the error, read the DFset using check=False, and then call reNormalize()
                        Example: 
                        rdf = MT.ReadRDF('somefile.rdf', check=False)
                        rdf.reNormalize()
                        """)
                        raise Exception

    @property
    def DFs_NB(self):
        """Return List of Non-Bonded DFs."""
        return [x for x in self.DFs if x.Type == "NB"]

    @property
    def DFs_B(self):
        """Return List of PairwiseBond-DFs."""
        return [x for x in self.DFs if x.Type == "B"]

    @property
    def DFs_A(self):
        """Return List of AngleBond-DFs."""
        return [x for x in self.DFs if x.Type == "A"]

    @property
    def DFs_BA(self):
        """Return List of bond-DFs both Pairwise and Angular."""
        return self.DFs_B + self.DFs_A

    @property
    def N_NB(self):
        return len(self.DFs_NB)

    @property
    def N_B(self):
        return len(self.DFs_B)

    @property
    def N_A(self):
        return len(self.DFs_A)

    def __getitem__(self, i):
        return self.DFs[i]

    def __len__(self):
        return len(self.DFs)

    def __has_similar(self, DF):
        """Check if the set has similar function to the given."""
        return any([DF.IsSimilar(df) for df in self.DFs])

    def __get_similar(self, DF):
        """Return a function similar to the given one from the DFset."""
        if self.__has_similar(DF):
            return [df for df in self.DFs if DF.IsSimilar(df)][0]
        return None

    @staticmethod
    def _read_prop(name, lines, must=True):
        """Read property in format NAME = value from text-file given as list of strings:
        name - name of the property
        must - throw exception if property was not found
        """
        import re

        value = [x for x in lines if re.search("^ *" + name + " *=", x, re.IGNORECASE)]
        if len(value) > 0:
            return value[0].split("=")[1].strip()
        if must:
            raise MTE.DFsetError("Error: No " + name + " value provided")
        return None

    @staticmethod
    def _parse_exclusions(str_):
        """Read exclusions from a given string.

        Returns: defaultdict[MolTypeName] = N_Excuded_Neighbours. Default value = 1
        """
        _exc_dict = defaultdict(lambda: 1)
        if str_ is not None:
            for rec_ in str_.replace(" ", "").split(","):
                assert rec_.count(":") == 1, (
                    f'Wrong number of ":" symbols in record {rec_}. Must be exactly 1'
                )
                k_, v_ = rec_.split(":")
                _exc_dict[k_] = int(v_)
        return _exc_dict

    def __init_from_file(self, File, Ucut=None, quiet=False):
        """Init a set of Distribution Functions (RDF,ADF,Potential) from the given rdf or potential file.

        Ucut - optional parameter - where to cut prohibiting high part of the potnetial.
        """
        kind = None
        # Stage 1. Read, clean and check
        ifile = open(File)
        lines = ifile.readlines()
        ifile.close()

        # 1.1 Clean lines from comments and leading spaces, convert all to uppercase
        def CleanAndUp(s):
            s = s.strip()
            if s.startswith("&") and "=" not in s:
                s = s.upper()
            if "=" in s:
                ss = s.split("=")
                ss[0] = ss[0].upper()
                s = "=".join(ss)
            return s

        lines = list(map(CleanAndUp, lines))
        lines = [s for s in lines if (s != "" and (s[0] != "!") and (s[0] != "#"))]

        # 1.2 Check for header tags, detect Kind
        # Check that either RDF or Potentials are present in the file
        if (lines.count("&POTENTIAL") > 0) & (lines.count("&RDF") > 0):
            raise MTE.DFsetError(
                "Error: Both &POTENTIAL and &RDF headers found in the file",
            )

        def checktags(knd, lines):
            if lines.count("&" + knd) > 0:
                return knd
            if lines.count("&END" + knd) != lines.count("&" + knd):
                raise MTE.DFsetError(
                    "Error: Uneven number of "
                    + knd
                    + " and &END"
                    + knd
                    + " tags in the file",
                )

        kind = [
            checktags(x, lines) for x in ("RDF", "POTENTIAL") if checktags(x, lines)
        ]
        if len(kind) != 1:
            raise MTE.DFsetError(
                "Can not detect what kind of function the file contains: Check the presence of "
                "&RDF or &POTENTIAL sections. Convert old rdf/potential file to the "
                "new format if neccessary.",
            )
        kind = kind[0]
        # Stage 2. Read General block
        # Check presence of the block
        knd = "GENERAL"
        if lines[0] == "&" + knd:
            if lines.count("&" + knd) > 1:
                raise MTE.DFsetError("too many &" + knd + " tags in lines")
            if lines.count("&END" + knd) != 1:
                raise MTE.DFsetError(
                    "too many or too few &END" + knd + " tags in lines",
                )

        N_NB = int(self._read_prop("N_NB", lines, must=True))
        N_B = int(self._read_prop("N_B", lines, must=True))
        N_A = int(self._read_prop("N_A", lines, must=True))
        self.Min = float(self._read_prop("MIN", lines, must=True))
        self.Max = float(self._read_prop("MAX", lines, must=True))
        self.Npoints = int(self._read_prop("NPOINTS", lines, must=True))

        # 2.5 AtomTypes if reading RDF-file
        AtomTypes = self._read_prop("TYPES", lines, must=(kind == "RDF"))
        AtomTypes = AtomTypes.split(",") if AtomTypes else None
        if AtomTypes:
            AtomTypes = [atom_type.lstrip().strip() for atom_type in AtomTypes]

        NTypes = self._read_prop("NTYPES", lines, must=(kind == "RDF"))
        if NTypes:
            NTypes = int(NTypes)
        else:
            NTypes = len(AtomTypes) if AtomTypes else None

        self.NPairBondsExclude = self._parse_exclusions(
            self._read_prop("NPAIRBONDSEXCLUDE", lines, must=False),
        )
        self.NAngleBondsExclude = self._parse_exclusions(
            self._read_prop("NANGLEBONDSEXCLUDE", lines, must=False),
        )

        # 3. Include Included files into the list of lines
        def CountIncludes(lines, kind):
            return sum([1 if x.startswith("&INCLUDE" + kind) else 0 for x in lines])

        while CountIncludes(lines, kind) != 0:
            # 3.1 Detect Include line number (with respect to Kind)
            s_inc = filter(
                lambda x: x if x.startswith("&INCLUDE" + kind) else None,
                lines,
            )
            s_inc = s_inc[0]  # the include directive line
            i_inc = lines.index(s_inc)  # index of the line
            # 3.2 Read included file
            inc_file_name = s_inc.split("=")[1].strip()
            try:
                inc_file = open(inc_file_name)
                inc_lines = inc_file.readlines()
                inc_file.close()
            except:
                raise MTE.DFsetError(
                    "Error: can not read included file " + inc_file_name,
                )
                # 3.3 Clean and check lines
            inc_lines = list(map(CleanAndUp, inc_lines))
            inc_lines = [s for s in inc_lines if (s[0] != "!") & (s[0] != "#")]
            lines = (
                lines[0:i_inc] + inc_lines + lines[i_inc + 1 :]
            )  # 3.4 Add included lines to the list

        # 4. Detect &Potential and &RDF blocks
        i_begins = [i for i, s in enumerate(lines) if s == ("&" + kind)]
        i_ends = [i for i, s in enumerate(lines) if s == ("&END" + kind)]
        if not quiet:
            print(f"{len(i_begins):d} {kind}-sections found ")
        # 5. Initializing DF-instances from sections:
        DFs = []
        for i in range(len(i_begins)):
            if not quiet:
                print(f"Reading {kind}-section {i + 1:d} of {len(i_begins):d}")
            # 4.1 Detect type of function inside the block
            Type = self._read_prop("TYPE", lines[i_begins[i] : i_ends[i]], must=True)
            if Type not in ("NB", "B", "A"):
                raise MTE.DFsetError("Unknown type stated in lines. Type=" + str(Type))

            DF_Class_Detector = {
                ("RDF", "NB"): DF.RDF_NB,
                ("RDF", "B"): DF.RDF_PairBond,
                ("RDF", "A"): DF.RDF_AngleBond,
                ("POTENTIAL", "NB"): DF.Pot_NB,
                ("POTENTIAL", "B"): DF.Pot_PairBond,
                ("POTENTIAL", "A"): DF.Pot_AngleBond,
            }
            DF_Class = DF_Class_Detector[(kind, Type)]
            if DF_Class == DF.Pot_NB:
                DFs.append(
                    DF_Class(Lines=lines[i_begins[i] : i_ends[i] + 1], Ucut=Ucut),
                )
            else:
                DFs.append(DF_Class(Lines=lines[i_begins[i] : i_ends[i] + 1]))
                if not quiet:
                    print("succesfull!")

        # Check if  we read everything as it is stated in General section
        def _check_consistency(title, n_total, DF_type, DFs_):
            n_actual = len([df for df in DFs_ if isinstance(df, DF_type)])
            if n_actual != n_total:
                raise MTE.DFsetError(
                    f"Error: Number of read {title}-functions ({n_actual:d}) differs from N_{title} ({n_total:d})stated in"
                    " &General-section",
                )

        for title, DF_type, n_total in zip(
            ["NB", "B", "A"],
            [DF.DF_NB, DF.DF_PairBond, DF.DF_AngleBond],
            [N_NB, N_B, N_A],
        ):
            _check_consistency(title, n_total, DF_type, DFs)

        # 6 Initialize object's properties
        if self.Name is None:
            self.Name = File
        self.NTypes = NTypes
        if AtomTypes is not None:
            self.AtomTypes = AtomTypes
        else:

            def uniq(seq):
                # order preserving
                noDupes = []
                [noDupes.append(i) for i in seq if not noDupes.count(i)]
                return noDupes

            self.AtomTypes = uniq(
                list(
                    [
                        at
                        for df in DFs
                        if isinstance(df, DF.DF_NB)
                        for at in df.AtomTypes
                    ],
                ),
            )
        self.DFs = DFs

    def _get_exclusions_records(self):
        olines_ = []
        if (self.NAngleBondsExclude is not None) and (
            list(self.NAngleBondsExclude.keys()) != []
        ):
            olines_.append(
                "NAngleBondsExclude={0}".format(
                    ",".join(
                        [
                            f"{moltype_}:{self.NAngleBondsExclude[moltype_]}"
                            for moltype_ in sorted(self.NAngleBondsExclude.keys())
                        ],
                    ),
                ),
            )
        if (self.NPairBondsExclude is not None) and (
            list(self.NPairBondsExclude.keys()) != []
        ):
            olines_.append(
                "NPairBondsExclude={0}".format(
                    ",".join(
                        [
                            f"{moltype_}:{self.NPairBondsExclude[moltype_]}"
                            for moltype_ in sorted(self.NPairBondsExclude.keys())
                        ],
                    ),
                ),
            )
        return olines_

    def Write(self, ofilename, Split=False):
        """Write the set of functions to the file.

        Args:
            ofilename (str): File to write the set
            Split (bool): Default False. If True, all functions will be written to a separate include-files.
                If Split=[True, False, True,....] only those functions DFs[i] where Split[i]=True will be written to
                include-files, and other will be kept in the main file

        Examples:
            df_set = MT.ReadPot('DMPC.pot', Ucut=1e5)
            df_set.Write('DMPC.split.pot', Split=True)

        """
        # 0. Check Split, and convert it to logical list:
        if Split:
            Split = [True for i in self.DFs]
        if not Split:
            Split = [False for i in self.DFs]
        if isinstance(Split, list):
            if len(Split) < len(self.DFs):
                print(
                    "Warning: The Split-list is too short, assume the missing values are False",
                )
                Split = Split + (len(self.DFs) - len(Split)) * [False]
        # 1. Open file for writing
        ofile = open(ofilename, "w")
        # 2. Write &General section
        olines = []
        olines.append("&General")
        olines.append(f"NTypes={self.NTypes:d}")
        if self.AtomTypes is not None:
            olines.append("Types = " + ", ".join(str(at_) for at_ in self.AtomTypes))
        olines.append(f"N_NB={len(self.DFs_NB):d}")
        olines.append(f"N_B={len(self.DFs_B):d}")
        olines.append(f"N_A={len(self.DFs_A):d}")
        olines.append(f"Max={self.Max:8.4f}")
        olines.append(f"Min={self.Min:8.4f}")
        olines.append(f"NPoints={self.Npoints:d}")
        olines = olines + self._get_exclusions_records()

        olines.append("&EndGeneral")
        olines = [x + "\n" for x in olines]
        ofile.writelines(olines)
        # 3. Write functions in order: NB, B, A
        for i in self.DFs:
            ofile.write("\n")
            s = Split[self.DFs.index(i)]
            i._write(ofile, Split=s)
        ofile.close()

    def Plot(self, atonce=False, linetype=None, **kwargs):
        """Plot all functions present in the DFset using MagicTools.OnePlot().

        Shortcut for MT.MultPlot(dfset) useful for quick plot of the DFset. We recommend to directly use MultPlot.

        Args:
            atonce (bool): If true, plot all on a same single plot. Deafult False.
            linetype (str): String specifying the line style and color as in matplotlib.pyplot.plot()
            **kwargs: arguments passed to MagicTools.OnePlot

        Example:
            dfset.Plot(atonce=False, linetype='r-')

        """
        from MagicTools import OnePlot

        if linetype:
            self.SetPlotProperty("linetype", linetype)
        if atonce:
            OnePlot(self, **kwargs)
        else:
            for df in self.DFs:
                OnePlot(df, _multiplot=False, **kwargs)

    def Reduce(self, template):
        """Create a reduced DFset from the original one, which will only contain DFs similar to the provided template set.

        Args:
            template (DFset): Set of function to be used as a template for filtering.

        Returns:
            New DFset

        """
        reduced_DFset = DFset(
            Name=self.Name,
            Min=self.Min,
            Max=self.Max,
            Npoints=self.Npoints,
            DFs=[
                self.__get_similar(df)
                for df in template.DFs
                if self.__get_similar(df) is not None
            ],
            NAngleBondsExclude=self.NAngleBondsExclude,
            NPairBondsExclude=self.NPairBondsExclude,
        )
        if (
            self.NAngleBondsExclude != template.NAngleBondsExclude
            or self.NPairBondsExclude != template.NPairBondsExclude
        ):
            print(
                f"Warning: Exclusion rules seems not consistent between DFset {self.Name} and {template.Name}",
            )
        return reduced_DFset

    def SetTitle(self, title=None):
        """OBSOLETE! Use DFset.Name field instead.

        Set title for the DFset and for every DF of the set. Used for having nice legends in massive plots

        Args:
            title (str): Title to set, if not provided field Name will be used insted.

        Example:
            ``SetTitle('sometitle')``

        """
        print("""Warning!
        This function and Title is deprecated, since it brings nothing else, but confusion.
        Please set value of DFset.Name - property instead:
        Example:
            dfset.Name = 'The desired name'
              """)
        assert title is not None
        self.Name = title

    def SetPlotProperty(self, property, value):
        """Set plot-related keyword property for the DFset and for every function (DF) of the set.

        Used for fine control of the pictures in massive plots

        Args:
            property (str): Name of the property which will be set
            value: Value of the property

        Example:
            ``dfset.SetPlotProperty('linestyle', '--')``: Set linestyle dashed.
            ``dfset.SetPlotProperty('linewidth', 3)``: Make line bolder.
            ``dfset.SetPlotProperty('color', 'red')`` : Make line red.

        """
        for df in self.DFs:
            df.plot_kwargs[property] = value

    def ExtendTail(self, RcutNB):
        """Extend the tail range of all NB potentials of the set up to `RcutNB` and fill these values with zero.

        Args:
            RcutNB (float): Range until which the NB tails shall be extended (A).

        Example:
            ``dfset.ExtendTail(30)``: Extend the range up to 30 A

        """
        if RcutNB <= self.Max:
            print(
                f"Warning: the provided RcutNB={RcutNB} is not larger than original RMax of the set {self.Max}",
            )
            return
        for df in self.DFs_NB:
            df.ExtendTail(RcutNB)
        resol = (self.Max - self.Min) / self.Npoints
        self.Max = RcutNB
        self.Npoints = int(round((self.Max - self.Min) / resol))
        print(f"The set {self.Name} updated successfully")

    def CutTail(self, RcutNB):
        """Cut the range of non-bonded potentials in the set to ``RcutNB``.

        Args:
            RcutNB (float): Range where to cut the NB potentials (A)

        Example:
             ``dfset.CutTail(10)``: Cut the NB-potentials at range of 10A

        """
        if RcutNB >= self.Max:
            print(
                f"Warning: the provided RcutNB={RcutNB} is not smaller than original RMax of the set {self.Max}",
            )
            return
        for df in self.DFs_NB:
            df.CutTail(RcutNB)
        resol = (self.Max - self.Min) / self.Npoints
        self.Max = RcutNB
        self.Npoints = int(round((self.Max - self.Min) / resol))
        print(f"The set {self.Name} updated successfully")

    def AddCore(self):
        """Adds repulsive core to non-bonded potentials of the set and sets Rmin=0.

        Needed when the potentials are read from Magic output file.
        """
        for df in self.DFs_NB:
            if isinstance(df, DF.Pot_NB):
                df._add_core()

        self.Npoints = int(round(self.Max * self.Npoints / (self.Max - self.Min)))
        self.Min = 0.0

    def ChangeResolution(
        self,
        NewResol,
    ):  # TODO: Make working for Bond-potentials. FirstNonZero/lastnonzero
        """Changes resolution of the set.

        Args:
            NewResol ((float, float, float)):  Tuple/list with 3 values defining the new resolution for NB,B and A bonds

        """
        if all([r > 0.0 for r in NewResol]):
            for df in self.DFs_NB:
                if abs(df.Resol - NewResol[0]) > 0.000001:
                    df.ChangeResolution(NewResol[0])
            for df in self.DFs_B:
                if abs(df.Resol - NewResol[1]) > 0.000001:
                    df.ChangeResolution(NewResol[1])
            for df in self.DFs_A:
                if abs(df.Resol - NewResol[2]) > 0.000001:
                    df.ChangeResolution(NewResol[2])
            self.Npoints = int(round((self.Max - self.Min) / NewResol[0]))
        else:
            print("Error: Wrong resolution")

    @staticmethod
    def Average(dfsets, weights=None, force=False):
        """Calculate average DFset from the given list of DFsets.

        Args:
            dfsets ([DFset, DFset, ...]): List of DFset-objects to be averaged. They shall have same composition.
            weights ([float, float, ...]): List of weights for averaging. Must have length of underlying dfset
            force (bool): Force averaging of DFs even if they are not alike. Default False

        Returns:
            New DFset, where each DF is an average of corrsponding DFs of the given DFsets.

        Example:
            ``rdf_average = DFset.Average([dfset1, dfset2], weights=[1.0, 1.0], force=False)``

        """
        from copy import deepcopy

        if isinstance(dfsets, Iterable):
            dfsets = list(dfsets)  # Convert iterable to list
        assert isinstance(dfsets, list), "Expecting to get a list of DFsets"
        assert len(dfsets) > 0, "The DFset-list shall be non-empty"
        template = dfsets[0]
        if len(dfsets) == 1:
            return template

        assert all([isinstance(dfset, DFset) for dfset in dfsets]), (
            "Expecting to get a list of DFsets, but got list of something else"
        )

        # Check that length of all sets is same
        if not all([template.IsSimilar(dfset_) for dfset_ in dfsets[1:]]):
            print(
                "Some DFsets are not similar to others. This may lead to errors in average DFset."
                "Use DFset.Reduce() first, than average reduced DFsets",
            )
            return None

        # scale weights to 1.0
        if weights is not None:
            assert len(weights) == len(dfsets), (
                "error in provided weights - wrong length"
            )
            weights = [float(weight_) for weight_ in weights]
            if (abs(sum(weights) - 1.0) > 1e-6) and not force:
                print(
                    f"Weghts are not normalized: sum(weights)={sum(weights)} instead of 1.0",
                )
                print(
                    "I will normalize the weights. if you insist on orignal values set force=True",
                )
                weights = [weight_ / sum(weights) for weight_ in weights]

        # Now let's average
        average_dfset = deepcopy(template)
        for i_df, df in enumerate(average_dfset.DFs):
            average_dfset.DFs[i_df] = DF.DF.Average(
                [dfset_.DFs[i_df] for dfset_ in dfsets],
                weights=weights,
                force=force,
            )
        average_dfset.Name = template.Name + ".averaged"
        return average_dfset

    def IsSimilar(self, other, quiet=False):
        """Check if the DFset is similar to the given one `other`:

        Compare exclusion-rules, lengths of the sets, and then check that undelaying DFs are similar.

        Args:
            other (DFset):
            quiet (bool): If true print differences between the sets. Default False.


        Returns:
            True or False

        """
        assert isinstance(other, DFset), "Require DFset as input"
        if (self.NPairBondsExclude != other.NPairBondsExclude) or (
            self.NAngleBondsExclude != other.NAngleBondsExclude
        ):
            if not quiet:
                print("Exclusion rules are different")
            return False
        if len(self.DFs) != len(other.DFs):
            if not quiet:
                print("Total Number of components are different")
            return False
        if (
            (len(self.DFs_NB) != len(other.DFs_NB))
            or (len(self.DFs_B) != len(other.DFs_B))
            or (len(self.DFs_A) != len(other.DFs_A))
        ):
            if not quiet:
                print("Number of components are different")
            return False
        for i, df in enumerate(self.DFs):
            if not df.IsSimilar(other.DFs[i]):
                if not quiet:
                    print(df, other.DFs[i], " are different\n")
                return False
        return True

    def FindBondDF(self, MolTypeName, BondNumber):
        """Find Bond-DF from the DFset by MolTypeName and BondNumber.

        Args:
            MolTypeName (str): Name of the molecular type the bond belongs to
            BondNumber (int):  Number of the bond

        Returns:
            single DF-object or a [DF] if more than one function is found. Return None if noting is found.

        Example:
            ``dfset.FindBondDF('DMPC.CG', 1)``: Find bond distribution corresponding to the first bond in moleular type DMPC.CG

        """
        assert isinstance(MolTypeName, str)
        assert isinstance(BondNumber, int)
        lst = [
            b
            for b in self.DFs_BA
            if b.MolTypeName == MolTypeName and b.BondNumber == BondNumber
        ]
        if len(lst) == 0:
            print(f"No matching bond DF found:{MolTypeName}:{BondNumber}")
            return None
        if len(lst) > 1:
            print(
                "More than one matching bond DF found:{0}".format(
                    ",".join([str(bond_) for bond_ in lst]),
                ),
            )
            return lst
        return lst[0]

    def reNormalize(self):
        """Normalize (inplace) all bonded distribution functions of the set to 1.0."""
        for df_ in self.DFs_BA:
            assert isinstance(df_, DF.RDF), "Only works with RDFs"
            df_.reNormalize()

    def _SetBondNamesByMolTypeAndBondNumber(self):
        """Set names of the bond-related functions according to their MolecularType and BondNumber, i.e. DNA:1."""
        for df_ in self.DFs_BA:
            df_.Name = f"{df_.MolTypeName}:{df_.BondNumber}"

    def Distance(self, other, **kwargs):
        """Distance between this and other DFset, calculated as sum of distances between underlying DFs.

        Args:
            other (DFset):

        Returns: (float) distance

        Example:
            ``thisDFset.Distance(other_DFset)``

        """
        self.IsSimilar(other)
        return sum(
            [
                df_this.Distance(df_other, **kwargs)
                for df_this, df_other in zip(self, other)
            ],
        )
