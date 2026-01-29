class Operations:

    def __init__(self):
        """ Initialise default values for both operations """
        self.implication_value = 1
        self.conjunction_value = 0

    @staticmethod
    def get_conjunction_from_vals(a, b):
        """ Calculates conjunction and returns value """
        val = a + b - 1
        return val

    @staticmethod
    def get_implication_from_vals(a, b):
        """ Calculates implication and returns value """
        val = 1 - a + b
        return val

    def calculate_lukasiewicz_values(self, fuzzy_set_weight, orig_data_value):
        """ Calculates both operations """
        self.implication(fuzzy_set_weight, orig_data_value)
        self.conjunction(fuzzy_set_weight, orig_data_value)

    def conjunction(self, a, b):
        """ calculates conjunction and UPDATES current values based on input values """
        val = self.get_conjunction_from_vals(a, b)
        val = min(1, val)
        self.update_conjunction_val(val)

    def implication(self, a, b):
        """ Calculates implication and UPDATES current values based on input values """
        val = self.get_implication_from_vals(a, b)
        val = max(0, val)
        self.update_implication_val(val)

    def get_conjunction_value(self):
        """ Returns current value of conjunction """
        return self.conjunction_value

    def get_implication_value(self):
        """ Returns current value of implication """
        return self.implication_value

    def update_conjunction_val(self, val):
        """ Updates current SELF.CONJUNCTION value """
        if val > self.conjunction_value:
            self.conjunction_value = val

    def update_implication_val(self, val):
        """ Updates current SELF.IMPLICATION value """
        if val < self.implication_value:
            self.implication_value = val

    def set_default_vals(self):
        """ Resets Implication and Conjunction value to its default values """
        self.implication_value = 1
        self.conjunction_value = 0


