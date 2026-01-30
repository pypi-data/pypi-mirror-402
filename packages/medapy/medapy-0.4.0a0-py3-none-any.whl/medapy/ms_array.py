"""
Extension Array implementation for measurement data with metadata.

This module provides pandas ExtensionDtype and ExtensionArray implementations
for storing measurement data with units and unique identifiers.
"""

import re
import uuid
from typing import Any, Optional, Sequence, Union

import numpy as np
import pandas as pd
from pandas.api.extensions import ExtensionArray, ExtensionDtype
from pandas.core.dtypes.base import register_extension_dtype

from medapy import ureg


@register_extension_dtype
class MeasurementDtype(ExtensionDtype):
    """
    ExtensionDtype for measurement data with units.

    This dtype represents measurements with Pint units. Different units
    or subdtypes create different dtype instances.

    Parameters
    ----------
    unit : str or pint.Unit, optional
        The unit for this dtype. If None, dimensionless.
    subdtype : str or numpy.dtype, optional
        The underlying numeric dtype (e.g., 'float64', 'Int32', 'complex128').
        If None, defaults to 'Float64' (pandas nullable float).

    Attributes
    ----------
    unit : pint.Unit
        The Pint unit for this dtype.
    subdtype : numpy.dtype or pandas dtype
        The underlying numeric dtype.
    type : type
        The scalar type for the array (float).
    kind : str
        A character code ('O' for object-like).
    """

    type = float  # The scalar type
    kind = "O"  # Character code for object-like
    _is_numeric = True  # Measurement data is numeric
    _metadata = ("unit", "subdtype")  # Tuple of strings for hashability
    _cache = {}  # Cache for dtype instances
    _match = re.compile(r"^(?:ms|pint|Pint)\[(?P<unit>.*?)\](?:\[(?P<subdtype>.+)\])?$")  # Pattern for parsing dtype strings

    def __new__(cls, unit=None, subdtype=None):
        """
        Create a new MeasurementDtype instance.

        Uses caching to ensure dtype instances with the same unit and subdtype are identical.

        Parameters
        ----------
        unit : str or pint.Unit or MeasurementDtype, optional
            The unit for this dtype
        subdtype : str or numpy.dtype, optional
            The underlying numeric dtype. Defaults to 'Float64'.

        Returns
        -------
        MeasurementDtype
            Cached dtype instance
        """
        # Handle MeasurementDtype input
        if isinstance(unit, MeasurementDtype):
            return unit

        # Handle None - dimensionless
        if unit is None:
            unit = ureg.dimensionless
        # Convert string to Pint unit
        elif isinstance(unit, str):
            unit = ureg.Unit(unit)

        # Handle subdtype default
        if subdtype is None:
            subdtype = "Float64"

        # Normalize subdtype to string for caching
        subdtype_str = str(subdtype)

        # Check cache
        cache_key = (str(unit), subdtype_str)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Create new instance
        instance = object.__new__(cls)
        instance.unit = unit
        instance.subdtype = subdtype
        cls._cache[cache_key] = instance
        return instance

    @property
    def name(self):
        """Return the string name of this dtype."""
        return f"ms[{self.unit}][{self.subdtype}]"

    @property
    def na_value(self):
        """Return the NA value for this dtype."""
        return np.nan

    @classmethod
    def construct_array_type(cls):
        """
        Return the array type associated with this dtype.

        Returns
        -------
        type
            MeasurementArray class
        """
        return MeasurementArray

    def __repr__(self):
        return self.name

    def __hash__(self):
        """Hash based on unit string."""
        return hash(str(self))

    def __eq__(self, other):
        """
        Check equality with another dtype.

        Two MeasurementDtype instances are equal if they have the same unit and subdtype.

        Parameters
        ----------
        other : object
            Object to compare with

        Returns
        -------
        bool
            True if equal
        """
        if isinstance(other, str):
            try:
                other = MeasurementDtype.construct_from_string(other)
            except Exception:
                return False
        if not isinstance(other, MeasurementDtype):
            return False
        return self.unit == other.unit and str(self.subdtype) == str(other.subdtype)

    @classmethod
    def construct_from_string(cls, string):
        """
        Construct a MeasurementDtype from a string.

        Parameters
        ----------
        string : str
            String representation like "ms[volt]", "pint[volt]", "Pint[volt]",
            or with subdtype: "ms[volt][Float64]", "pint[volt][Float64]"

        Returns
        -------
        MeasurementDtype
            Constructed dtype

        Raises
        ------
        TypeError
            If string cannot be parsed
        """
        if not isinstance(string, str):
            raise TypeError(
                f"'construct_from_string' expects a string, got {type(string)}"
            )

        match = cls._match.match(string)
        if match:
            unit_str = match.group("unit")
            subdtype_str = match.group("subdtype")  # May be None if not provided

            # Handle empty unit string as dimensionless (use '1' for brevity)
            if unit_str == "":
                unit_str = "1"

            try:
                return cls(unit_str, subdtype_str)
            except Exception:
                pass

        raise TypeError(f"Cannot construct a 'MeasurementDtype' from '{string}'")


class MeasurementArray(ExtensionArray):
    """
    ExtensionArray for measurement data with units and unique identifier.

    This array wraps a pandas/numpy array and associates it with:
    - A Pint unit (stored in dtype)
    - A subdtype (underlying numeric type)
    - A unique identifier (UUID) for linking to DataFrame-level metadata

    Parameters
    ----------
    data : array-like
        The measurement values
    dtype : MeasurementDtype, str, or pint.Unit, optional
        The dtype or unit of measurement
    id : str or UUID, optional
        Unique identifier for this measurement. Auto-generated if not provided.

    Attributes
    ----------
    _data : pandas.array or np.ndarray
        The underlying array containing the data (with subdtype)
    _dtype : MeasurementDtype
        The dtype containing unit and subdtype information
    _id : uuid.UUID
        Unique identifier for linking to DataFrame-level metadata
    """

    def __init__(
        self,
        data: Union[np.ndarray, Sequence, pd.core.arrays.ExtensionArray],
        dtype: Union[MeasurementDtype, str, Any] = None,
        id: Optional[Union[str, uuid.UUID]] = None
    ):
        """
        Initialize a MeasurementArray.

        Parameters
        ----------
        data : array-like
            The measurement values
        dtype : MeasurementDtype, str, or pint.Unit, optional
            The dtype or unit of measurement
        id : str or UUID, optional
            Unique identifier. Auto-generated if not provided.
        """
        # Handle dtype parameter
        if dtype is None:
            # Infer subdtype from data
            if hasattr(data, 'dtype'):
                inferred_subdtype = data.dtype
            else:
                inferred_subdtype = None
            dtype = MeasurementDtype(subdtype=inferred_subdtype)
        elif isinstance(dtype, str):
            # Must be in format "ms[unit]" or "ms[unit][subdtype]"
            dtype = MeasurementDtype.construct_from_string(dtype)
        elif not isinstance(dtype, MeasurementDtype):
            # Assume it's a pint.Unit or similar
            dtype = MeasurementDtype(dtype)

        self._dtype = dtype

        # Convert data to appropriate array type based on subdtype
        if not hasattr(data, 'dtype') or data.dtype != self._dtype.subdtype:
            data = pd.array(data, dtype=self._dtype.subdtype)

        self._data = data

        # Handle ID
        if id is None:
            self._id = uuid.uuid4()
        elif isinstance(id, str):
            self._id = uuid.UUID(id)
        else:
            self._id = id

    @property
    def unit(self):
        """Return the unit of this measurement."""
        return self._dtype.unit

    @property
    def id(self):
        """Return the unique identifier of this measurement."""
        return self._id

    @property
    def dtype(self):
        """Return the dtype object for this array."""
        return self._dtype

    def __len__(self):
        """Return the length of the array."""
        return len(self._data)

    def __getitem__(self, item):
        """
        Select a subset of self.

        Parameters
        ----------
        item : int, slice, or ndarray
            Indexer for selecting elements

        Returns
        -------
        MeasurementArray or scalar
            If item is an integer, returns a scalar.
            Otherwise, returns a new MeasurementArray with the same unit and ID.
        """
        if isinstance(item, int):
            return self._data[item]
        else:
            return type(self)(self._data[item], self._dtype, self._id)

    def __setitem__(self, key, value):
        """
        Set one or more values inplace.

        Parameters
        ----------
        key : int, slice, or ndarray
            Indexer for selecting elements
        value : scalar or array-like
            Values to set
        """
        self._data[key] = value

    def __array__(self, dtype=None):
        """
        Return underlying numpy array when np.asarray() is called.

        This enables fast numpy operations by extracting the raw array.
        Metadata (unit, id) is lost in the conversion.

        Parameters
        ----------
        dtype : numpy dtype, optional
            Target dtype for the array

        Returns
        -------
        np.ndarray
            The underlying numpy array
        """
        if dtype is None:
            return np.asarray(self._data)
        return np.asarray(self._data, dtype=dtype)

    @property
    def nbytes(self):
        """Return the number of bytes needed to store this object in memory."""
        return self._data.nbytes

    def isna(self):
        """
        Return a boolean array indicating if each value is missing.

        Returns
        -------
        np.ndarray
            Boolean array with True where values are NaN
        """
        if hasattr(self._data, 'isna'):
            return self._data.isna()
        return np.isnan(self._data)

    def take(self, indices, allow_fill=False, fill_value=None):
        """
        Take elements from an array.

        Parameters
        ----------
        indices : sequence of int
            Indices to take
        allow_fill : bool, default False
            If True, allow filling indices beyond the array length with fill_value
        fill_value : scalar, optional
            Fill value to use for out-of-bounds indices when allow_fill=True

        Returns
        -------
        MeasurementArray
            New array with selected elements
        """
        from pandas.core.algorithms import take

        if allow_fill and fill_value is None:
            fill_value = self.dtype.na_value

        result = take(self._data, indices, fill_value=fill_value, allow_fill=allow_fill)
        return type(self)(result, self._dtype, self._id)

    def copy(self):
        """
        Return a copy of the array.

        Returns
        -------
        MeasurementArray
            Copy with same unit and ID
        """
        if hasattr(self._data, 'copy'):
            data_copy = self._data.copy()
        else:
            data_copy = self._data[:]
        return type(self)(data_copy, self._dtype, self._id)

    @classmethod
    def _concat_same_type(cls, to_concat):
        """
        Concatenate multiple arrays.

        Parameters
        ----------
        to_concat : sequence of MeasurementArray
            Arrays to concatenate

        Returns
        -------
        MeasurementArray
            Concatenated array with unit and ID from first array
        """
        # Concatenate underlying data arrays
        data_list = [arr._data for arr in to_concat]

        # Use pandas concat if data is ExtensionArray, otherwise numpy
        if hasattr(data_list[0], '__class__') and hasattr(data_list[0].__class__, '_concat_same_type'):
            data = data_list[0].__class__._concat_same_type(data_list)
        else:
            data = np.concatenate(data_list)

        # Use dtype and ID from first array
        return cls(data, to_concat[0]._dtype, to_concat[0]._id)

    @classmethod
    def _from_sequence(cls, scalars, dtype=None, copy=False):
        """
        Construct a new MeasurementArray from a sequence of scalars.

        Parameters
        ----------
        scalars : sequence
            Scalar values or MeasurementArray instances
        dtype : MeasurementDtype, optional
            The dtype for the array
        copy : bool, default False
            Whether to copy the data

        Returns
        -------
        MeasurementArray
            New array constructed from scalars
        """
        # Handle MeasurementArray input
        if isinstance(scalars, cls):
            data = scalars._data
            if dtype is None:
                dtype = scalars._dtype
            id = scalars._id
        else:
            # Infer dtype if not provided
            if dtype is None:
                dtype = MeasurementDtype()

            data = pd.array(scalars, dtype=dtype.subdtype)
            id = None

        if copy and hasattr(data, 'copy'):
            data = data.copy()

        return cls(data, dtype, id)

    @classmethod
    def _from_factorized(cls, values, original):
        """
        Reconstruct an ExtensionArray after factorization.

        Parameters
        ----------
        values : ndarray
            Integer ndarray of codes from factorize
        original : MeasurementArray
            The original array that was factorized

        Returns
        -------
        MeasurementArray
            Reconstructed array
        """
        return cls(values, original._dtype, original._id)

    def _reduce(self, name, skipna=True, **kwargs):
        """
        Return a scalar result of performing the reduction operation.

        Parameters
        ----------
        name : str
            Name of the reduction function (e.g., 'sum', 'mean', 'min', 'max')
        skipna : bool, default True
            If True, skip NaN values
        **kwargs
            Additional keyword arguments passed to the reduction function

        Returns
        -------
        scalar
            Result of the reduction
        """
        # Delegate to underlying array if it has _reduce
        if hasattr(self._data, '_reduce'):
            return self._data._reduce(name, skipna=skipna, **kwargs)

        # Otherwise use numpy
        data = np.asarray(self._data)
        if skipna:
            # Create a masked version that ignores NaN
            data = data[~np.isnan(data)]

        if name == "sum":
            return np.sum(data, **kwargs)
        elif name == "mean":
            return np.mean(data, **kwargs)
        elif name == "min":
            return np.min(data, **kwargs)
        elif name == "max":
            return np.max(data, **kwargs)
        elif name == "std":
            return np.std(data, **kwargs)
        elif name == "var":
            return np.var(data, **kwargs)
        else:
            raise NotImplementedError(f"Reduction '{name}' not implemented")

    def __repr__(self):
        """String representation of the array."""
        return f"MeasurementArray({self._data}, unit={self._dtype.unit}, id={self._id})"
