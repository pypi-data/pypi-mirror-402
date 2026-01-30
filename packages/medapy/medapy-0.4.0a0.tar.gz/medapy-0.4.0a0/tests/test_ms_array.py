"""
Tests for MeasurementArray and MeasurementDtype implementations.
"""

import numpy as np
import pandas as pd
import pytest
import uuid
from medapy.ms_array import MeasurementArray, MeasurementDtype
from medapy import ureg


@pytest.fixture
def sample_data():
    """Provide sample numeric data for array creation."""
    return [1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.fixture
def sample_data_with_nan():
    """Provide sample data containing NaN values."""
    return [1.0, np.nan, 3.0, np.nan, 5.0]


@pytest.fixture
def volt_array(sample_data):
    """Create a MeasurementArray with volt units."""
    return MeasurementArray(sample_data, dtype="ms[volt]")


@pytest.fixture
def ampere_array(sample_data):
    """Create a MeasurementArray with ampere units."""
    return MeasurementArray(sample_data, dtype="ms[ampere]")


def test_measurement_dtype_creation():
    """Test MeasurementDtype creation and caching."""
    # Create dtype with unit string
    dtype1 = MeasurementDtype("volt")
    assert dtype1.unit == ureg.volt
    assert str(dtype1.subdtype) == "Float64"

    # Create dtype with unit and subdtype
    dtype2 = MeasurementDtype("ampere", "float32")
    assert dtype2.unit == ureg.ampere
    assert str(dtype2.subdtype) == "float32"

    # Test caching - same parameters should return same instance
    dtype3 = MeasurementDtype("volt")
    assert dtype1 is dtype3

    # Test dimensionless
    dtype4 = MeasurementDtype(None)
    assert dtype4.unit == ureg.dimensionless


def test_measurement_dtype_string_parsing():
    """Test parsing dtype from string."""
    # Parse simple unit with "ms"
    dtype1 = MeasurementDtype.construct_from_string("ms[volt]")
    assert dtype1.unit == ureg.volt

    # Parse with "pint" prefix
    dtype2 = MeasurementDtype.construct_from_string("pint[volt]")
    assert dtype2.unit == ureg.volt

    # Parse with "Pint" prefix (capitalized)
    dtype3 = MeasurementDtype.construct_from_string("Pint[volt]")
    assert dtype3.unit == ureg.volt

    # All three should be equal
    assert dtype1 == dtype2 == dtype3

    # Parse with subdtype
    dtype4 = MeasurementDtype.construct_from_string("ms[ampere][float32]")
    assert dtype4.unit == ureg.ampere
    assert str(dtype4.subdtype) == "float32"

    # Parse pint format with subdtype
    dtype5 = MeasurementDtype.construct_from_string("pint[ampere][float32]")
    assert dtype5.unit == ureg.ampere
    assert str(dtype5.subdtype) == "float32"

    # Parse Pint format with subdtype
    dtype6 = MeasurementDtype.construct_from_string("Pint[ohm][Int32]")
    assert dtype6.unit == ureg.ohm
    assert str(dtype6.subdtype) == "Int32"

    # Test equality with string
    dtype7 = MeasurementDtype("volt")
    assert dtype1 == dtype7
    assert dtype1 == "ms[volt][Float64]"


def test_measurement_array_creation(sample_data):
    """Test MeasurementArray creation."""
    # Create array with data and unit using string format
    arr = MeasurementArray(sample_data, dtype="ms[volt]")

    assert len(arr) == 5
    assert arr.unit == ureg.volt
    assert isinstance(arr.id, uuid.UUID)

    # Create with explicit ID
    test_id = uuid.uuid4()
    arr2 = MeasurementArray(sample_data, dtype="ms[ampere]", id=test_id)
    assert arr2.id == test_id

    # Create with numpy array and MeasurementDtype
    arr3 = MeasurementArray(np.array(sample_data), dtype=MeasurementDtype("ohm"))
    assert len(arr3) == 5
    assert arr3.unit == ureg.ohm

    # Create with pint.Unit directly
    arr4 = MeasurementArray(sample_data, dtype=ureg.tesla)
    assert arr4.unit == ureg.tesla


def test_measurement_array_dtype_validation():
    """Test that only proper dtype formats are accepted."""
    data = [1.0, 2.0, 3.0]

    # Valid: "ms[]" format
    arr1 = MeasurementArray(data, dtype="ms[volt]")
    assert arr1.unit == ureg.volt

    arr2 = MeasurementArray(data, dtype="ms[volt][Float64]")
    assert arr2.unit == ureg.volt

    # Valid: "pint[]" format (compatibility)
    arr3 = MeasurementArray(data, dtype="pint[ampere]")
    assert arr3.unit == ureg.ampere

    arr4 = MeasurementArray(data, dtype="pint[ohm][float32]")
    assert arr4.unit == ureg.ohm
    assert str(arr4.dtype.subdtype) == "float32"

    # Valid: "Pint[]" format (compatibility)
    arr5 = MeasurementArray(data, dtype="Pint[tesla]")
    assert arr5.unit == ureg.tesla

    # Valid: MeasurementDtype instance
    arr6 = MeasurementArray(data, dtype=MeasurementDtype("ampere"))
    assert arr6.unit == ureg.ampere

    # Valid: pint.Unit instance
    arr7 = MeasurementArray(data, dtype=ureg.ohm)
    assert arr7.unit == ureg.ohm

    # Invalid: plain string without proper format should fail
    with pytest.raises(TypeError):
        MeasurementArray(data, dtype="volt")

    # Invalid: random string should fail
    with pytest.raises(TypeError):
        MeasurementArray(data, dtype="random_string")


def test_measurement_array_indexing(volt_array):
    """Test indexing and slicing."""
    # Single element access
    val = volt_array[0]
    assert val == 1.0

    # Slicing returns new array with same metadata
    arr_slice = volt_array[1:4]
    assert len(arr_slice) == 3
    assert arr_slice.unit == volt_array.unit
    assert arr_slice.id == volt_array.id

    # Boolean indexing
    mask = np.array([True, False, True, False, True])
    arr_masked = volt_array[mask]
    assert len(arr_masked) == 3
    assert arr_masked.unit == volt_array.unit


def test_measurement_array_setitem(sample_data):
    """Test setting values."""
    arr = MeasurementArray(sample_data, dtype="ms[volt]")

    # Set single value
    arr[0] = 10.0
    assert arr[0] == 10.0

    # Set slice
    arr[1:3] = [20.0, 30.0]
    assert arr[1] == 20.0
    assert arr[2] == 30.0


def test_measurement_array_operations(volt_array, sample_data_with_nan):
    """Test array operations."""
    # Test copy
    arr_copy = volt_array.copy()
    assert len(arr_copy) == len(volt_array)
    assert arr_copy.unit == volt_array.unit
    assert arr_copy.id == volt_array.id
    arr_copy[0] = 100.0
    assert volt_array[0] != 100.0  # Original unchanged

    # Test take
    indices = [0, 2, 4]
    arr_taken = volt_array.take(indices)
    assert len(arr_taken) == 3
    assert arr_taken[0] == volt_array[0]
    assert arr_taken[1] == volt_array[2]

    # Test isna
    arr_nan = MeasurementArray(sample_data_with_nan, dtype="ms[volt]")
    na_mask = arr_nan.isna()
    assert np.sum(na_mask) == 2


def test_measurement_array_reductions(volt_array, sample_data_with_nan):
    """Test reduction operations."""
    # Test sum
    total = volt_array._reduce("sum")
    assert total == 15.0

    # Test mean
    mean = volt_array._reduce("mean")
    assert mean == 3.0

    # Test min/max
    minimum = volt_array._reduce("min")
    maximum = volt_array._reduce("max")
    assert minimum == 1.0
    assert maximum == 5.0

    # Test with NaN
    arr_nan = MeasurementArray(sample_data_with_nan, dtype="ms[volt]")
    mean_skipna = arr_nan._reduce("mean", skipna=True)
    assert mean_skipna == 3.0


def test_measurement_array_concat():
    """Test concatenation."""
    arr1 = MeasurementArray([1.0, 2.0, 3.0], dtype="ms[volt]")
    arr2 = MeasurementArray([4.0, 5.0], dtype="ms[volt]")
    arr3 = MeasurementArray([6.0, 7.0, 8.0], dtype="ms[volt]")

    # Concatenate
    arr_concat = MeasurementArray._concat_same_type([arr1, arr2, arr3])

    assert len(arr_concat) == 8
    assert arr_concat.unit == arr1.unit
    assert arr_concat.id == arr1.id  # Takes first array's ID
    assert arr_concat[0] == 1.0
    assert arr_concat[7] == 8.0


def test_pandas_integration():
    """Test integration with pandas."""
    # Create DataFrame with MeasurementArray
    voltage_data = MeasurementArray([1.0, 2.0, 3.0, 4.0], dtype="ms[volt]")
    current_data = MeasurementArray([0.1, 0.2, 0.3, 0.4], dtype="ms[ampere]")

    df = pd.DataFrame({"voltage": voltage_data, "current": current_data})

    # Test that dtypes are preserved
    assert isinstance(df["voltage"].dtype, MeasurementDtype)
    assert isinstance(df["current"].dtype, MeasurementDtype)
    assert df["voltage"].dtype.unit == ureg.volt
    assert df["current"].dtype.unit == ureg.ampere

    # Test slicing
    df_slice = df.iloc[1:3]
    assert len(df_slice) == 2
    assert isinstance(df_slice["voltage"].dtype, MeasurementDtype)

    # Test that we can access underlying arrays
    voltage_arr = df["voltage"].array
    assert isinstance(voltage_arr, MeasurementArray)
    assert voltage_arr.unit == ureg.volt


def test_subdtype_handling():
    """Test different subdtypes."""
    # Float64 (default)
    arr_f64 = MeasurementArray(
        [1.0, 2.0, 3.0], dtype=MeasurementDtype("volt", "Float64")
    )
    assert str(arr_f64.dtype.subdtype) == "Float64"

    # float32
    arr_f32 = MeasurementArray(
        [1.0, 2.0, 3.0], dtype=MeasurementDtype("volt", "float32")
    )
    assert str(arr_f32.dtype.subdtype) == "float32"

    # Int32 (nullable integer)
    arr_int = MeasurementArray([1, 2, 3], dtype=MeasurementDtype("volt", "Int32"))
    assert str(arr_int.dtype.subdtype) == "Int32"

    # complex128
    arr_complex = MeasurementArray(
        [1 + 2j, 3 + 4j], dtype=MeasurementDtype("volt", "complex128")
    )
    assert str(arr_complex.dtype.subdtype) == "complex128"
