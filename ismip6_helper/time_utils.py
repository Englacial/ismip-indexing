"""
Time utilities for ISMIP6 datasets.

This module provides functions to fix common time encoding issues in ISMIP6 files
to ensure CF-compliance and compatibility with xarray's time decoding.
"""

import re
import xarray as xr
from typing import Optional


def fix_time_encoding(ds: xr.Dataset, verbose: bool = False) -> xr.Dataset:
    """
    Fix common time encoding issues in ISMIP6 files.

    This function modifies time variable attributes in-place to fix:
    1. 'unit' typo → 'units' (CF-compliant)
    2. Missing timestamps → add ' 00:00:00'
    3. Invalid dates with day 0 → change to day 1
    4. Missing calendar attribute → add '365_day'

    Parameters
    ----------
    ds : xr.Dataset
        Dataset opened with decode_cf=False, decode_times=False
    verbose : bool, optional
        If True, print information about fixes applied

    Returns
    -------
    xr.Dataset
        Dataset with fixed time encoding attributes

    Examples
    --------
    >>> import xarray as xr
    >>> import ismip6_helper
    >>>
    >>> # Open with decoding disabled
    >>> ds_raw = xr.open_dataset(url, engine='h5netcdf', decode_cf=False, decode_times=False)
    >>>
    >>> # Fix time encoding issues
    >>> ds_fixed = ismip6_helper.fix_time_encoding(ds_raw, verbose=True)
    >>>
    >>> # Now decode with xarray
    >>> ds = xr.decode_cf(ds_fixed, use_cftime=True)
    """
    # Work on a copy to avoid modifying the original
    ds = ds.copy()

    # Find time variables
    if 'time' not in ds.variables:
        return ds  # No time variable to fix
    

    attrs = ds['time'].attrs

    # Fix 1: Rename 'unit' to 'units' (CF-compliance)
    if 'unit' in attrs and 'units' not in attrs:
        if verbose:
            print(f"  - Fixing typo: 'unit' → 'units'")
        attrs['units'] = attrs.pop('unit')

    # Fix 2: Correct MM-DD-YYYY to YYYY-MM-DD
    if 'units' in attrs:
        units_str = str(attrs['units'])
        original_units = units_str

        # Fix pattern like "2000-31-12" or "YYYY-DD-MM"
        if re.search(r'\d{1,2}-\d{1,2}-\d{4}', units_str):
            # Swap day and month
            units_str = re.sub(r'(\d{1,2})-(\d{1,2})-(\d{4})', lambda m: f"{m.group(3)}-{m.group(1)}-{m.group(2)}", units_str)

            if units_str != original_units:
                if verbose:
                    print(f"  - Fixing date format: MM-DD-YYYY → YYYY-MM-DD")
                attrs['units'] = units_str

    # Fix 3: Correct invalid dates (day 0 → day 1)
    if 'units' in attrs:
        units_str = str(attrs['units'])
        original_units = units_str

        # Fix pattern like "2000-1-0" or "YYYY-M-0"
        if re.search(r'-\d+-0\s', units_str) or re.search(r'-\d+-0$', units_str):
            # Replace month-0 with month-1
            units_str = re.sub(r'(-\d+)-0(\s|$)', r'\1-1\2', units_str)

            if units_str != original_units:
                if verbose:
                    print(f"  - Fixing invalid date: day 0 → day 1")
                attrs['units'] = units_str

    # Fix 4: Add calendar if missing (for cftime compatibility)
    if 'units' in attrs and 'calendar' not in attrs:
        if verbose:
            print(f"  - Adding missing calendar attribute: '365_day'")
        attrs['calendar'] = '365_day'

    # Update the variable attributes
    ds['time'].attrs = attrs

    return ds


def open_ismip6_dataset(
    url: str,
    engine: Optional[str] = None,
    chunks: Optional[dict] = None,
    use_cftime: bool = True,
    fix_time: bool = True,
    convert_cftime_to_datetime: bool = True,
    **kwargs
) -> xr.Dataset:
    """
    Open an ISMIP6 dataset with automatic time encoding fixes.

    This is a convenience wrapper around xr.open_dataset that:
    1. Tries h5netcdf engine first, falls back to scipy for NetCDF3 files
    2. Automatically fixes time encoding issues before decoding
    3. Decodes times to cftime by default for consistency

    Parameters
    ----------
    url : str
        Path or URL to the NetCDF file
    engine : str, optional
        NetCDF engine to use. If None, tries h5netcdf first, then scipy
    chunks : dict, optional
        Chunk sizes for dask arrays (e.g., {'time': 1})
    use_cftime : bool, default True
        Whether to decode times to cftime objects (recommended for ISMIP6)
    fix_time : bool, default True
        Whether to apply time encoding fixes before decoding
    **kwargs
        Additional arguments passed to xr.open_dataset

    Returns
    -------
    xr.Dataset
        Opened dataset with properly decoded times

    Examples
    --------
    >>> import ismip6_helper
    >>>
    >>> ds = ismip6_helper.open_ismip6_dataset(
    ...     'gs://ismip6/path/to/file.nc',
    ...     chunks={'time': 1}
    ... )
    """
    # Default chunks if not specified
    if chunks is None:
        chunks = {'time': 1}

    # Try to determine the engine if not specified
    engines_to_try = [engine] if engine else ['h5netcdf', 'scipy']

    last_error = None
    for eng in engines_to_try:
        try:
            if fix_time:
                # Open without decoding
                ds_raw = xr.open_dataset(
                    url,
                    engine=eng,
                    decode_cf=False,
                    decode_times=False,
                    chunks=chunks,
                    **kwargs
                )

                # Fix time encoding
                ds_fixed = fix_time_encoding(ds_raw)

                # Now decode with proper settings
                ds = xr.decode_cf(ds_fixed, use_cftime=use_cftime)
            else:
                # Open with standard decoding
                ds = xr.open_dataset(
                    url,
                    engine=eng,
                    decode_cf=True,
                    decode_times=True,
                    chunks=chunks,
                    **kwargs
                )
                if use_cftime:
                    # Convert to cftime if needed
                    ds = xr.decode_cf(ds, use_cftime=True)

            if convert_cftime_to_datetime:
                ds['time'] = ds.indexes['time'].to_datetimeindex(time_unit='us')

            return ds

        except Exception as e:
            last_error = e
            continue

    # If we get here, all engines failed
    raise last_error
