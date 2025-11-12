"""
Data loading module with async support and progress tracking.

This module handles loading NetCDF data from Google Cloud Storage
with progress updates for the UI.
"""

import asyncio
import numpy as np
import xarray as xr
import panel as pn
from typing import Dict, List, Tuple, Callable, Optional
import traceback

from ismip6_helper import correct_grid_coordinates
from ismip6_comparison_app.config_loader import get_config


# Initialize cache configuration
config = get_config()
CACHE_ENABLED = config.get('performance.cache_loaded_datasets', True)
CACHE_MAX_ITEMS = config.get('performance.dataset_cache.max_items', 10)
CACHE_POLICY = config.get('performance.dataset_cache.policy', 'LRU')


@pn.cache(max_items=CACHE_MAX_ITEMS, policy=CACHE_POLICY)
def load_single_netcdf_cached(url: str, variable: str) -> xr.DataArray:
    """
    Load a single NetCDF file with caching.

    This function is cached to avoid re-loading the same file multiple times.
    The cache stores the full dataset with all time steps.

    Parameters
    ----------
    url : str
        URL to the NetCDF file
    variable : str
        Variable name to extract

    Returns
    -------
    xr.DataArray
        The loaded variable data with all time steps
    """
    print(f"  [CACHE MISS] Loading from source: {url}")

    # Load dataset
    ds = xr.open_dataset(
        url,
        engine='h5netcdf',
        decode_times=True,
        use_cftime=True
    )

    # Apply grid correction
    ds = correct_grid_coordinates(ds, data_var=variable)

    # Get the variable data
    if variable not in ds:
        raise ValueError(f"Variable {variable} not found in dataset")

    var_data = ds[variable]

    # Load into memory to avoid keeping file handle open
    var_data = var_data.load()

    ds.close()

    return var_data


async def load_datasets_async(
    file_list: List[Tuple[str, str, str, int]],
    variable: str,
    nan_values: List[float],
    time_step: Optional[int],
    progress_callback: Callable[[float, str], None]
) -> Tuple[Dict[str, xr.DataArray], Optional[Tuple[int, int]]]:
    """
    Load multiple NetCDF files asynchronously with progress updates.

    Parameters
    ----------
    file_list : List[Tuple[str, str, str, int]]
        List of (key, model, experiment, url, size) tuples
    variable : str
        Variable name to extract
    nan_values : List[float]
        Values to replace with NaN
    time_step : Optional[int]
        Time step to select (None for all)
    progress_callback : Callable[[float, str], None]
        Callback function to update progress (percentage, status message)

    Returns
    -------
    Tuple[Dict[str, xr.DataArray], Optional[Tuple[int, int]]]
        Dictionary of loaded datasets keyed by display name, and time range (min_year, max_year) if time dimension exists
    """
    datasets = {}
    total_files = len(file_list)
    all_time_coords = []

    if total_files == 0:
        progress_callback(100, "No files to load")
        return datasets, None

    for i, (key, model, experiment, url, size) in enumerate(file_list):
        try:
            size_mb = size / (1024 * 1024)
            print(f"\n[{i+1}/{total_files}] Loading {key} ({size_mb:.1f} MB)")
            print(f"  URL: {url}")

            progress_callback(
                (i / total_files) * 100,
                f"Loading {model} - {experiment}... ({size_mb:.1f} MB)"
            )

            # Load dataset using cached loader or direct load
            print(f"  Opening NetCDF file...")

            if CACHE_ENABLED:
                # Use cached loader (runs in thread pool automatically via pn.cache)
                print(f"  [Using cache - max {CACHE_MAX_ITEMS} items, policy: {CACHE_POLICY}]")
                var_data = await asyncio.to_thread(
                    load_single_netcdf_cached,
                    url,
                    variable
                )
                print(f"  ✓ File loaded (cached or fresh)")
            else:
                # Direct load without caching
                ds = await asyncio.to_thread(
                    xr.open_dataset,
                    url,
                    engine='h5netcdf',
                    decode_times=True,
                    use_cftime=True
                )
                print(f"  ✓ File opened successfully")

                # Apply grid correction if needed
                print(f"  Applying grid correction...")
                ds = correct_grid_coordinates(ds, data_var=variable)
                print(f"  ✓ Grid correction complete")

                # Get the variable data
                if variable not in ds:
                    print(f"  ⚠ Variable {variable} not found in dataset")
                    progress_callback(
                        ((i + 1) / total_files) * 100,
                        f"Warning: {variable} not found in {key}"
                    )
                    continue

                var_data = ds[variable]

            print(f"  ✓ Variable '{variable}' extracted, shape: {var_data.shape}")

            # Replace specified NaN values with actual NaN
            if nan_values:
                print(f"  Replacing NaN values: {nan_values}")
                for nan_val in nan_values:
                    var_data = var_data.where(var_data != nan_val, np.nan)

            # Collect time coordinates if present (for time slider)
            if 'time' in var_data.dims and 'time' in var_data.coords:
                time_coord = var_data.time
                print(f"  Time coordinate found: {len(time_coord)} steps")
                all_time_coords.append(time_coord)

            # Note: We keep all time steps now - time selection happens in plotting
            # This allows the time slider to work without reloading data
            datasets[key] = var_data
            print(f"  ✓ Successfully loaded {key}")

        except Exception as e:
            error_msg = f"Error loading {key}: {str(e)}"
            print(f"\n{error_msg}")
            print(traceback.format_exc())
            progress_callback(
                ((i + 1) / total_files) * 100,
                error_msg
            )

    print(f"\n{'='*60}")
    print(f"LOADING COMPLETE: Successfully loaded {len(datasets)}/{total_files} datasets")
    print(f"{'='*60}\n")

    # Calculate time range from all loaded datasets
    time_range = None
    if all_time_coords:
        try:
            import cftime
            # Extract years from time coordinates (handles both datetime and cftime)
            all_years = []
            for time_coord in all_time_coords:
                times = time_coord.values
                # Check if cftime objects
                if len(times) > 0 and isinstance(times[0], cftime.datetime):
                    years = [t.year for t in times]
                else:
                    # Try pandas conversion for standard datetime
                    import pandas as pd
                    times_pd = pd.to_datetime(times)
                    years = [t.year for t in times_pd]
                all_years.extend(years)

            if all_years:
                min_year = min(all_years)
                max_year = max(all_years)
                time_range = (min_year, max_year)
                print(f"Time range across all datasets: {min_year} to {max_year}")
        except Exception as e:
            print(f"Warning: Could not calculate time range: {e}")

    progress_callback(100, f"Loaded {len(datasets)} datasets successfully")
    return datasets, time_range


def calculate_global_ranges(
    datasets: Dict[str, xr.DataArray],
    percentile_low: float = 5.0,
    percentile_high: float = 95.0
) -> Tuple[Optional[float], Optional[float], str]:
    """
    Calculate global min/max for consistent color scale across all plots.

    Parameters
    ----------
    datasets : Dict[str, xr.DataArray]
        Dictionary of loaded datasets
    percentile_low : float
        Lower percentile for range calculation (default: 5.0)
    percentile_high : float
        Upper percentile for range calculation (default: 95.0)

    Returns
    -------
    Tuple[Optional[float], Optional[float], str]
        (vmin, vmax, colormap) - value range and recommended colormap
    """
    if len(datasets) == 0:
        return None, None, 'viridis'

    # Collect sample values from all datasets
    all_values = []
    for key, data in datasets.items():
        try:
            values = data.values.flatten()
            # Remove NaN and infinite values
            valid_values = values[np.isfinite(values)]
            if len(valid_values) > 0:
                # Sample to avoid memory issues with very large arrays
                if len(valid_values) > 1_000_000:
                    sample_indices = np.random.choice(
                        len(valid_values),
                        size=1_000_000,
                        replace=False
                    )
                    valid_values = valid_values[sample_indices]
                all_values.extend(valid_values)
        except Exception as e:
            print(f"Warning: Error sampling values from {key}: {e}")
            continue

    if len(all_values) == 0:
        return None, None, 'viridis'

    # Calculate percentile-based range
    vmin = np.percentile(all_values, percentile_low)
    vmax = np.percentile(all_values, percentile_high)

    # Choose colormap based on data characteristics
    if vmin < 0 and vmax > 0:
        # Diverging data (crosses zero)
        abs_max = max(abs(vmin), abs(vmax))
        vmin, vmax = -abs_max, abs_max
        cmap = 'RdBu_r'
    elif (np.abs(vmax) > np.abs(vmin)) and np.abs(vmin) < 1:
        # Positive data starting near zero
        vmin = 0
        cmap = 'Blues'
    elif (np.abs(vmin) > np.abs(vmax)) and np.abs(vmax) < 1:
        # Negative data ending near zero
        vmax = 0
        cmap = 'Blues_r'
    else:
        # General sequential data
        cmap = 'viridis'

    return float(vmin), float(vmax), cmap


def get_coordinate_ranges(datasets: Dict[str, xr.DataArray]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Get common x and y coordinate ranges across all datasets.

    Parameters
    ----------
    datasets : Dict[str, xr.DataArray]
        Dictionary of loaded datasets

    Returns
    -------
    Tuple[Tuple[float, float], Tuple[float, float]]
        ((x_min, x_max), (y_min, y_max))
    """
    if len(datasets) == 0:
        return (0, 1), (0, 1)

    # Use the first dataset's coordinates as reference
    first_data = next(iter(datasets.values()))

    if 'x' in first_data.coords and 'y' in first_data.coords:
        x_coords = first_data.x.values
        y_coords = first_data.y.values

        x_range = (float(x_coords.min()), float(x_coords.max()))
        y_range = (float(y_coords.min()), float(y_coords.max()))

        return x_range, y_range
    else:
        # Fallback to shape-based ranges
        ny, nx = first_data.shape[-2:]
        return (0, nx), (0, ny)
