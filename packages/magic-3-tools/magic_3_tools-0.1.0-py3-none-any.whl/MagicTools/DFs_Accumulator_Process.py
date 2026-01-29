"""Created on Wed Apr 20 22:15:01 2016.

@author: sasha
"""

import multiprocessing

import numpy as np

from . import DF
from . import MTException as MTE


class RDFs_Accumulator_Process(
    multiprocessing.Process,
):  # TODO: Make correct behavior when crush with exception
    def __init__(self, Traj, DFs, ID, queue, RDFcalculator, Box=None):
        super(
            RDFs_Accumulator_Process,
            self,
        ).__init__()  # as in example - call constructor if the parent  class
        self.ID = ID
        self.Traj = Traj
        self.DFs = DFs
        self.Box = np.array(Box) if np.any(Box) else None
        self.DFs_ghist = [np.zeros(len(DF._ghist)) for DF in self.DFs]
        self._box_ac = np.zeros(3, dtype=float)
        self.RDFcalculator = RDFcalculator

        self.queue = queue

    def run(self):
        self.Traj.Connect()
        eof = self.Traj.ReadConf()
        conf = 0

        if (self.Box is None) and (self.Traj.box is None):
            raise MTE.DFsAccumulatorError(
                "Error: No box provided neither in the input file nor in the trajectory. Exiting.",
            )
        while eof == 0:
            if self.Traj.box is not None:
                box = self.Traj.box
            else:
                box = self.Box
            self._box_ac = self._box_ac + box

            for irdf in range(len(self.DFs)):
                rdf = self.DFs[irdf]
                c = self.Traj.conf
                if self.RDFcalculator._opt_memory_use and isinstance(rdf, DF.RDF_NB):
                    rdf._pairslist = self.RDFcalculator._RDF_NB_pairs_matrix_generator(
                        rdf,
                    )

                for chunk_ in rdf._pairslist:
                    dr = c[chunk_[1]] - c[chunk_[0]]
                    dr = np.abs(dr)
                    dr = np.abs(dr - np.round(np.divide(dr, box), 0) * box)
                    drr = np.sqrt(np.sum(np.square(dr), axis=1))
                    drr[drr < rdf.Min] = 0.0
                    drr[drr >= rdf.Max] = 0.0
                    i = (drr / rdf.Resol).astype(int)
                    self.DFs_ghist[irdf] = (
                        self.DFs_ghist[irdf]
                        + np.bincount(i, minlength=len(self.DFs_ghist[irdf]))[
                            0 : len(self.DFs_ghist[irdf])
                        ]
                    )
            print(
                (f"Process {self.ID}: Configuration {conf}: analyzed"),
                end="\r",
            )
            eof = self.Traj.ReadConf()
            conf += 1
        print("\n")
        self.queue.put((self.DFs_ghist, self._box_ac, conf))


class ADFs_Accumulator_Process(multiprocessing.Process):
    def __init__(self, Traj, DFs, ID, queue):
        super(
            ADFs_Accumulator_Process,
            self,
        ).__init__()  # as in example - call constructor if the parent  class
        self.ID = ID
        self.Traj = Traj
        self.DFs = DFs
        self.DFs_ghist = [np.zeros(len(DF._ghist)) for DF in self.DFs]
        self.queue = queue

    def run(self):
        # Loop over trajectory configurations, counting pairs
        self.Traj.Connect()
        eof = self.Traj.ReadConf()
        conf = 0
        while eof == 0:
            for iadf, adf in enumerate(self.DFs):
                c = self.Traj.conf
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
                self.DFs_ghist[iadf] += np.bincount(
                    i,
                    minlength=len(self.DFs_ghist[iadf]),
                )
            print(
                (f"Process {self.ID}: Configuration {conf}: analyzed"),
                end="\r",
            )
            eof = self.Traj.ReadConf()
            conf += 1
        print("\n")
        self.queue.put((self.DFs_ghist, conf))
