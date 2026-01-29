class MT_Exception(Exception):
    """Base class for exceptions in MagicTools."""


class GeneralError(MT_Exception):
    """General non-specific Error in MagicTools."""

    # def __init__(self, msg):
    #     self.message = msg
    #     print(self.message)
    #     super(GeneralError, self).__init__(self, self.message)


class InputValueError(GeneralError):
    """Error in input file."""


class AtomError(GeneralError):
    pass


class MolTypeError(GeneralError):
    pass


class MCMError(GeneralError):
    """Class for reporting MCMfile-related errors."""


class TrajError(GeneralError):
    """Class for reporting Trajectory file-related errors."""


class RDFError(GeneralError):
    """Class for reporting RDF-related errors."""


class RDFCalculatorError(GeneralError):
    pass


class RDFReadError(RDFError):
    """Class for reporting errors while reading RDF input file."""


class MagicToolsError(GeneralError):
    pass


class DFsetError(GeneralError):
    pass


class DFError(GeneralError):
    pass


class DFsAccumulatorError(GeneralError):
    pass
