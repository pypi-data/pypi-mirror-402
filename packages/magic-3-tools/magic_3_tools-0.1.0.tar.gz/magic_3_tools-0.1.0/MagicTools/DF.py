import copy
from collections import defaultdict

import numpy as np
import pandas as pd

from . import MTException as MTE
from .object_magictools import ObjectMagicTools


class DF(ObjectMagicTools):
    """Base class representing a single Distribution Function (RDF,ADF,Potential, etc.).

    It contains common properties and methods of distribution functions.

    Attributes:
            x, y: numpy arrays storing tabulated values of the argument and the function
            Name: Name of the DF
            FullName: Completely resolved name of the DF, including type and kind of the DF
            Min,Max: range of distance/angle values where the function is defined
            Type: type of the function: NB, B (pairwise bond), A (angle-bond)
            Kind: kind of the function: RDF, Potential
            Npoints: Number of points in a table defining the  function
            Resol: resolution of the table defining the function

    Methods:
            Write(): write the function into a file-stream
            Plot(): Plot the function
            Save(): Write the function in a tabulated for to a text file.
            Average(): Make a new DF which is average of given list of DFs
            ExtendRange(): Extend range of the DF
            ExtendTail(): Extend the tail range of NB distribution function in to RcutNB
            CutTail(): Cut the tail of NB RDF/potential
            IsSimilar(): Checks if the DF is similar to given one, based on its Type, Kind, AtomTypes, MolecularType and Bond number
            ChangeResolution(): Change resolution of the potential. The new points will have an average value between closest neighbours
            Distance(): Calculate the distance between this and the given DF

            Normalize(): Calculate values of g[:,0:2] by normalizing accumulated histogram.
            Smooth(): Smooth values of the function using Savitzky Golay 5 points smoothing procedure
            Trim(): Cut function's (g[:,1]) left and right tails which have values smaller then the tolerance




    """

    _round = 7
    default_plot_kwargs = defaultdict(lambda: None)
    default_plot_kwargs["linewidth"] = 1
    default_plot_kwargs["xlabel"] = "R, A"
    default_plot_kwargs["linetype"] = ""

    def __init__(
        self,
        Name=None,
        Min=None,
        Max=None,
        Npoints=None,
        AtomTypes=None,
        AtomGroups=None,
        _AtomGroups_=None,
        g=None,
        BondNumber=None,
        MolTypeName=None,
        Lines=None,
    ):
        """Construct the object of class DF:

        Either specify all the required properties or just provide list of strings (Lines) specifying
        single RDF/potential section.
        """
        super(DF, self).__init__()
        self.Fixed = False
        self.g = None
        self.DFset = None
        self.SameAsBond = None
        if Lines is None:  # No lines provided - old-type constructor
            self.Name = Name
            self._npoints = Npoints
            self.AtomGroups = AtomGroups
            self._AtomGroups_ = _AtomGroups_
            self.AtomTypes = AtomTypes
            self.MolTypeName = MolTypeName
            self.BondNumber = BondNumber
            self._min = Min
            self._max = Max
            if g is not None:
                self.g = g if g.shape[0] == 2 else g.T
                if np.any(
                    np.abs(np.diff(self.g[0, :]) - self.Resol) > self.Resol * 0.01,
                ):
                    raise MTE.DFError(
                        f"Error while creating the function: {self.FullName} points in the table are not equidistant",
                    )
            else:
                self.g = np.array(
                    (
                        np.arange(0, self.Npoints) * self.Resol
                        + 0.5 * self.Resol
                        + self.Min,
                        np.zeros(self.Npoints),
                    ),
                )

        else:
            self.__init_from_lines(Lines)
        self._ghist = np.zeros(self.Npoints)
        self._pairslist = []
        self._title = None
        self._write_section_header = "RDF" if "RDF" in self.Kind else "Potential"

        self.plot_kwargs = self.default_plot_kwargs.copy()
        # self._update_title()

    @property
    def Max(self):
        if self.g is not None:
            return self.x[-1] + self.Resol * 0.5
        return self._max

    @property
    def Min(self):
        if self.g is not None:
            return abs(self.x[0] - self.Resol * 0.5)
        return self._min

    @property
    def x(self):
        """Tabulated variable of the DF, usually distance or angle."""
        return self.g[0, :]

    @x.setter
    def x(self, value):
        assert isinstance(value, np.ndarray)
        self.g[0, :] = value

    @property
    def y(self):
        """Tabulated values of the DF."""
        return self.g[1, :]

    @y.setter
    def y(self, value):
        assert isinstance(value, np.ndarray)
        self.g[1, :] = value

    @property
    def Resol(self):
        if self.g is not None:
            return (self.x[-1] - self.x[0]) / (len(self.x) - 1)
        return (self._max - self._min) / self._npoints  # if we read min/max from file

    @property
    def Npoints(self):
        if self.g is not None:
            return len(self.g[1, :])
        return self._npoints

    @property
    def FullName(self):
        """Return full name of the object: shortname + Kind + Type."""
        return f"{self.Name}.{self.Kind}.{self.Type}"

    @property
    def DFsetName(self):
        """Return name of the parent DFset. Used for legend when plotting DF."""
        if self.DFset:
            if self.DFset.Name is not None:
                return self.DFset.Name
        return None

    @property
    def _write_specific_lines(self):
        raise MTE.DFError(
            "Called virtual method _write_specific_lines of parent class DF. Check your code!",
        )

    @property
    def Kind(self):
        raise MTE.DFError(
            "Called virtual method Kind of parent class DF. Check your code!",
        )

    @property
    def Type(self):
        raise MTE.DFError(
            "Called virtual method Type of parent class DF. Check your code!",
        )

    @property
    def plot_args(self):
        """Returns list of unnamed arguments for pyplot.plot(): X,Y, linetype"""
        return [self.x, self.y, self.plot_kwargs["linetype"]]

    def __init_from_lines(self, lines):
        """InitFromLines(lines) - Reads section of a .rdf or .pot file provided in text lines and creates required object."""

        # Stage 1. Clean and check
        # 1.1 Clean lines from comments and leading spaces, convert all to uppercase
        def CleanAndUp(s):
            s = s.strip().lstrip()
            if s.startswith("&"):
                s = s.upper()
            if "=" in s:
                ss = s.split("=")
                ss[0] = ss[0].upper()
                s = "=".join(ss)
            return s

        lines = [
            CleanAndUp(line)
            for line in lines
            if not (line.startswith("!") or line.startswith("#"))
        ]

        # 2 Check for header tags, detect Kind

        def check_header_tag(knd, lines):
            if lines[0] == "&" + knd:
                if lines.count("&" + knd) > 1:
                    raise MTE.DFError("too many &" + knd + " tags in lines")
                if lines.count("&END" + knd) != 1:
                    raise MTE.DFError(
                        "too many or too few &END" + knd + " tags in lines",
                    )

        for header_kind in ["RDF", "POTENTIAL", "INCLUDED", "TABLE"]:
            check_header_tag(header_kind, lines)

        # 3 Read properties
        def read_prop(property, lines_, must=True):
            import re

            query = [line for line in lines_ if re.search("^" + property + " *=", line)]
            if query:
                return query[0].split("=")[1].strip()
            if must:
                raise MTE.DFError("Error: No " + property + " value provided")
            return None

        # 3.1 Name
        Name = read_prop("NAME", lines, must=True)
        Name = Name.replace(" ", "")  # remove spaces
        # 3.2 Type
        Type = read_prop("TYPE", lines, must=True)
        if Type not in ("NB", "B", "A"):
            raise MTE.DFError("Unknown type stated in lines. Type=" + str(Type))
        # 3.25  Fixed - flag
        self.Fixed = "&FIXED" in lines
        # 3.3 Min Max
        Min = float(read_prop("MIN", lines, must=True))
        Max = float(read_prop("MAX", lines, must=True))
        # 3.4 NPoints
        NPoints = int(read_prop("NPOINTS", lines, must=True))
        # 3.5 AtomTypes if reading NB-rdf or potential
        AtomTypes = read_prop("ATOMTYPES", lines, must=(Type == "NB"))
        if Type == "NB":
            AtomTypes = AtomTypes.replace(" ", "").split(",")
        # 3.6 if bonded -rdf or potential -> read Pairs, Bond Number and MolecularType
        AtomGroups = None
        NGroups = None
        BondNumber = None
        MolTypeName = None
        if Type != "NB":
            if Type == "B":
                knd = "PAIRS"
            elif Type == "A":
                knd = "TRIPLETS"
            AtomGroups = read_prop(knd, lines, must=True).replace(" ", "").split(",")
            NGroups = int(read_prop("N" + knd, lines, must=True))
            AtomGroups = [[int(n) for n in ag.split("-")] for ag in AtomGroups]
            if len(AtomGroups) != NGroups:
                raise MTE.DFError(
                    f"Actual number of atom groups {len(AtomGroups):d} differs from stated {NGroups:d}",
                )
            BondNumber = int(read_prop("BONDNUMBER", lines, must=True))
            MolTypeName = read_prop("MOLTYPE", lines, must=True)
            self.SameAsBond = read_prop("SAMEASBOND", lines, must=False)

        # 4. Read Table
        try:
            table = np.loadtxt(
                lines[lines.index("&TABLE") + 1 : lines.index("&ENDTABLE")],
                dtype=float,
            )
        except:
            raise MTE.DFError("Can not read table - check the data")

        # 5 Set the object's properties
        self.Name = Name
        self._min = Min
        self._max = Max
        self._npoints = NPoints
        self.AtomTypes = AtomTypes
        self.g = table.T
        self.AtomGroups = AtomGroups
        # self.NGroups = NGroups
        self.BondNumber = BondNumber
        self.MolTypeName = MolTypeName

    def Normalize(self, volume):
        """Normalize(volume) - Calculate values of g[:,0:2] by normalizing accumulated histogram.

        Intermolecular DFs are normalized over volume/(4*Pi*r**2*Npairs_counted). Intramolecular DFs are normalized
        over Npairs_counted. Only available with rdf-2.0.
        """
        # Calculating total number of pairs in the RDF excepting pairs in point 0.
        npairs = sum(np.asarray(self._ghist))
        if npairs == 0:
            self.y = np.zeros_like(self._ghist, dtype=float)
        elif self.Type == "NB":
            self.y = (
                np.asarray(self._ghist)
                * (volume / npairs)
                / (4 * 3.1415926536 * self.Resol * (self.x**2 + self.Resol**2 / 12.0))
            )
            self.y[0] = 0.0
        elif self.Type in ("B", "A"):
            self.y = np.asarray(self._ghist) / (self.Resol * npairs)

    def Smooth(self):
        """Smooth - Smooth values of the function using Savitzky-Golay 5 points smoothing procedure."""
        y_smooth = np.array(self.y)
        y_smooth[2:-2] = (
            self.y[2:-2] * 0.486
            + self.y[1:-3] * 0.343
            - self.y[0:-4] * 0.086
            + self.y[3:-1] * 0.343
            - self.y[4:] * 0.086
        )
        self.y = y_smooth

    def Trim(self, tolerance=None):
        """Trim(tolerance) - Cut function's (g[:,1]) left and right tails which have values smaller then <tolerance>."""
        if tolerance is None:
            tolerance = 10.0 ** (-self._round)
        imax = self.y.argmax()  # position of the maximum
        firstnonzero = 0
        while (self.y[firstnonzero] < tolerance) and (firstnonzero < imax):
            firstnonzero += 1

        lastnonzero = self.Npoints
        while (self.y[lastnonzero - 1] < tolerance) and (lastnonzero > imax):
            lastnonzero -= 1

        if firstnonzero == lastnonzero:  # the RDF is zero
            x_new = self.x[0:2]
            y_new = self.y[0:2]
        else:
            x_new = self.x[firstnonzero:lastnonzero]
            y_new = self.y[firstnonzero:lastnonzero]
        y_new[y_new < tolerance] = tolerance
        self.g = np.array((x_new, y_new))

    def Plot(self, linetype=None, **kwargs):
        """Plot the function, using MagicTools.OnePlot->matplotlib.pyplot.
            hardcopy: - if true, does not show the plot, but save it to file
            linetype: - define type of lines to use (linetype='.' use dots, linetype='- 'use solid lines)
        all other arguments are identical to matplotlib.pyplot keyword arguments
        """
        from MagicTools import OnePlot

        if linetype:
            self.plot_kwargs["linetype"] = linetype
        OnePlot(self, _multiplot=False, **kwargs)

    def Dump(self, filename):
        """Dump(filename)- Dump the object to a file <filename> using pickle library."""
        import pickle

        f = open(filename, "ab")
        pickle.dump(self, f)
        f.close()

    def Save(self, path=""):
        """Save() - Write the function in a tabulated for to a text file.

        Filename is defined as (self.Type+self.Name).replace(' ','.')
        """
        if path:
            path = path + r"\/"
        ofilename = f"{path}{self.Type}.{self.Name}.dat".replace(" ", ".")
        with open(ofilename, "w") as f:
            f.write(f"# R      {self.Name}{self.Type}\n")
            f.writelines(f"{x_:9.5f}  {y_:9.5f}\n" for x_, y_ in zip(self.x, self.y))

    def IsSimilar(self, other):
        """Check if this DF is similar to the other one.

        Args:
            other (DF):

        Returns: True or False

        """
        assert isinstance(other, DF), "The object to compare must be of class DF"
        # if type(self) != type(other):
        #     return False
        if self.Type != other.Type:
            return False
        if self.Kind != other.Kind:
            return False
        if isinstance(self, DF_NB):  # Non-bonded
            if set(self.AtomTypes) != set(other.AtomTypes):
                return False
        else:  # Bond or Angle
            if self.BondNumber != other.BondNumber:
                return False
            if self.MolTypeName != other.MolTypeName:
                return False
        return True

    def Distance(self, other, force=False):
        """Calculate the distance between this and the given DF.

        Distance = sqrt(sum([f(r)-f_0(r)]**2))

        Args:
            other (DF): The other DF.
            force (bool): Calculate the distance, even if functions seem too different from each other

        Returns: Distance.

        Example:
            `thisDF.Distance(otherDF)`

        """
        from scipy.interpolate import interp1d

        if not (self.IsSimilar(other) or force):
            print(
                "The DFs are seem to be not alike. If you are sure that they are, use force=True",
            )
            return 0.0

        f_self = interp1d(
            self.x,
            self.y,
            kind="linear",
            fill_value=0.0,
            bounds_error=False,
            assume_sorted=True,
        )
        f_other = interp1d(
            other.x,
            other.y,
            kind="linear",
            fill_value=0.0,
            bounds_error=False,
            assume_sorted=True,
        )
        min_, max_, resol_ = (
            min(self.x[0], other.x[0]),
            max(self.x[-1], other.x[-1]),
            min(self.Resol, other.Resol) * 0.1,
        )
        x_range = np.arange(min_, max_, resol_, dtype=float)

        integral_ = np.trapezoid(
            np.square(f_self(x_range) - f_other(x_range)),
            x=x_range,
        )

        return np.sqrt(integral_) / (max_ - min_) / (self.y.mean())

    def ChangeResolution(self, new_resolution):
        """Change resolution of the potential. The new points will have an average value between closest neighbours."""
        npoints_new = int(round((self.Max - self.Min) / new_resolution))
        if (
            abs(self.Max - self.Min - new_resolution * npoints_new)
            > new_resolution * 0.01
        ):
            print("Error: inconsistent resolution at " + self.Name)
            raise MTE.DFError("inconsistent resolution" + self.Name)

        x_new = np.zeros(npoints_new)
        y_new = np.zeros(npoints_new)

        x_new = np.linspace(
            self.Min + 0.5 * new_resolution,
            self.Max + 0.5 * new_resolution,
            npoints_new,
            endpoint=False,
        )
        y_new = np.interp(x_new, self.x, self.y)
        self.g = np.array((x_new, y_new))

    @staticmethod
    def Average(dfs, force=False, weights=None):
        """Average list of DF-objects.

        Args:
            dfs: list of DFs to average
            force: (False) Force calculation despite inconsistency in the input
            weights: weight used for averaging, default - equal weights,
                    'by_population' - assign weigths proportional to number of AtomGroups in each DF

        Returns: new DF-object

        """
        assert isinstance(dfs, list), "Expexting to get a list of DFs"
        assert len(dfs) > 0, "The DFs-list shall be non-empty"
        template = dfs[0]
        if len(dfs) == 1:
            return template

        if weights is None:
            weights = [1.0 / len(dfs)] * len(dfs)
        elif weights == "by_population":
            assert all([isinstance(df_, DF_Bond) for df_ in dfs]), (
                "For weight='by_population' all averaged objects shall be bond distributions"
            )
            weights = [len(b_.AtomGroups) for b_ in dfs]
            weights = [float(weight_) for weight_ in weights]
            weights = [weight_ / sum(weights) for weight_ in weights]
        else:
            assert len(weights) == len(dfs), "error in provided weights - wrong length"
            weights = [float(weight_) for weight_ in weights]
        if (abs(sum(weights) - 1.0) > 1e-6) and not force:
            print(f"strange weights: sum(weights)={sum(weights)} instead of 1.0")
            print("if you insist, call with force=True")
            return None

        assert all([isinstance(df, DF) for df in dfs]), (
            "Expexting to get a list of DFs, but got list of something else"
        )
        if not (all([template.IsSimilar(df) for df in dfs[1:]]) or force):
            print(
                "Not all DFs are similar. This may lead to errors in averaging. "
                "If you insist to proceed, call procedure again with force=True",
            )
            return None
        if not all([abs(template.Resol - df.Resol) < 1e-6 for df in dfs[1:]]):
            print("Resolution is not same for all provided DFs")
            return None
        # All checks are done, now let's calculate the average
        g_series = [
            pd.Series(df_.y * weight_, index=df_.x)
            for weight_, df_ in zip(weights, dfs)
        ]
        cc = pd.concat(g_series, axis=1)
        cc = cc.fillna(0.0)
        mean_ = cc.sum(axis=1)
        average_df = copy.deepcopy(template)
        average_df.g = np.array([mean_.index.values, mean_.values])
        average_df.Trim()
        # average_df.Name = template.Name + '.averaged'
        return average_df

    def ExtendRange(self, new_min, new_max, interpolate=False, **kwargs):
        """Extend range of the DF using the first and the last values to fill the new points on left and right side, respectively."""
        assert new_min <= self.Min
        assert new_max >= self.Max
        ratio = (new_max - new_min) / self.Resol
        assert abs(round(ratio, 0) - ratio) < 1e-6, (
            "New max and min values do not fit the resolution"
        )
        s_new = pd.Series(self.y, index=self.x.round(5))
        if new_min < self.Min:
            ndx = (np.arange(new_min + self.Resol / 2, self.Max, self.Resol)).round(5)
            s_left = pd.Series(np.zeros(len(ndx)), index=ndx)
            s_new = s_new + s_left

            def _fill_na_(s_new):
                assert isinstance(self, Pot)
                R, U, F = self._export(**kwargs)

                def f(r, R):
                    return U[np.argmin(np.abs(R - r))]

                fill_ndx = s_new.index
                fill_value = pd.Series(fill_ndx, index=fill_ndx)
                fill_value = fill_value.apply(f, args=(R,))
                return s_new.fillna(fill_value)

            if not interpolate:
                s_new.fillna(method="backfill", inplace=True)
            else:
                s_new = _fill_na_(s_new)
        if new_max > self.Max:
            ndx = (np.arange(new_min + self.Resol * 0.5, new_max, self.Resol)).round(5)
            s_right = pd.Series(np.zeros(len(ndx)), index=ndx)
            s_new = s_new + s_right
            if not interpolate:
                s_new.fillna(method="ffill", inplace=True)
            else:
                s_new = _fill_na_(s_new)
        self.g = np.array([s_new.index.values, s_new.values])

    @property
    def _write_common_lines(self):
        lines = f"Name={self.Name}\nType={self.Type}\nMin={self.Min:8.4f}\nMax={self.Max:8.4f}\nNPoints={self.Npoints:d}\n"
        if self.Fixed:
            lines = lines + "&Fixed\n"
        return lines

    @property
    def _write_table_lines(self):
        try:
            round_precision = int(round(abs(np.log10(self.Resol))))
        except:
            round_precision = 0
        round_precision += 2
        x_rounded = self.x.round(round_precision)  # rounding R-values
        y_rounded = self.y.round(self._round)  # rounding RDF/potential values
        table_lines = [
            f"{x_rounded[i]:11.7f}  {y_rounded[i]:11.7f}\n" for i in range(self.Npoints)
        ]
        table_lines = ["&Table\n", *table_lines, "&EndTable\n"]
        return table_lines

    def _write(self, ofile, Split=False, include_file_name=None):
        ofile.write(f"&{self._write_section_header}\n")
        ofile.writelines(self._write_common_lines)
        ofile.writelines(self._write_specific_lines)

        if Split:  # if we write table to the include file
            if not include_file_name:  # If no name provided - create one
                ofilename = ofile.name
                include_file_name = f"{ofilename}.{self._write_incfile_template}.inc"
            ofile.write(f"&Include{self._write_section_header}={include_file_name}\n")
            with open(include_file_name, "w") as oinc_file:
                oinc_file.write(f"&Included{self._write_section_header}\n")
                oinc_file.writelines(self._write_common_lines)
                oinc_file.writelines(self._write_specific_lines)
                oinc_file.writelines(self._write_table_lines)
                oinc_file.write(f"&ENDIncluded{self._write_section_header}\n")
        else:  # No split
            ofile.writelines(self._write_table_lines)
        ofile.write(f"&END{self._write_section_header}\n")


class RDF(DF):
    __doc__ = DF.__doc__
    default_plot_kwargs = DF.default_plot_kwargs.copy()
    default_plot_kwargs["ylabel"] = "RDF"

    @property
    def Kind(self):
        return "RDF"

    def Smooth(self):
        """Smooth() - Smooth values of the function using Savitzky Golay 5 points smoothing procedure and set negative element to zero."""
        super(RDF, self).Smooth()
        self.y[self.y < 0] = 0.0  # for RDF add negative value elimination

    def reNormalize(self):
        """Make sure that Bonded-RDFs are normalized to 1.0."""


class DF_NB(DF):
    __doc__ = DF.__doc__
    default_plot_kwargs = DF.default_plot_kwargs.copy()
    default_plot_kwargs["xlabel"] = "R, A"

    @property
    def Type(self):
        return "NB"

    @property
    def _write_specific_lines(self):
        return ["AtomTypes={0}\n".format(", ".join(str(at_) for at_ in self.AtomTypes))]

    @property
    def _write_incfile_template(self):
        return "{0}.{1}".format(self.Type, "-".join(str(at_) for at_ in self.AtomTypes))

    def ExtendTail(self, RcutNB):
        """Extend the tail range of NB distribution function in to RcutNB."""
        if RcutNB <= self.Max:
            print(
                f"Warning: the provided RcutNB{RcutNB} is not larger than original RMax of the function {self.Max}",
            )
            return

        # populate
        nAddPoints = int(round((RcutNB - self.Max) / self.Resol))
        if abs(nAddPoints * self.Resol + self.Max - RcutNB) > 0.00001:
            print(
                f"Error: the provided RcutNB={RcutNB} is uncompatible with resolution of {self.Resol}",
            )
            print(f"Try to use RcutNB={nAddPoints * self.Resol + self.Max} instead")
            return
        x_new = np.zeros(self.Npoints + nAddPoints, dtype=float)
        y_new = np.zeros(self.Npoints + nAddPoints, dtype=float)
        x_new[0 : self.Npoints] = self.x
        y_new[0 : self.Npoints] = self.y
        x_new[self.Npoints :] = (
            self.x[-1] + np.linspace(1, nAddPoints, nAddPoints) * self.Resol
        )
        self.g = np.array((x_new, y_new))
        print(f"DF: {self.Name} updated successfully")

    def CutTail(self, RcutNB):
        """Cut the tail of NB RDF/potential."""
        if RcutNB >= self.Max:
            print(
                f"Warning: the provided RcutNB{RcutNB} is not smaller than original RMax of the function {self.Max}",
            )
            return
        nCutPoints = int(round((-RcutNB + self.Max) / self.Resol))
        if abs(nCutPoints * self.Resol - self.Max + RcutNB) > 0.00001:
            print(
                f"Error: the provided RcutNB={RcutNB} is uncompatible with resolution of {self.Resol}",
            )
            print(f"Try to use RcutNB={nCutPoints * self.Resol + self.Max} instead")
            return
        Npoints_new = self.Npoints - nCutPoints
        x_new = np.zeros(Npoints_new, dtype=float)
        y_new = np.zeros(Npoints_new, dtype=float)
        x_new[:] = self.x[:Npoints_new]
        y_new[:] = self.y[:Npoints_new]
        self.g = np.array((x_new, y_new))
        print(f"DF: {self.Name} updated successfully")


class DF_Bond(DF):
    __doc__ = DF.__doc__

    def __init__(self, *args, **kwargs):
        super(DF_Bond, self).__init__(*args, **kwargs)
        try:  # Try to access the attribute
            if self.SameAsBond:
                pass
        except:  # if it does not exists, initialize it with None
            self.SameAsBond = None
        if self.Name is None:
            self.Name = f"{self.Type}.{self.MolTypeName}.{self.BondNumber}"

    @property
    def _write_incfile_template(self):
        return f"{self.Type}.{self.MolTypeName}.{self.BondNumber}"

    @property
    def _write_specific_lines(self):
        lines = []
        if self.SameAsBond:
            lines.append(f"SameAsBond={self.SameAsBond}\n")
        return lines

    @staticmethod
    def Merge(dfs, new_bond_number):
        """Merge a list of DF_Bond objects into a single DF_Bond. The distribution is averaged, while AtomGroups are concatenated.

        Args:
            dfs: list of DF_Bond objects
            new_bond_number: Number to assign to the new DF_Bond

        Returns: Merged DF_Bond (PairBond- or AngleBond- distribution)

        """
        bond_average = DF.Average(dfs, weights="by_population", force=True)
        bond_average.BondNumber = new_bond_number
        bond_average.AtomGroups = [ag for b_ in dfs for ag in b_.AtomGroups]
        return bond_average


class DF_PairBond(DF_Bond):
    __doc__ = DF_Bond.__doc__

    @property
    def Type(self):
        return "B"

    @property
    def _write_specific_lines(self):
        lines = [
            f"MolType={self.MolTypeName}\n",
            f"BondNumber={self.BondNumber:d}\n",
            f"NPairs={len(self.AtomGroups):d}\n",
            "Pairs={0}\n".format(
                ", ".join(["-".join([str(a) for a in ag]) for ag in self.AtomGroups]),
            ),
        ]
        lines += super(DF_PairBond, self)._write_specific_lines
        return lines


class DF_AngleBond(DF_Bond):
    __doc__ = DF_Bond.__doc__
    _round = 6

    def __init__(self, *args, **kwargs):
        super(DF_AngleBond, self).__init__(*args, **kwargs)
        self.plot_kwargs["xlabel"] = "Angle, deg"

    @property
    def Type(self):
        return "A"

    @property
    def _write_specific_lines(self):
        lines = [
            f"MolType={self.MolTypeName}\n",
            f"Bondnumber={self.BondNumber:d}\n",
            f"NTriplets={len(self.AtomGroups):d}\n",
            "Triplets={0}\n".format(
                ", ".join(["-".join([str(a) for a in ag]) for ag in self.AtomGroups]),
            ),
        ]
        lines += super(DF_AngleBond, self)._write_specific_lines
        return lines


class RDF_AngleBond(RDF, DF_AngleBond):
    __doc__ = DF_AngleBond.__doc__

    def reNormalize(self):
        """Make sure that the RDF is normalized to 1.0."""
        self.y = self.y / (self.y.sum() * self.Resol)


class RDF_PairBond(RDF, DF_PairBond):
    __doc__ = DF_PairBond.__doc__

    def reNormalize(self):
        """Make sure that the RDF is normalized to 1.0."""
        self.y = self.y / (self.y.sum() * self.Resol)


class RDF_NB(RDF, DF_NB):
    __doc__ = DF_NB.__doc__


class Pot(DF):
    """Dummy class inherited from base class DF and parent for specific potential types, which have diferrent implementations of Export2Gromacs, and PotPressCorr method."""

    default_plot_kwargs = DF.default_plot_kwargs.copy()
    default_plot_kwargs["ylabel"] = "Potential, kJ/mol"
    digits_to_round = 5

    @property
    def Kind(self):
        return "Potential"

    def Export2Gromacs(
        self,
        zeroforce=True,
        ofilename="",
        _template="{0:12.6f}      0.000000     0.000000 {1:12.6f} {2:12.6f}     0.000000     0.000000\n",
        **kwargs,
    ):
        if not ofilename.endswith(".xvg"):
            ofilename = ofilename + "table_" + self.Name + "." + self.Type + ".xvg"
        (R_ie, U_ie, F_ie) = self._export(
            zeroforce=zeroforce,
            ofilename=ofilename,
            **kwargs,
        )
        print(f"{self.Name:<50s} -> {ofilename:<s}")
        with open(ofilename, "w") as ofile:
            ofile.writelines(
                _template.format(R_ie[i], U_ie[i], F_ie[i]) for i in range(len(U_ie))
            )

    def Export2GALAMOST(self, ofilename="", _xmlheader=None, **kwargs):
        if not ofilename.endswith(".dat"):
            ofilename = ofilename + "table_" + self.Name + "." + self.Type + ".dat"
        (R_ie, U_ie, F_ie) = self._export(ofilename=ofilename, **kwargs)
        # skip last datapoint for angle-potentials, otherwise GALAMOST complaints on non-equidistant table
        if isinstance(self, Pot_AngleBond):
            R_ie = R_ie[0:-1]
            U_ie = U_ie[0:-1]
        print(f"{self.Name:<50s} -> {ofilename:<s}")
        np.savetxt(
            ofilename,
            np.array((R_ie, U_ie)).T,
            delimiter="  ",
            fmt=("%10.5f", "%10.5f"),
            header=f"<{_xmlheader}>",
            footer=f"</ {_xmlheader}>",
        )

    def Export2LAMMPS(self, zeroforce=False, ofilename="", **kwargs):
        name = self.Name.replace(":", ".").replace("-", "_")
        if not ofilename.endswith(".table"):
            ofilename = ofilename + f"{name}.table"
        (R_ie, U_ie, F_ie) = self._export(
            zeroforce=zeroforce,
            ofilename=ofilename,
            _convert=(1.0, 0.239, 0.239),
            **kwargs,
        )
        # convert from default units: A, kJ/mol, kJ/mol/A  to GROMACS units: NM, kJ/mol, kJ/mol/nm
        if not isinstance(self, Pot_AngleBond):
            R_ie[0] = R_ie[0] + 0.000001
        with open(ofilename, "w") as ofile:
            ofile.write(f"{name}\nN {len(R_ie)}\n\n")
            ofile.writelines(
                f"{i + 1:d}  {R_ie[i]:12.6f}  {U_ie[i]:12.6f}  {F_ie[i]:12.6f}\n"
                for i in range(len(U_ie))
            )

    def _gauss_interpol(self, R0, U0, R_ie, sigma=None):
        """Auxiliary subroutine performing Gaussian smoothing-interpolation of given potential.

        U0,R0 - given set of points describing potential, R_ie-points defining resulting potential.
        Sigma defines gaussian's decay speed. default value is half distance between points in R0
        """
        U_ie = np.zeros(len(R_ie))
        if sigma is None:
            sigma = R0[1] - R0[0]
        for i in range(len(R_ie)):
            r = R_ie[i]
            w = np.exp(-np.square(r - R0) / (2 * sigma**2))
            U_ie[i] = np.dot(U0, w) / np.sum(w)
        return U_ie

    def _export_prepare_init(
        self,
        npoints=1800,
        Rmaxtable=180.0,
        sigma=1.0,
        interpol=True,
    ):
        self._export_R0 = self.x
        self._export_sigma = (self._export_R0[1] - self._export_R0[0]) * sigma
        self._export_U0 = self.y
        self._export_res = self.Resol
        # Generate sets of R-points
        self._export_npoints = npoints
        if not interpol:
            self._export_npoints = int(round(2 * (Rmaxtable - 0.0) / self._export_res))

        self._export_R_ie = np.linspace(0, Rmaxtable, self._export_npoints + 1)
        self._export_res_ie = self._export_R_ie[1] - self._export_R_ie[0]
        self._export_R_rtail_ie = self._export_R_ie[
            np.where(
                (self._export_R_ie - self._export_R0[-1]) > self._export_res_ie / 2,
            )
        ]
        self._export_R_ltail_ie = self._export_R_ie[
            np.where((self._export_R0[0] - self._export_R_ie) > self._export_res_ie / 2)
        ]

    def _export_left_tail_ie(
        self,
        Umax=2000.0,
        tail_strength=2.51922,
    ):
        """Left tail iextrapolation - harmonic extension."""
        from scipy import stats

        if self._export_R_ltail_ie.any():  # if we need to add left tail
            self._export_ltailpoints = int(
                round(self._export_R0[0] / self._export_res - 0.5),
            )
            self._export_ltailpoints = max(self._export_ltailpoints, 0)
            self._export_R_ltail = np.append(
                np.array([0]),
                np.linspace(
                    self._export_res / 2,
                    self._export_R0[0],
                    self._export_ltailpoints + 1,
                ),
            )
            #            k_ltail = (np.diff(self._export_U0[0:2]) / np.diff(self._export_R0[0:2]))
            #            a = ((self._export_U0[0] - Umax) - k_ltail * self._export_R0[0]) / (-self._export_R0[0] ** 2)
            #            b = k_ltail - 2 * self._export_R0[0] * a
            #            k_ltail = (np.diff(self._export_U0[0:6]) / np.diff(self._export_R0[0:6]))
            #            a = ((self._export_U0[0] - Umax) - np.mean(k_ltail) * self._export_R0[0]) / (-self._export_R0[0] ** 2)
            #            b = np.mean(k_ltail) - 2 * self._export_R0[0] * a
            #            self._export_U_ltail = np.square(self._export_R_ltail) * a + self._export_R_ltail * b + Umax

            k_ltail, intercept, r_value, p_value, std_err = stats.linregress(
                self._export_R0[0:6],
                self._export_U0[0:6],
            )
            b0 = self._export_R0[0] - k_ltail / 2 / tail_strength
            e0 = self._export_U0[0] - tail_strength * (self._export_R0[0] - b0) ** 2
            self._export_U_ltail = tail_strength * (self._export_R_ltail - b0) ** 2 + e0
            #            self._export_U_ltail = k_ltail*np.subtract(self._export_R_ltail, self._export_R0[0]) + self._export_U0[0]
            self._export_U_ltail = self._export_U_ltail[
                0 : len(self._export_U_ltail) - 1
            ]
            self._export_R_ltail = self._export_R_ltail[
                0 : len(self._export_R_ltail) - 1
            ]
        else:
            self._export_ltailpoints = 0
            self._export_U_ltail = np.array([])
            self._export_R_ltail = np.array([])

    def _export_right_tail_ie(self, Rmaxtable=0.0, tail_strength=0.0):
        self._export_U_rtail = []
        self._export_R_rtail = []

    def _export_join_and_interpolate(self, interpol=True, method="gauss"):
        import scipy.interpolate as sciint

        # Join all parts together
        self._export_U = np.append(
            self._export_U_ltail,
            np.append(self._export_U0, self._export_U_rtail),
        )
        self._export_R = np.append(
            self._export_R_ltail,
            np.append(self._export_R0, self._export_R_rtail),
        )
        # Interpolation and force calculation
        if "sciint" in method:
            rbf_inter = sciint.Rbf(self._export_R, self._export_U)
            self._export_U_ie = rbf_inter(self._export_R_ie)
        elif "gauss" in method:
            self._export_U_ie = self._gauss_interpol(
                self._export_R,
                self._export_U,
                self._export_R_ie,
                sigma=self._export_sigma,
            )
        else:
            raise ValueError("Unknown interpolation method: Try gauss or sciint")

        self._export_F_ie = -np.gradient(
            self._export_U_ie,
            self._export_R_ie[1] - self._export_R_ie[0],
        )

        if not interpol:
            for i in range(len(self._export_U0)):
                self._export_U_ie[len(self._export_R_ltail_ie) + i * 2] = (
                    self._export_U0[i]
                )

    def _export(
        self,
        npoints=2500,
        Umax=6000.0,
        Rmaxtable=25.0,
        tail_strength=2.51922,
        noplot=False,
        hardcopy=True,
        figsize=(14, 7.5),
        dpi=120,
        sigma=0.5,
        zeroforce=False,
        interpol=True,
        method="gauss",
        ofilename="",
        units=("A", "kJ/mol", "kJ/mol/A"),
        _convert=(1.0, 1.0, 1.0),
    ):
        self._export_prepare_init(
            npoints=npoints,
            Rmaxtable=Rmaxtable,
            sigma=sigma,
            interpol=interpol,
        )
        self._export_left_tail_ie(Umax=Umax, tail_strength=tail_strength)
        self._export_right_tail_ie(Rmaxtable=Rmaxtable, tail_strength=tail_strength)
        self._export_join_and_interpolate(interpol=interpol, method=method)

        if not noplot:
            import matplotlib.pyplot as plt

            self._export_plot(figsize=figsize, dpi=dpi, units=units)
            if hardcopy:
                plt.savefig(ofilename + ".png")

        if zeroforce:
            self._export_F_ie = self._export_F_ie * 0.0
        # Convert from default units: deg, kJ/mol, kJ/mol/deg  to the MDengine units: deg, kJ/mol, kJ/mol/deg
        self._export_R_ie = self._export_R_ie * _convert[0]
        self._export_U_ie = self._export_U_ie * _convert[1]
        self._export_F_ie = self._export_F_ie * _convert[2]

        return (
            self._export_R_ie.round(self.digits_to_round),
            self._export_U_ie.round(self.digits_to_round),
            self._export_F_ie.round(self.digits_to_round - 2),
        )


class Pot_AngleBond(Pot, DF_AngleBond):
    __doc__ = DF_AngleBond.__doc__

    def _export(
        self,
        npoints=1800,
        Rmaxtable=180.0,
        Umax=2000.0,
        units=("Deg", "kJ/mol", "kJ/mol/deg"),
        **kwargs,
    ):
        (R_ie, U_ie, F_ie) = super(Pot_AngleBond, self)._export(
            npoints=npoints,
            Rmaxtable=Rmaxtable,
            Umax=Umax,
            units=units,
            **kwargs,
        )
        R_ie[0] = 0.0
        return (R_ie, U_ie, F_ie)

    def _export_right_tail_ie(self, Rmaxtable=180.0, Umax=2000.0, tail_strength=0.0):
        """Right tail ie-polation."""
        if self._export_R_rtail_ie.any():  # if we need to add right tail
            self._export_rtailpoints = int(
                round((Rmaxtable - self._export_R0[-1]) / self._export_res - 0.5),
            )
            self._export_R_rtail = np.append(
                np.linspace(
                    self._export_R0[-1],
                    Rmaxtable - self._export_res / 2,
                    self._export_rtailpoints + 1,
                )[1:],
                np.array([Rmaxtable]),
            )
            if self._export_U0[-1] > 1.0e-5:  # assume U-shape
                k_rtail = np.diff(
                    self._export_U0[self.Npoints - 2 : self.Npoints],
                ) / np.diff(
                    self._export_R0[self.Npoints - 2 : self.Npoints],
                )
                self._export_U_rtail = (
                    k_rtail * (self._export_R_rtail - self._export_R0[-1])
                    + self._export_U0[-1]
                )
            else:
                self._export_U_rtail = (
                    np.exp(
                        -100.0
                        * (self._export_R_rtail - self._export_R0[-1])
                        / (Rmaxtable - self._export_R0[-1]),
                    )
                    * self._export_U0[-1]
                )
        else:
            self._export_rtailpoints = 0
            self._export_U_rtail = np.array([])
            self._export_R_rtail = np.array([])

    def _export_plot(self, units=("Deg", "kJ/mol", "kJ/mol/deg"), **kwargs):
        import matplotlib.pyplot as plt

        fig = plt.figure(**kwargs)
        ax1 = fig.add_subplot(211)
        plt.title(self.Name)
        ax1.plot(self._export_R, self._export_U, "y.")
        ax1.plot(self._export_R0, self._export_U0, "r.")
        ax1.plot(self._export_R_ie, self._export_U_ie, "b-")
        ax2 = ax1.twinx()
        ax2.plot(self._export_R_ie, self._export_F_ie, "g-", label="Force")
        ax1.set_xlim(
            2 * self._export_R[self._export_ltailpoints + 1]
            - self._export_R[self._export_ltailpoints + 2],
            2 * self._export_R[-1 - self._export_rtailpoints]
            - self._export_R[-2 - self._export_rtailpoints],
        )
        ax1.set_ylim(
            min(
                self._export_U[
                    self._export_ltailpoints : len(self._export_U)
                    - self._export_rtailpoints
                ],
            )
            * 0.8,
            max(
                self._export_U[
                    self._export_ltailpoints : len(self._export_U)
                    - self._export_rtailpoints
                ],
            )
            * 1.2,
        )
        ax1.set_xlabel(f"Angle, {units[0]}")

        ax2.set_xlim(
            2 * self._export_R[self._export_ltailpoints + 1]
            - self._export_R[self._export_ltailpoints + 2],
            2 * self._export_R[-1 - self._export_rtailpoints]
            - self._export_R[-2 - self._export_rtailpoints],
        )
        f_low_lim = min(
            self._export_F_ie[
                self._export_ltailpoints + 1 : len(self._export_F_ie)
                - self._export_rtailpoints
                + 2
            ],
        )
        f_upp_lim = max(
            self._export_F_ie[
                self._export_ltailpoints + 1 : len(self._export_F_ie)
                - self._export_rtailpoints
                + 2
            ],
        )
        f_margin = (f_upp_lim - f_low_lim) * 0.05
        ax2.set_ylim(f_low_lim - f_margin, f_upp_lim + f_margin)
        ax2.set_ylabel(f"Force {units[2]}")

        ax3 = fig.add_subplot(223)
        ax3.plot(self._export_R, self._export_U, "y.", label="Extrapolated tails")
        ax3.plot(self._export_R0, self._export_U0, "r.", label="Original potential")
        ax3.plot(
            self._export_R_ie,
            self._export_U_ie,
            "b-",
            label="Interpolated potential",
        )
        ax3.set_xlabel(f"Angle {units[0]}")
        ax3.set_ylabel(f"Potential {units[1]}")
        ax3.legend(
            ("Extrapolated tails", "Original potential", "Interpolated potential"),
            loc=0,
            fancybox=False,
        )

        ax5 = fig.add_subplot(224)
        ax5.plot(self._export_R, self._export_U, "yo", label="Extrapolated tails")
        ax5.plot(self._export_R, self._export_U, "ro", label="Original potential")
        ax5.plot(
            self._export_R_ie,
            self._export_U_ie,
            "b-",
            label="Interpolated potential",
        )
        ax5.set_xlabel(f"Angle {units[0]}")
        ax5.set_ylabel(f"Potential {units[1]}")
        ax5.set_xlim(self._export_R0[-20], self._export_R0[-1])
        ax5.set_ylim(min(self._export_U0[-20:]), max(self._export_U0[-20:]))

    def Export2Gromacs(self, **kwargs):
        if self.BondNumber is None:
            print(f"{self.Name} is not exported, since the bond number is not known")
            return
        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += (
                f"table_a{self.BondNumber:<d}.{self.MolTypeName:<}.xvg"
            )
            super(Pot_AngleBond, self).Export2Gromacs(
                _template="{0:12.6f}   {1:12.6f} {2:12.6f}\n",
                **kwargs,
            )

    def Export2GALAMOST(self, **kwargs):
        if self.BondNumber is None:
            print(f"{self.Name} is not exported, since the bond number is not known")
            return
        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += (
                f"table_{self.MolTypeName:<}-{self.BondNumber:<d}.dat"
            )
            super(Pot_AngleBond, self).Export2GALAMOST(
                _convert=(3.141592653589793 / 180.0, 1.0, 1.0),
                units=("Rad", "kJ/mol", "kJ/mol/deg"),
                _xmlheader="AnglePotential",
                **kwargs,
            )

    def Export2LAMMPS(self, **kwargs):
        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += "{0}.table".format(str(self.Name).replace(":", "."))
            super(Pot_AngleBond, self).Export2LAMMPS(**kwargs)

    def PotPressCorr(self, U_corr0):
        """Dummy method, only print information message that nothing was done."""
        print("No correction was applied to angle bending potential ", str(self.Name))


class Pot_PairBond(Pot, DF_PairBond):
    __doc__ = DF_PairBond.__doc__

    def _export_right_tail_ie(
        self,
        Rmaxtable=2.5,
        Umax=6000.0,
        tail_strength=2.51922,
    ):  # default strength for tail part ~5kT when T=303K
        """Right tail ie-polation, Now use a weak harmonic potential for the right tail."""
        from scipy import stats

        if self._export_R_rtail_ie.any():  # if we need to add left tail
            self._export_rtailpoints = int(
                round((Rmaxtable - self._export_R0[-1]) / self._export_res - 0.5),
            )
            self._export_R_rtail = np.append(
                np.linspace(
                    self._export_R0[-1],
                    Rmaxtable - self._export_res / 2,
                    self._export_rtailpoints + 1,
                )[1:],
                np.array([Rmaxtable]),
            )
            #            k_rtail = (np.diff(self._export_U0[self.Npoints - 2:self.Npoints])
            #                       / np.diff(self._export_R0[self.Npoints - 2:self.Npoints]))
            #            a = ((self._export_U0[-1] - Umax) - k_rtail * self._export_R0[-1]) / (-self._export_R0[-1] ** 2)
            #            b = k_rtail - 2 * self._export_R0[-1] * a
            #            k_rtail = (np.diff(self._export_U0[self.Npoints - 6:self.Npoints])
            #                       / np.diff(self._export_R0[self.Npoints - 6:self.Npoints]))
            #            a = ((self._export_U0[-1] - Umax) - np.mean(k_rtail) * self._export_R0[-1]) / (-self._export_R0[-1] ** 2)
            #            b = np.mean(k_rtail) - 2 * self._export_R0[-1] * a
            #            self._export_U_rtail = np.square(self._export_R_rtail) * a + self._export_R_rtail * b + Umax

            k_rtail, intercept, r_value, p_value, std_err = stats.linregress(
                self._export_R0[self.Npoints - 6 : self.Npoints],
                self._export_U0[self.Npoints - 6 : self.Npoints],
            )
            b0 = self._export_R0[-1] - k_rtail / 2 / tail_strength
            e0 = self._export_U0[-1] - tail_strength * (self._export_R0[-1] - b0) ** 2
            self._export_U_rtail = tail_strength * (self._export_R_rtail - b0) ** 2 + e0
        #            self._export_U_rtail = k_rtail * (self._export_R_rtail - self._export_R0[-1]) + self._export_U0[-1]
        else:
            self._export_rtailpoints = 0
            self._export_U_rtail = np.array([])
            self._export_R_rtail = np.array([])

    def _export_plot(self, figsize=(14, 7.5), dpi=120, units=None):
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax1 = fig.add_subplot(211)
        plt.title(self.Name)
        ax1.plot(self._export_R, self._export_U, "y.", label="Extrapolated tails")
        ax1.plot(self._export_R0, self._export_U0, "r.", label="Original potential")
        ax1.plot(
            self._export_R_ie,
            self._export_U_ie,
            "b-",
            label="Interpolated potential",
        )
        # ax1.legend(('Extrapolated tails', 'Original potential', 'Interpolated potential'),
        #                         loc=0, fancybox=False)
        ax1.set_ylabel(f"Potential {units[1]}")

        ax2 = ax1.twinx()
        ax2.plot(
            self._export_R_ie,
            self._export_F_ie,
            "g-",
            label="Force from IE-polated pot",
        )

        ax3 = fig.add_subplot(212)

        ax1.set_xlim(
            self._export_R0[0] - 2.0 * self._export_res,
            self._export_R0[-1] + 2.0 * self._export_res,
        )
        ax1.set_ylim(
            min(
                self._export_U[
                    self._export_ltailpoints : len(self._export_U)
                    - self._export_rtailpoints
                ],
            )
            * 0.8,
            max(
                self._export_U[
                    self._export_ltailpoints : len(self._export_U)
                    - self._export_rtailpoints
                ],
            )
            * 1.2,
        )
        ax1.set_xlabel(f"R, {units[0]}")
        ax2.set_ylabel(f"Force {units[2]}")
        ax2.set_xlim(
            self._export_R0[0] - 2.0 * self._export_res,
            self._export_R0[-1] + 2.0 * self._export_res,
        )
        ax2.set_ylim(
            min(
                self._export_F_ie[
                    self._export_ltailpoints + 1 : len(self._export_F_ie)
                    - self._export_rtailpoints
                ],
            ),
            max(
                self._export_F_ie[
                    self._export_ltailpoints + 1 : len(self._export_F_ie)
                    - self._export_rtailpoints
                ],
            ),
        )

        ax3.plot(self._export_R, self._export_U, "y.", label="Extrapolated tails")
        ax3.plot(self._export_R0, self._export_U0, "r.", label="Original potential")
        ax3.plot(
            self._export_R_ie,
            self._export_U_ie,
            "b-",
            label="Interpolated potential",
        )
        ax3.set_xlabel(f"R, {units[0]}")
        ax3.set_ylabel(f"Potential {units[1]}")
        ax3.legend(
            ("Extrapolated tails", "Original potential", "Interpolated potential"),
            loc=0,
            fancybox=False,
        )
        ax4 = ax3.twinx()
        ax4.plot(self._export_R_ie, self._export_F_ie, "g-", label="Force")
        ax4.legend(loc=7)

    def Export2Gromacs(self, **kwargs):
        if self.BondNumber is None:
            print(f"{self.Name} is not exported, since the bond number is not known")
            return

        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += (
                f"table_b{self.BondNumber:<d}.{self.MolTypeName:<}.xvg"
            )
            super(Pot_PairBond, self).Export2Gromacs(
                _template="{0:12.6f}   {1:12.6f} {2:12.6f}\n",
                _convert=(0.1, 1.0, 10.0),
                units=("A", "kJ/mol", "kJ/mol/A"),
                **kwargs,
            )

    def Export2GALAMOST(self, **kwargs):
        if self.BondNumber is None:
            print(f"{self.Name} is not exported, since the bond number is not known")
            return
        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += (
                f"table_{self.MolTypeName:<}-{self.BondNumber:<d}.dat"
            )
            super(Pot_PairBond, self).Export2GALAMOST(
                _convert=(0.1, 1.0, 0.0),
                units=("A", "kJ/mol", "kJ/mol/A"),
                _xmlheader="BondPotential",
                **kwargs,
            )

    def Export2LAMMPS(self, **kwargs):
        if (
            self.SameAsBond is None
        ):  # Only export if it is original potential (not linked)
            kwargs["ofilename"] += "{0}.table".format(str(self.Name).replace(":", "."))
            super(Pot_PairBond, self).Export2LAMMPS(**kwargs)

    def PotPressCorr(self, U_corr0):
        """Dummy method, only print information message that nothing was done."""
        print("No correction was applied to bond potential ", str(self.Name))


class Pot_NB(Pot, DF_NB):
    __doc__ = DF_NB.__doc__

    def __init__(
        self,
        Name=None,
        Min=None,
        Max=None,
        Npoints=None,
        AtomTypes=None,
        AtomGroups=None,
        g=None,
        BondNumber=None,
        MolTypeName=None,
        Lines=None,
        Ucut=None,
    ):
        Pot.__init__(
            self,
            Name=Name,
            Min=Min,
            Max=Max,
            Npoints=Npoints,
            AtomTypes=AtomTypes,
            AtomGroups=AtomGroups,
            g=g,
            BondNumber=BondNumber,
            MolTypeName=MolTypeName,
            Lines=Lines,
        )
        if Ucut is not None:
            self.g = self.g[:, self.y < Ucut]
        self.qq = None

    def _add_core(self, Umax=1000, FKJM=2.5193):
        """Adds repulsive core to the potential and sets Rmin=0.

        Needed when the potential is read from Magic output file
        """
        NA = int(round(self.Max / self.Resol))
        g_new = np.zeros((2, NA))
        g_new[0, :] = np.linspace(0, self.Max, NA, endpoint=False) + 0.5 * self.Resol
        g_new[:, -self.Npoints :] = self.g
        g_new[1, 0 : -self.Npoints] = (
            Umax + 100 * np.linspace(NA - 1, 0, NA)[0 : -self.Npoints]
        ) * FKJM
        self.g = g_new

    def _export(self, **kwargs):
        (R_ie, U_ie, F_ie) = super(Pot_NB, self)._export(**kwargs)
        # Make right hand tail zero for NB-potentials. Correct for artificial nonzero values provided by sciint
        if "method" in kwargs:
            if kwargs["method"] == "sciint":
                _convert = kwargs["_convert"][0]
                U_ie[R_ie > self.Max * _convert] = 0.0
                F_ie[R_ie > self.Max * _convert] = 0.0
        return (R_ie, U_ie, F_ie)

    def _export_right_tail_ie(self, Rmaxtable=2.5, tail_strength=0.0):
        """Right tail extrapolation."""
        assert Rmaxtable > self._export_R0[-1], (
            "The Rmaxtable value is smaller then Rmax of the original table"
        )
        self._export_rtailpoints = int(
            round((Rmaxtable - self._export_R0[-1]) / self._export_res - 0.5),
        )
        self._export_R_rtail = np.append(
            np.linspace(
                self._export_R0[-1],
                Rmaxtable - self._export_res / 2,
                self._export_rtailpoints + 1,
            )[1:],
            np.array([Rmaxtable]),
        )
        self._export_U_rtail = (
            np.exp(
                -5.0
                * (self._export_R_rtail - self._export_R0[-1])
                / (Rmaxtable - self._export_R0[-1]),
            )
            * self._export_U0[-1]
        )

        # Right tail extrapolation - experimental
        self._export_U_rtail = 0.0 * self._export_R_rtail

    def _export_plot(
        self,
        figsize=(14, 7.5),
        dpi=120,
        units=("A", "kJ/mol", "kJ/mol/A"),
    ):
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax1 = fig.add_subplot(211)
        plt.title(self.Name)
        ax3 = fig.add_subplot(212)
        ax1.plot(self._export_R, self._export_U, "y.")
        ax1.plot(self._export_R0, self._export_U0, "r.")
        ax1.plot(self._export_R_ie, self._export_U_ie, "b-")
        ax2 = ax1.twinx()
        ax2.plot(self._export_R_ie, self._export_F_ie, "g-", label="Force")
        ax1.set_xlabel(f"R, {units[0]}")
        ax1.set_ylabel(f"Potential {units[1]}")
        ax2.set_ylabel(f"Force {units[2]}")
        ax1.set_xlim(
            self._export_R[self._export_ltailpoints - 1],
            self._export_R[+2 - self._export_rtailpoints]
            if (self._export_rtailpoints > 2)
            else self._export_R[-1],
        )
        y_low_lim = min(
            self._export_U[
                self._export_ltailpoints + 1 : len(self._export_U)
                - self._export_rtailpoints
                + 2
            ],
        )
        y_upp_lim = max(
            self._export_U[
                self._export_ltailpoints + 1 : len(self._export_U)
                - self._export_rtailpoints
                + 2
            ],
        )
        y_margin = (y_upp_lim - y_low_lim) * 0.05
        ax1.set_ylim(y_low_lim - y_margin, y_upp_lim + y_margin)
        f_low_lim = min(
            self._export_F_ie[
                self._export_ltailpoints + 1 : len(self._export_F_ie)
                - self._export_rtailpoints
                + 2
            ],
        )
        f_upp_lim = max(
            self._export_F_ie[
                self._export_ltailpoints + 1 : len(self._export_F_ie)
                - self._export_rtailpoints
                + 2
            ],
        )
        f_margin = (f_upp_lim - f_low_lim) * 0.05
        ax2.set_ylim(f_low_lim - f_margin, f_upp_lim + f_margin)

        ax3.plot(self._export_R, self._export_U, "yo", label="Extrapolated tails")
        ax3.plot(self._export_R0, self._export_U0, "ro", label="Original potential")
        ax3.plot(
            self._export_R_ie,
            self._export_U_ie,
            "b-",
            label="Interpolated potential",
        )
        ax3.legend(
            ("Extrapolated tails", "Original potential", "Interpolated potential"),
            loc=0,
            fancybox=False,
        )
        ax3.set_xlabel(f"R, {units[0]}")
        ax3.set_ylabel(f"Potential {units[1]}")
        ax4 = ax3.twinx()
        ax4.plot(self._export_R_ie, self._export_F_ie, "g-", label="Force")
        ax4.set_ylabel(f"Force {units[2]}")
        ax4.legend(loc=7)

    def Export2Gromacs(self, **kwargs):
        kwargs["ofilename"] += f"table_{self.AtomTypes[0]}_{self.AtomTypes[1]}.xvg"
        super(Pot_NB, self).Export2Gromacs(
            _template="{0:12.6f}      0.000000     0.000000 {1:12.6f} {2:12.6f}     0.000000     0.000000\n",
            _convert=(0.1, 1.0, 10.0),
            **kwargs,
        )

    def Export2LAMMPS(self, **kwargs):
        kwargs["ofilename"] += f"{self.AtomTypes[0]}_{self.AtomTypes[1]}.table"
        super(Pot_NB, self).Export2LAMMPS(**kwargs)

    def Export2GALAMOST(self, **kwargs):
        kwargs["ofilename"] += "table_{0[0]}-{0[1]}.dat".format(sorted(self.AtomTypes))
        super(Pot_NB, self).Export2GALAMOST(
            _convert=(0.1, 1.0, 0.0),
            _xmlheader="PairPotential",
            **kwargs,
        )

    def GetWeight(self, eps, eps_orig, r1):
        """Get weight of the potentials tail in range R1:Rmax (A). The weight is defined as absolute value of integral of r^2*U(r)dr taken from R1 to Rmax.

        eps_orig is dielectric permittivity used for IMC calculation, while eps is dielectric permittivity used for current splitting of the potential on short-range ang electrostatic parts.
        """
        if r1 < self.Min:
            print("Error: r1 is less than r_min")
            return None
        U_sr_new = self.y + (
            (self.qq * 1.602e-19 * 1.602e-19 * 6.022e23)
            / (4.0 * 3.1416 * 8.85e-12 * 1.0e-10 * 1.0e3)
        ) * (1.0 / eps_orig - 1.0 / eps) * (1.0 / self.x)
        r2 = self.x**2
        range_ = np.where(self.x >= r1)
        weight = np.abs(np.sum(U_sr_new[range_] * r2[range_] * self.Resol))
        return weight

    def GetCharges(self, mcmfile, **kwargs):
        """Load charges to the atom types from molecular descriptions files (*.mcm)."""
        import MolType
        import System

        system = System.System()
        if not isinstance(mcmfile, type([])):
            mcmfile = [mcmfile]
        MolTypes = [MolType.MolType(mcm, system, **kwargs) for mcm in mcmfile]

        def _getQ(atom_types_):
            Q = [
                A.Charge
                for MT in MolTypes
                for A in MT.Atoms
                if A.AtomType.Name in atom_types_
            ]
            if len(Q) < 1:
                raise MTE.DFError(
                    f"Error: Can not detect atoms with type {self.AtomTypes[0]} in files {mcmfile}\nCheck your mcm files",
                )
            return Q

        Q1 = _getQ(self.AtomTypes[0])
        Q2 = _getQ(self.AtomTypes[1])

        if len(Q1) > 1 or len(Q2) > 1:
            print(
                "Warning: More than one atom is detected for the atom type. "
                "The charge value is taken from the first record.",
            )
        print(
            f"{self.AtomTypes[0]}, Charge {Q1[0]}  <-->  {self.AtomTypes[1]}, Charge {Q2[0]}",
        )
        self.qq = Q1[0] * Q2[0]

    def PotPressCorr(self, U_corr0):
        """Adding decaying linear correction, which suppose to improve pressure of represented system.

        Correction term is linear and has value of U_corr0 at point r=0, and value of 0 at r=rmax
        """
        print(
            "Applying correction to intermolecular potential ",
            str(self.Name),
            " Ucorr(0)=",
            str(U_corr0),
        )
        self.y += U_corr0 - (float(U_corr0) / self.Max) * self.x


class RDFref(RDF):
    """Class of reference RDFs. It differs from parent only in line thickness in plot() method."""

    def __init__(self, *args, **kwargs):
        super(RDF, self).__init__(*args, **kwargs)
        self.plot_kwargs["linewidth"] = 2


class RDFref_NB(RDFref, DF_NB):
    __doc__ = DF_NB.__doc__


class RDFref_PairBond(RDFref, DF_PairBond):
    __doc__ = DF_PairBond.__doc__


class RDFref_AngleBond(RDFref, DF_AngleBond):
    __doc__ = DF_AngleBond.__doc__
