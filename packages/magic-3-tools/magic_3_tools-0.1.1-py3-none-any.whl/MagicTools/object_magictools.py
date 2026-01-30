class ObjectMagicTools:
    """Class derived from class object, but having method _clear_cached().

    This class will be used as parent class for all MagicTools classes.
    """

    def __init__(self):
        self._cached = dict()

    def _clear_cached(self):
        self._cached = dict.fromkeys(self._cached.keys())

    def __str__(self):
        try:
            if self.Name is not None:
                return self.Name
        except:
            pass
        return super(ObjectMagicTools, self).__repr__()

    __repr__ = __str__
