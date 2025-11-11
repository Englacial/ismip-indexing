"""
Plot panel component for displaying HoloViews visualizations.

This module creates the main content area with interactive plots.
"""

import panel as pn
import holoviews as hv
from holoviews import streams
import numpy as np
from typing import Dict, Tuple, Optional
import xarray as xr
from ..config_loader import get_config


def create_empty_state() -> pn.Column:
    """
    Create an empty state placeholder.

    Returns
    -------
    pn.Column
        Empty state component
    """
    svg_icon = """
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 120px; height: 120px; opacity: 0.5; color: #999;">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>
    """

    empty_state = pn.Column(
        pn.pane.HTML(svg_icon, align='center'),
        pn.pane.Markdown(
            '## No Data Loaded\n\nSelect variables, models, and experiments from the sidebar, then click "Compare"',
            align='center',
            styles={'color': '#666', 'text-align': 'center'}
        ),
        align='center',
        sizing_mode='stretch_both',
        styles={
            'justify-content': 'center',
            'align-items': 'center'
        }
    )

    return empty_state


def create_loading_state(progress: float, status: str) -> pn.Column:
    """
    Create a loading state with spinner and status.

    Parameters
    ----------
    progress : float
        Progress percentage (0-100) - not used but kept for compatibility
    status : str
        Status message

    Returns
    -------
    pn.Column
        Loading state component
    """
    # Use LoadingSpinner instead of progress bar
    spinner = pn.indicators.LoadingSpinner(
        value=True,
        size=80,
        color='primary',
        align='center'
    )

    status_text = pn.pane.Markdown(
        f'**{status}**',
        align='center',
        styles={'text-align': 'center', 'font-size': '1.1em'}
    )

    loading_state = pn.Column(
        pn.pane.Markdown('## Loading Data', align='center', styles={'text-align': 'center'}),
        spinner,
        status_text,
        align='center',
        sizing_mode='stretch_both',
        styles={
            'justify-content': 'center',
            'align-items': 'center'
        }
    )

    return loading_state


def create_linked_plots(
    datasets: Dict[str, xr.DataArray],
    variable: str,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    vmin: Optional[float],
    vmax: Optional[float],
    colormap: str,
    selected_year: Optional[int] = None
) -> hv.Layout:
    """
    Create HoloViews plots with linked axes.

    Parameters
    ----------
    datasets : Dict[str, xr.DataArray]
        Dictionary of loaded datasets
    variable : str
        Variable name being plotted
    x_range : Tuple[float, float]
        X coordinate range (min, max)
    y_range : Tuple[float, float]
        Y coordinate range (min, max)
    vmin : Optional[float]
        Minimum value for color scale
    vmax : Optional[float]
        Maximum value for color scale
    colormap : str
        Colormap name
    selected_year : Optional[int]
        Year to select from time dimension (finds nearest time step)

    Returns
    -------
    hv.Layout
        HoloViews layout with linked plots
    """
    if len(datasets) == 0:
        return hv.Layout([])

    # Load config
    config = get_config()

    # Get units from first dataset for colorbar label
    units = None
    first_data = next(iter(datasets.values()))
    if hasattr(first_data, 'attrs') and 'units' in first_data.attrs:
        units = first_data.attrs['units']

    # Create colorbar label with units
    if units:
        clabel = f"{variable} ({units})"
    else:
        clabel = variable

    plots = []

    for key, data in datasets.items():
        try:
            # Handle time selection if data has time dimension
            if data.ndim == 3 and 'time' in data.dims:
                if selected_year is not None:
                    # Find time step closest to selected year
                    import cftime
                    time_coord = data.time
                    times = time_coord.values

                    # Extract years (handle both cftime and standard datetime)
                    if len(times) > 0 and isinstance(times[0], cftime.datetime):
                        years = np.array([t.year for t in times])
                    else:
                        import pandas as pd
                        times_pd = pd.to_datetime(times)
                        years = np.array([t.year for t in times_pd])

                    # Find closest year
                    closest_idx = np.argmin(np.abs(years - selected_year))
                    print(f"  Selecting time step {closest_idx} (year {years[closest_idx]}) for {key}")
                    plot_data = data.isel(time=closest_idx).values
                else:
                    # Default to first time step
                    plot_data = data.isel(time=0).values
            elif data.ndim == 2:
                # 2D data, use as-is
                plot_data = data.values
            else:
                print(f"Warning: Unexpected dimensions for {key}: {data.dims}")
                continue

            # Flip vertically to match coordinate system
            plot_data = np.flipud(plot_data)

            # Create HoloViews Image with config settings
            # Debug: Print aspect ratio settings
            print(f"Creating plot with: width={config.plot_width}, height={config.plot_height}, "
                  f"aspect={config.aspect_ratio}, data_aspect={config.data_aspect}")

            img = hv.Image(
                plot_data,
                bounds=(x_range[0], y_range[0], x_range[1], y_range[1]),
                #kdims=['x', 'y'],
                #vdims=[variable]
            ).opts(
                cmap=colormap,
                clim=(vmin, vmax) if vmin is not None and vmax is not None else None,
                title=key,
                colorbar=True,
                colorbar_opts={'background_fill_alpha': 0, 'title': clabel},
                tools=config.plot_tools,
                xlabel='X (m)',
                ylabel='Y (m)',
                aspect='equal',
                data_aspect=1,
                fontsize={'title': 11, 'labels': 10, 'xticks': 8, 'yticks': 8},
                toolbar=config.toolbar_position
            )

            plots.append(img)

        except Exception as e:
            print(f"Error creating plot for {key}: {e}")
            continue

    if len(plots) == 0:
        return hv.Layout([])

    # Create layout with linked axes
    if len(plots) == 1:
        layout = plots[0]
    else:
        layout = hv.Layout(plots).opts(
            shared_axes=config.shared_axes,
            merge_tools=False
        ).cols(config.layout_columns)

    return layout


def create_plot_panel(state) -> pn.Column:
    """
    Create the main plot panel component.

    Parameters
    ----------
    state : DataSelectionState
        Application state object

    Returns
    -------
    pn.Column
        Plot panel component
    """
    # Create a Column to hold dynamic content
    plot_container = pn.Column(
        create_empty_state(),
        #sizing_mode='stretch_both',
        min_height=400
    )

    # Create a Stream to trigger updates without recreating plots
    time_stream = streams.Params(parameters=[state.param.time_slider_year])

    # Keep reference to current DynamicMap to preserve zoom
    current_dmap = [None]  # Use list to allow mutation in nested function
    current_hv_pane = [None]

    def create_plot_function(datasets, variable, x_range, y_range, vmin, vmax, colormap):
        """Create a function that generates plots based on time stream."""
        def plot_for_time(time_slider_year):
            selected_year = int(time_slider_year) if state.time_slider_visible else None
            return create_linked_plots(
                datasets=datasets,
                variable=variable,
                x_range=x_range,
                y_range=y_range,
                vmin=vmin,
                vmax=vmax,
                colormap=colormap,
                selected_year=selected_year
            )
        return plot_for_time

    def update_plot(*events):
        """Update the plot based on state changes."""
        # Check what triggered the update
        is_time_only_update = False
        is_colorrange_only_update = False
        if events:
            event = events[0]
            if hasattr(event, 'name'):
                if event.name == 'time_slider_year':
                    is_time_only_update = True
                elif event.name in ['vmin', 'vmax', 'colormap']:
                    is_colorrange_only_update = True

        if state.is_loading:
            # Show loading state
            plot_container.clear()
            current_dmap[0] = None
            current_hv_pane[0] = None
            plot_container.append(create_loading_state(
                state.load_progress,
                state.load_status
            ))
        elif len(state.datasets) == 0:
            # Show empty state
            plot_container.clear()
            current_dmap[0] = None
            current_hv_pane[0] = None
            plot_container.append(create_empty_state())
        else:
            # Show plots
            try:
                from .data_loader import get_coordinate_ranges

                x_range, y_range = get_coordinate_ranges(state.datasets)

                # If this is just a time slider update, the DynamicMap will handle it automatically
                if is_time_only_update and current_dmap[0] is not None:
                    # Stream will automatically trigger update, preserving zoom
                    return

                # If only color range/colormap changed, recreate DynamicMap but don't reload data
                # This preserves zoom and is much faster than reloading
                if is_colorrange_only_update and current_dmap[0] is not None:
                    plot_container.clear()

                    plot_func = create_plot_function(
                        state.datasets,
                        state.selected_variable,
                        x_range,
                        y_range,
                        state.vmin,
                        state.vmax,
                        state.colormap
                    )

                    dmap = hv.DynamicMap(plot_func, streams=[time_stream])
                    current_dmap[0] = dmap

                    hv_pane = pn.pane.HoloViews(
                        dmap,
                        #sizing_mode='stretch_both'
                    )
                    current_hv_pane[0] = hv_pane
                    plot_container.append(hv_pane)
                    return

                # Create new DynamicMap (new data loaded or first time)
                plot_container.clear()

                plot_func = create_plot_function(
                    state.datasets,
                    state.selected_variable,
                    x_range,
                    y_range,
                    state.vmin,
                    state.vmax,
                    state.colormap
                )

                dmap = hv.DynamicMap(plot_func, streams=[time_stream])
                current_dmap[0] = dmap

                hv_pane = pn.pane.HoloViews(
                    dmap,
                    #sizing_mode='stretch_both'
                )
                current_hv_pane[0] = hv_pane
                plot_container.append(hv_pane)

            except Exception as e:
                print(f"Error updating plot: {e}")
                import traceback
                traceback.print_exc()
                plot_container.clear()
                current_dmap[0] = None
                current_hv_pane[0] = None
                plot_container.append(pn.pane.Markdown(
                    f'## Error Creating Plots\n\n```\n{str(e)}\n```',
                    styles={'color': 'red'}
                ))

    # Watch for state changes (including time slider and color ranges)
    state.param.watch(update_plot, ['datasets', 'is_loading', 'load_progress', 'load_status', 'time_slider_year', 'vmin', 'vmax', 'colormap'])

    # Create main panel
    panel = pn.Column(
        plot_container,
        sizing_mode='stretch_both'
    )

    return panel
