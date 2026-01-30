from numpy import array, diag, loadtxt

from . import MTException as MTE
from .object_magictools import ObjectMagicTools


class Trajectory(ObjectMagicTools):
    """Base class representing trajectory. Has two methods, to Connect to the trajectory and to read configuration from the trajectory."""

    def __init__(self, file_, type_, start, stop, step, natoms):
        super(Trajectory, self).__init__()
        self.file = file_
        self.type = type_
        self.start = start
        self.stop = stop
        self.step = step
        self.current = self.start
        self.natoms = natoms
        self.conf = None
        self.box = None
        self.ofile = None
        self._pID_ = 0  # Parallel ID
        self._pSize_ = 1  # Size of parallel processes pool

    def ReadConf(self):
        pass

    def Connect(self, **kwargs):
        pass

    def GetAtomNames(self):
        """Return a list of atom names if available, otherwise None.

        Has to be defined in child-classes
        """
        return

    def Split(self, N):
        """Create N instances of trajectory, based on the present one.

        They will have individual starting frame (number of frames skipped
        at the beginning of trajectory file, to provide independent parallel accumulation of RDF data)
        """
        if not (isinstance(N, int) and N > 0):
            raise MTE.TrajError(f"Wrong number of splits stated {N}:")

        lst = []
        for i in range(N):
            T = self.__class__(
                self.file,
                self.type,
                self.start,
                self.stop,
                self.step,
                self.natoms,
            )
            T._pID_ = i
            T._pSize_ = N
            lst.append(T)
        return lst

    def Open2Write(self, ofilename):
        """Open file for writing the trajectory."""
        if self.ofile:
            raise MTE.TrajError(f"The file {ofilename} is already opened for writing:")
        try:
            self.ofile = open(ofilename, "w")
        except:
            raise MTE.TrajError(
                f"unable to open file {ofilename} for writing the trajectory:",
            )

    def Close(self):
        """Close the output file."""
        self.ofile.close()
        self.ofile = None


class XMOL_Trajectory(Trajectory):
    """Subclass of Trajectory working with XMOL-file format."""

    def Connect(self, restart=False):
        """Connect to the trajectory."""
        assert self.type.upper() == "XMOL"
        if restart:
            self.current = self.start
        try:
            if "xmol" in self.file:
                self.file = self.file.split(".xmol")[0]
            filename = self.file + ".xmol"
            self._ifile = open(filename)
            print("Trajectory file:" + filename + " connected")
        except:
            filename = self.file + "." + str(self.current).zfill(3)
            try:
                self._ifile = open(filename)
                print("Trajectory file:" + filename + " connected")
            except:
                raise MTE.TrajError("unable to open trajectory file:" + filename)
        try:
            # Make offset due to parallel reading of the trajectory: Skip first Step*pID frames
            for _ in range((self.natoms + 2) * (self.step * self._pID_)):
                self._ifile.readline()
        except:
            raise MTE.TrajError(
                f"Can not make {self.step * self._pID_} frames offset for parallel reading file {filename}, pID {self._pID_}:",
            )

    def GetAtomNames(self):
        self.Connect(restart=True)
        names = [self._ifile.readline().split()[0] for i in range(self.natoms + 2)][2:]
        return names

    def ReadConf(self):
        """Read configuration from the trajectory."""
        # Check if the file connected refers to given trajectory
        ll = [self._ifile.readline() for i in range(self.natoms + 2)]
        # Skip following self.step-1 configurations if necessary
        for _ in range((self.natoms + 2) * (self.step * self._pSize_ - 1)):
            self._ifile.readline()
        # Check if EOF reached
        if "" in ll:  # EOF reached - proceed to next trajectory file
            if self.current < self.stop:
                self._ifile.close()
                self.current = self.current + 1
                self.Connect()
                eofff = self.ReadConf()
                return eofff
            return 1
            # EOF not reached, analyzing lines
            # Check number of atoms in the first configuration of file:
        natoms = int(ll.pop(0))
        lbox = ll.pop(0)
        if natoms != self.natoms:
            raise MTE.TrajError(
                f"Number of atoms stated in trajectory header: {natoms} "
                f"is incosistent with systems description:{self.natoms}\n",
            )

        # Reading box size
        if "BOX" in lbox:
            self.box = array([float(i) for i in lbox.strip().split("BOX:")[1].split()])
        try:
            self.conf = loadtxt(ll, dtype=float, usecols=(1, 2, 3))
            return 0
        except:
            raise MTE.TrajError("Error in trajectory file")

    def SkipConf(self, nskip):
        """Skips n configurations from reading."""
        for _ in range((self.natoms + 2) * nskip):
            self._ifile.readline()


class Gromacs_Trajectory(Trajectory):
    """Subclass of Trajectory working with GROMACS trajectory file formats: trr, xdr."""

    def __init__(self, *args):
        super(Gromacs_Trajectory, self).__init__(*args)
        self.__EOF__ = False

    def Connect(self, **kwargs):
        """Connect to the trajectory."""
        import mdtraj

        self.__EOF__ = False
        try:
            self.trj = mdtraj.open(self.file)
            print("Trajectory file:" + self.file + " connected")
        except:
            raise MTE.TrajError("unable to open trajectory file:" + self.file)

        r, time, step, box = self.trj.read(1)
        if len(r[0]) != self.natoms:
            raise MTE.TrajError("N Atoms in trajectory != Natoms in system description")
        try:
            # Make offset due to parallel reading of the trajectory: Skip first Step*pID frames
            self.trj.seek(self.step * self._pID_)
        except:
            raise MTE.TrajError(
                f"Can not make {self.step * self._pID_} frames offset for parallel reading file {self.file}, pID {self._pID_}:",
            )

    def ReadConf(self):
        """Read configuration from the trajectory."""
        # read a frame

        if self.__EOF__:
            return 1

        try:
            r, time, step, box = self.trj.read(1)
            # Skip follwing self.step-1 configurations if necessary
            self.trj.seek(offset=self.step * self._pSize_ - 1, whence=1)
        except:
            # if EOF reached
            self.__EOF__ = True

        if len(r) == 0:  # if EOF reached
            self.__EOF__ = True
            return 1
        # EOF not reached, analyzing lines
        # Reading box size
        self.box = array(diag(box[0]) * 10.0)
        self.conf = array(r[0] * 10.0)
        return 0
