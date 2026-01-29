from .fuzzy_set_basic import FuzzySetBasic


class FuzzySet(FuzzySetBasic):
    """Fuzzy set definition, LINEAR shape"""

    def __repr__(self):
        return "<FuzzySet Linear kernel_start:%s kernel_end:%s fuzzy_set_width:%s>" % (
            self.kernel_start,
            self.kernel_end,
            self.fuzzy_set_width,
        )
