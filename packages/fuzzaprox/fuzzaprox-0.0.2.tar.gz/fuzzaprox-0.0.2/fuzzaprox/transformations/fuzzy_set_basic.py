import numpy as np


class FuzzySetBasic:
    """ Fuzzy set definition, as well return its weights for any point on x-axis """

    def __init__(self, fuzzy_set):
        """ Initialise Fuzzy set with entered parameters """
        self.fuzzy_set_start = 0
        self.kernel_start = fuzzy_set["kernel_start"]
        self.kernel_end = fuzzy_set["kernel_end"]
        self.fuzzy_set_width = fuzzy_set["fuzzy_set_width"]

        self.middle_point = fuzzy_set["kernel_start"] + int(
            (fuzzy_set["kernel_end"] - fuzzy_set["kernel_start"]) / 2)  # middle - in case of special shape

        self.step_size = 1  # smallest step on its interval

    def get_fuzzy_set_value(self, x):
        """ Calculates weight of fuzzy set - values from 0 to 1 """

        self.middle_point = self.kernel_start + int((self.kernel_end - self.kernel_start) / 2)

        ret = 0
        if x < self.fuzzy_set_start or x > self.fuzzy_set_width:  # outside fuzzy set base
            ret = 0
        elif x <= self.kernel_start:
            ret = (x - self.fuzzy_set_start) / \
                  (self.kernel_start - self.fuzzy_set_start)
        elif x <= self.kernel_end:
            ret = 1
        elif x <= self.fuzzy_set_width:
            ret = 1 - ((x - self.kernel_end) /
                       (self.fuzzy_set_width - self.kernel_end))
        return ret

    def get_length(self):
        """ Returns fuzzy set length """
        return self.fuzzy_set_width - 1

    def draw_fuzzy_set(self, start, end):
        i = 0
        fuzzy_set_x = []
        fuzzy_set_y = []
        while i <= self.fuzzy_set_width:
            if 0 <= (start + i) <= end:
                fuzzy_set_x.append(i + start)
                fuzzy_set_y.append(-(self.get_fuzzy_set_value(i)) / 4)
            i += 1

        fuzzy_set_x_array = np.asarray(fuzzy_set_x)
        fuzzy_set_y_array = np.asarray(fuzzy_set_y)

        fuzzy_set_graph = {"x": fuzzy_set_x_array, "y": fuzzy_set_y_array}
        return fuzzy_set_graph

    def get_values_as_dict(self) -> dict:
        ret = {"kernel_start": self.kernel_start,
               "kernel_end": self.kernel_end,
               "fuzzy_set_width": self.fuzzy_set_width}
        return ret

    def __repr__(self):
        """"""
        return "<FuzzySet kernel_start:%s kernel_end:%s fuzzy_set_width:%s>" % (self.kernel_start,
                                                                                self.kernel_end,
                                                                                self.fuzzy_set_width)
