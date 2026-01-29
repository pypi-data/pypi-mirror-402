"""
Unit tests for Fuzzaprox class
"""
import pytest

import numpy as np
from fuzzaprox import Fuzzaprox
from fuzzaprox.transformations import FuzzySet


class TestFuzzaproxInitialization:
    """Test Fuzzaprox initialization"""
    
    def test_init(self):
        """Test that Fuzzaprox initializes with correct default values"""
        fa = Fuzzaprox()
        assert fa.fuzzy_set_instance is None
        assert fa.fuzzy_set_push is None
        assert fa.transformation is None
        assert fa.data_x is None
        assert fa.norm_data_y is None
        assert fa.orig_data_y is None


class TestFuzzaproxStaticMethods:
    """Test static methods of Fuzzaprox"""
    
    def test_convert_list_to_array_with_list(self):
        """Test convert_list_to_array with a list input"""
        test_list = [1, 2, 3, 4, 5]
        result = Fuzzaprox.convert_list_to_array(test_list)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, np.array([1, 2, 3, 4, 5]))
    
    def test_convert_list_to_array_with_array(self):
        """Test convert_list_to_array with a numpy array input"""
        test_array = np.array([1, 2, 3, 4, 5])
        result = Fuzzaprox.convert_list_to_array(test_array)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, test_array)
        # Should return a copy to prevent external modifications affecting internal state
        assert result is not test_array
        # Verify it's a copy by modifying original and checking result is unchanged
        test_array[0] = 999
        assert result[0] == 1  # Result should be unchanged
    
    def test_convert_list_to_array_with_invalid_type(self):
        """Test convert_list_to_array raises error for invalid input type"""
        with pytest.raises(ValueError, match="Data should be in list or np.ndarray format"):
            Fuzzaprox.convert_list_to_array("invalid")
    
    def test_generate_x_axis_from_y_list(self):
        """Test generate_x_axis_from_y_list generates correct indices"""
        y_array = np.array([1, 2, 3, 4, 5])
        result = Fuzzaprox.generate_x_axis_from_y_list(y_array)
        expected = np.arange(5, dtype=int)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, expected)
        assert result.dtype == int
    
    def test_generate_x_axis_from_y_list_empty(self):
        """Test generate_x_axis_from_y_list with empty array"""
        y_array = np.array([])
        result = Fuzzaprox.generate_x_axis_from_y_list(y_array)
        expected = np.array([], dtype=int)
        assert np.array_equal(result, expected)


class TestFuzzaproxFuzzySetMethods:
    """Test fuzzy set related methods"""
    
    def test_define_fuzzy_set(self):
        """Test define_fuzzy_set creates fuzzy set correctly"""
        fa = Fuzzaprox()
        fa.define_fuzzy_set(base_start=0, kernel_start=12, kernel_end=14, base_end=26)
        
        assert fa.fuzzy_set_instance is not None
        assert isinstance(fa.fuzzy_set_instance, FuzzySet)
        assert fa.fuzzy_set_instance.kernel_start == 12
        assert fa.fuzzy_set_instance.kernel_end == 14
        assert fa.fuzzy_set_instance.fuzzy_set_width == 26
        # fuzzy_set_push should be set to half of fuzzy_set_width
        assert fa.fuzzy_set_push == 13  # 26/2
    
    def test_set_fuzzy_set(self):
        """Test set_fuzzy_set with dictionary"""
        fa = Fuzzaprox()
        fuzzy_set_dict = {
            'kernel_start': 5,
            'kernel_end': 10,
            'fuzzy_set_width': 20
        }
        fa.set_fuzzy_set(fuzzy_set_dict)
        
        assert fa.fuzzy_set_instance is not None
        assert isinstance(fa.fuzzy_set_instance, FuzzySet)
        assert fa.fuzzy_set_instance.kernel_start == 5
        assert fa.fuzzy_set_instance.kernel_end == 10
        assert fa.fuzzy_set_instance.fuzzy_set_width == 20
    
    def test_set_fuzzy_set_with_instance(self):
        """Test set_fuzzy_set_with_instance"""
        fa = Fuzzaprox()
        # First create a fuzzy set instance
        original_instance = FuzzySet({
            'kernel_start': 3,
            'kernel_end': 7,
            'fuzzy_set_width': 15
        })
        fa.set_fuzzy_set_with_instance(original_instance)
        
        assert fa.fuzzy_set_instance is not None
        assert fa.fuzzy_set_instance is original_instance
    
    def test_set_fuzzy_set_push(self):
        """Test set_fuzzy_set_push"""
        fa = Fuzzaprox()
        fa.set_fuzzy_set_push(20)
        assert fa.fuzzy_set_push == 10  # Should be half of input


class TestFuzzaproxInputData:
    """Test input data methods"""
    
    def test_set_input_data_with_list(self):
        """Test set_input_data with list"""
        fa = Fuzzaprox()
        y_values = [1, 2, 3, 4, 5]
        fa.set_input_data(y_values)
        
        assert fa.orig_data_y == y_values
        assert fa.norm_data_y is not None
        assert isinstance(fa.norm_data_y, np.ndarray)
        assert fa.data_x is not None
        assert isinstance(fa.data_x, np.ndarray)
        assert len(fa.data_x) == len(y_values)
    
    def test_set_input_data_with_array(self):
        """Test set_input_data with numpy array"""
        fa = Fuzzaprox()
        y_values = np.array([1, 2, 3, 4, 5])
        fa.set_input_data(y_values)
        
        assert np.array_equal(fa.orig_data_y, y_values)
        assert fa.norm_data_y is not None
        assert isinstance(fa.norm_data_y, np.ndarray)
    
    def test_set_input_data_normalizes(self):
        """Test that set_input_data normalizes data to [0,1]"""
        fa = Fuzzaprox()
        y_values = [10, 20, 30, 40, 50]
        fa.set_input_data(y_values)
        
        # Normalized values should be in [0, 1]
        assert np.all(fa.norm_data_y >= 0)
        assert np.all(fa.norm_data_y <= 1)
        # Minimum value should be 0 and maximum should be 1 (but not necessarily at first/last positions)
        assert np.min(fa.norm_data_y) == 0.0, f"Expected min=0.0, got {np.min(fa.norm_data_y)}"
        assert np.max(fa.norm_data_y) == 1.0, f"Expected min=0.0, got {np.max(fa.norm_data_y)}"
    
    def test_set_input_data_generates_x_axis(self):
        """Test that set_input_data generates correct x-axis"""
        fa = Fuzzaprox()
        y_values = [1, 2, 3, 4, 5]
        fa.set_input_data(y_values)
        
        expected_x = np.arange(5, dtype=int)
        assert np.array_equal(fa.data_x, expected_x)


class TestFuzzaproxRun:
    """Test run method"""
    
    def test_run_requires_fuzzy_set(self):
        """Test that run requires fuzzy set to be set"""
        fa = Fuzzaprox()
        fa.set_input_data([1, 2, 3, 4, 5])
        
        # Should raise an error or fail when fuzzy_set_instance is None
        with pytest.raises((AttributeError, TypeError)):
            fa.run()
    
    def test_run_requires_input_data(self):
        """Test that run requires input data to be set"""
        fa = Fuzzaprox()
        fa.define_fuzzy_set(0, 12, 14, 26)
        
        # Should raise an error when data_x or norm_data_y is None
        with pytest.raises((AttributeError, TypeError)):
            fa.run()
    
    def test_run_completes_successfully(self):
        """Test that run completes successfully with valid setup"""
        fa = Fuzzaprox()
        y_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        fa.set_input_data(y_values)
        fa.define_fuzzy_set(0, 2, 3, 5)
        
        # Should not raise any errors
        fa.run()
        
        assert fa.transformation is not None


class TestFuzzaproxGetMethods:
    """Test getter methods"""
    
    @pytest.fixture
    def setup_fuzzaprox(self):
        """Fixture to set up a complete Fuzzaprox instance"""
        fa = Fuzzaprox()
        # Create a simple test dataset
        y_values = list(range(1, 21))  # [1, 2, ..., 20]
        fa.set_input_data(y_values)
        fa.define_fuzzy_set(0, 5, 7, 12)
        fa.run()
        return fa
    
    def test_get_approximations(self, setup_fuzzaprox):
        """Test get_approximations returns dictionary"""
        fa = setup_fuzzaprox
        result = fa.get_approximations()
        
        assert isinstance(result, dict)
        assert "original_data_x" in result
        assert "normalised_original_data_y" in result
        assert "upper_t_fw_data_x" in result
        assert "upper_t_fw_data_y" in result
        assert "upper_t_inv_data_y" in result
        assert "bottom_t_fw_data_x" in result
        assert "bottom_t_fw_data_y" in result
        assert "bottom_t_inv_data_y" in result
    
    def test_get_fw_approx_upper(self, setup_fuzzaprox):
        """Test get_fw_approx_upper returns correct format"""
        fa = setup_fuzzaprox
        result = fa.get_fw_approx_upper()
        
        assert isinstance(result, dict)
        assert "fw_x" in result
        assert "fw_y" in result
        assert isinstance(result["fw_x"], np.ndarray)
        assert isinstance(result["fw_y"], np.ndarray)
    
    def test_get_fw_approx_bottom(self, setup_fuzzaprox):
        """Test get_fw_approx_bottom returns correct format"""
        fa = setup_fuzzaprox
        result = fa.get_fw_approx_bottom()
        
        assert isinstance(result, dict)
        assert "fw_x" in result
        assert "fw_y" in result
        assert isinstance(result["fw_x"], np.ndarray)
        assert isinstance(result["fw_y"], np.ndarray)
    
    def test_get_inv_approx_upper(self, setup_fuzzaprox):
        """Test get_inv_approx_upper returns array"""
        fa = setup_fuzzaprox
        result = fa.get_inv_approx_upper()
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_get_inv_approx_bottom(self, setup_fuzzaprox):
        """Test get_inv_approx_bottom returns array"""
        fa = setup_fuzzaprox
        result = fa.get_inv_approx_bottom()
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_get_normalised_y_vals(self, setup_fuzzaprox):
        """Test get_normalised_y_vals returns normalized array"""
        fa = setup_fuzzaprox
        result = fa.get_normalised_y_vals()
        
        assert isinstance(result, np.ndarray)
        assert np.all(result >= 0)
        assert np.all(result <= 1)
    
    def test_get_x_axes(self, setup_fuzzaprox):
        """Test get_x_axes returns x-axis array"""
        fa = setup_fuzzaprox
        result = fa.get_x_axes()
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == int
        assert len(result) > 0


class TestFuzzaproxIntegration:
    """Integration tests for complete workflow"""
    
    def test_complete_workflow(self):
        """Test complete workflow from initialization to results"""
        fa = Fuzzaprox()
        
        # Create test data
        y_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        
        # Set input data
        fa.set_input_data(y_values)
        
        # Define fuzzy set
        fa.define_fuzzy_set(0, 3, 5, 8)
        
        # Run approximation
        fa.run()
        
        # Get all results
        approx_inv_upper = fa.get_inv_approx_upper()
        approx_inv_bottom = fa.get_inv_approx_bottom()
        approx_fw_upper = fa.get_fw_approx_upper()
        approx_fw_bottom = fa.get_fw_approx_bottom()
        normalized_y = fa.get_normalised_y_vals()
        x_axes = fa.get_x_axes()
        
        # Verify all results are valid
        assert len(approx_inv_upper) == len(y_values)
        assert len(approx_inv_bottom) == len(y_values)
        assert len(normalized_y) == len(y_values)
        assert len(x_axes) == len(y_values)
        assert "fw_x" in approx_fw_upper
        assert "fw_y" in approx_fw_upper
        assert "fw_x" in approx_fw_bottom
        assert "fw_y" in approx_fw_bottom
    
    def test_workflow_with_sine_data(self):
        """Test workflow with sine wave data similar to test files"""
        fa = Fuzzaprox()
        
        # Create sine wave data
        length_data = 50
        data_x_idx = np.linspace(0, 2 * np.pi, length_data)
        sin_val_y = np.sin(data_x_idx)
        y_vals = sin_val_y.tolist()
        
        # Set input data
        fa.set_input_data(y_vals)
        
        # Define fuzzy set
        fa.define_fuzzy_set(0, 5, 7, 12)
        
        # Run approximation
        fa.run()
        
        # Verify results
        approx_inv_upper = fa.get_inv_approx_upper()
        approx_inv_bottom = fa.get_inv_approx_bottom()
        
        assert len(approx_inv_upper) == length_data
        assert len(approx_inv_bottom) == length_data
        assert isinstance(approx_inv_upper, np.ndarray)
        assert isinstance(approx_inv_bottom, np.ndarray)
