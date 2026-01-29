import numpy as np
from .operations import Operations


class Transform:

    def __init__(self, original_data_x, original_data_y, fuzzy_set, fuzzy_density):

        #  INPUT data values
        self.original_data_x = original_data_x
        self.normalised_original_data_y = original_data_y

        # Fuzzy set definition
        self.fuzzy_set = fuzzy_set
        self.fuzzy_density = fuzzy_density

        self.actual_fuzzy_set_first_x = 0
        self.actual_fuzzy_set_step_x = 0
        self.actual_fuzzy_set_last_x = 0

        self.operations = Operations()

        # UPPER approx
        self.upper_t_fw_data_x = []
        self.upper_t_fw_data_y = []
        self.upper_t_inv_data_y = []

        # BOTTOM approx
        self.bottom_t_fw_data_x = []
        self.bottom_t_fw_data_y = []
        self.bottom_t_inv_data_y = []

    ####################################################
    # FW TRANSFORM #####################################
    ####################################################

    def upper_bottom_forward_ft(self):
        """Calculates FW values for both approximations and creates arrays"""
        for for_x in range(
            self.original_data_x[0],
            self.original_data_x[self.original_data_x.size - 1],
            self.fuzzy_density,
        ):
            self.calculate_fw_values_for_x(
                for_x
            )  # calculates for each point its FW values

        self.calculate_fw_values_for_x(
            self.upper_t_fw_data_x[len(self.upper_t_fw_data_x) - 1] + self.fuzzy_density
        )  # calculates FW vals for last element

        # transpose lists into arrays
        self.upper_t_fw_data_x = np.asarray(self.upper_t_fw_data_x)
        self.upper_t_fw_data_y = np.asarray(self.upper_t_fw_data_y)
        #  Convert bottom arrays to numpy arrays as well
        self.bottom_t_fw_data_x = np.asarray(self.bottom_t_fw_data_x)
        self.bottom_t_fw_data_y = np.asarray(self.bottom_t_fw_data_y)

    def calculate_fw_values_for_x(self, for_x):
        """Calculates values for FW FT"""
        self.operations.set_default_vals()  # resets into default operation values
        self.set_fuzzy_set_range(for_x)  # sets actual "active" fuzzy set range

        for curr_x in range(
            self.actual_fuzzy_set_first_x,
            self.actual_fuzzy_set_last_x,
            self.actual_fuzzy_set_step_x,
        ):
            if self.curr_x_out_of_data_x_range(
                curr_x
            ):  # prevents outbox point to be calculated
                continue
            self.calculate_fw_value_for_curr_x(
                curr_x
            )  # calculates FW values for this "fuzzy set" and "curr_x"

        self.append_y_do_transform_array()

        return True

    def append_x_to_transform_array(self, x):
        """Append to FW X list to be calculated"""
        self.upper_t_fw_data_x.append(x)
        self.bottom_t_fw_data_x.append(x)

    def get_position_of_curr_x_in_orig_range(self, curr_x):
        """Position curr_x in input data"""
        position_array = np.where(self.original_data_x == curr_x)
        position_el = self.original_data_x[position_array]
        position = position_el[0]
        return position

    def calculate_fw_value_for_curr_x(self, curr_x):
        """Calculates FW values for actual curr_x"""
        fuzzy_set_weight = self.fuzzy_set.get_fuzzy_set_value(
            curr_x - self.actual_fuzzy_set_first_x
        )
        position = self.get_position_of_curr_x_in_orig_range(curr_x)
        orig_data_value = float(self.normalised_original_data_y[position])
        orig_data_value = round(orig_data_value, 2)  # DELTE ???? round

        self.operations.calculate_lukasiewicz_values(fuzzy_set_weight, orig_data_value)

    def append_y_do_transform_array(self):
        """prilepi x do vysupniho array pro FW hodnoty"""
        self.upper_t_fw_data_y.append(self.operations.get_conjunction_value())
        self.bottom_t_fw_data_y.append(self.operations.get_implication_value())

    def clear_current_fuzzy_set_range(self):
        """Resets current fuzzy set settings"""
        self.actual_fuzzy_set_first_x = 0
        self.actual_fuzzy_set_step_x = 0
        self.actual_fuzzy_set_last_x = 0

    def curr_x_out_of_data_x_range(self, curr_x, limit=0):
        """Controls, if is x in interval of input data"""
        ret = False
        if curr_x < self.original_data_x[0]:
            ret = True
        if curr_x > self.original_data_x[-1]:
            ret = True
        return ret

    ####################################################
    #  end -- FW TRANSFORM ###########################
    ####################################################

    ###########################################################
    # INVERSE F-TRANSFORM #####################################
    ###########################################################

    # 1
    # příprava vstupních polí pro inverzní FT
    def initiate_inv_array(self):
        """Preparation"""
        # Initialisation of empty array for INVERSION Trasforms
        for element in self.original_data_x:
            self.upper_t_inv_data_y.append(1.00)
            self.bottom_t_inv_data_y.append(0.00)
        # conversion from list to array
        self.upper_t_inv_data_y = np.asarray(self.upper_t_inv_data_y)
        self.bottom_t_inv_data_y = np.asarray(self.bottom_t_inv_data_y)

    # 2
    def calculate_inverse_ft(self):

        self.initiate_inv_array()

        # for every point of FT transform calculate Inverse FT
        for forward_points_x in self.upper_t_fw_data_x:
            self.calc_inv_val_for_fw_x(forward_points_x)

    # 3
    # add values for all points of current FS
    def calc_inv_val_for_fw_x(self, for_x):

        # calculates position of FS
        self.set_fuzzy_set_range(for_x, False)

        # FW value of appropriate FT
        position_fw_ft = self.get_position_of_curr_x_in_fw_ft_range(for_x)

        # values of FW transforms
        fw_ft_upper_value = round(float(self.upper_t_fw_data_y[position_fw_ft]), 2)
        fw_ft_bottom_value = round(float(self.bottom_t_fw_data_y[position_fw_ft]), 2)

        # projdeme celý rozsah fuzzy množiny a pro každý bod spočítáme a přičteme hodnotu
        # loops through whole interval of FS
        for curr_x in range(
            self.actual_fuzzy_set_first_x,
            self.actual_fuzzy_set_last_x,
            self.actual_fuzzy_set_step_x,
        ):

            # sanitise border points outside of FS base
            if self.curr_x_out_of_data_x_range(curr_x, limit=self.fuzzy_density):
                continue

            fuzzy_set_weight = self.fuzzy_set.get_fuzzy_set_value(
                curr_x - self.actual_fuzzy_set_first_x
            )

            upper_inv_val = self.operations.get_implication_from_vals(
                fuzzy_set_weight, fw_ft_upper_value
            )
            bottom_inv_val = self.operations.get_conjunction_from_vals(
                fuzzy_set_weight, fw_ft_bottom_value
            )

            if upper_inv_val > 1:
                upper_inv_val = 1

            if upper_inv_val < self.upper_t_inv_data_y[curr_x]:
                self.upper_t_inv_data_y[curr_x] = upper_inv_val

            if bottom_inv_val > self.bottom_t_inv_data_y[curr_x]:
                self.bottom_t_inv_data_y[curr_x] = bottom_inv_val

    def get_position_of_curr_x_in_fw_ft_range(self, curr_x):
        """Calculates position curr_x"""
        position_array = np.where(self.upper_t_fw_data_x == curr_x)
        position_a = position_array[0]
        position_b = position_a[0]
        return position_b

    ###########################################################
    # end - INVERSE F-TRANSFORM #############################
    ###########################################################

    ####################################################
    # CUSTOM ###########################################
    ####################################################

    def set_fuzzy_set_range(self, for_x, append_to_array=True):
        """Sets absolute values for current fuzzy set"""
        self.clear_current_fuzzy_set_range()  # reset values

        self.actual_fuzzy_set_first_x = for_x - (
            getattr(self.fuzzy_set, "middle_point")
            - getattr(self.fuzzy_set, "fuzzy_set_start")
        )
        self.actual_fuzzy_set_step_x = getattr(self.fuzzy_set, "step_size")
        self.actual_fuzzy_set_last_x = for_x + (
            getattr(self.fuzzy_set, "fuzzy_set_width")
            - getattr(self.fuzzy_set, "middle_point")
        )

        # append value of fuzzy set for FW FT
        if append_to_array is True:
            self.append_x_to_transform_array(for_x)

    def return_input_param_and_approx(self):
        """Return all approximations, input data, fuzzy set instance and fuzzy set push"""
        result = {
            "original_data_x": self.original_data_x,
            "normalised_original_data_y": self.normalised_original_data_y,
            "upper_t_fw_data_x": self.upper_t_fw_data_x,
            "upper_t_fw_data_y": self.upper_t_fw_data_y,
            "upper_t_inv_data_y": self.upper_t_inv_data_y,
            "bottom_t_fw_data_x": self.bottom_t_fw_data_x,
            "bottom_t_fw_data_y": self.bottom_t_fw_data_y,
            "bottom_t_inv_data_y": self.bottom_t_inv_data_y,
        }
        return result
