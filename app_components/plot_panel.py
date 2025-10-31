"""
Plot panel component for displaying HoloViews visualizations.

This module creates the main content area with interactive plots.
"""

import panel as pn
import holoviews as hv
import numpy as np
from typing import Dict, Tuple, Optional
import xarray as xr
from config_loader import get_config


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
    colormap: str
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

    Returns
    -------
    hv.Layout
        HoloViews layout with linked plots
    """
    if len(datasets) == 0:
        return hv.Layout([])

    # Load config
    config = get_config()

    plots = []

    for key, data in datasets.items():
        try:
            # Get data array (handle 2D and 3D cases)
            if data.ndim == 2:
                plot_data = data.values
            elif data.ndim == 3:
                # Take first time step if 3D
                plot_data = data.isel(time=0).values
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

    def update_plot(*events):
        """Update the plot based on state changes."""
        if state.is_loading:
            # Show loading state
            plot_container.clear()
            plot_container.append(create_loading_state(
                state.load_progress,
                state.load_status
            ))
        elif len(state.datasets) == 0:
            # Show empty state
            plot_container.clear()
            plot_container.append(create_empty_state())
        else:
            # Show plots
            try:
                from .data_loader import get_coordinate_ranges

                x_range, y_range = get_coordinate_ranges(state.datasets)

                layout = create_linked_plots(
                    datasets=state.datasets,
                    variable=state.selected_variable,
                    x_range=x_range,
                    y_range=y_range,
                    vmin=state.vmin,
                    vmax=state.vmax,
                    colormap=state.colormap
                )

                plot_container.clear()
                plot_container.append(pn.pane.HoloViews(
                    layout,
                    #sizing_mode='stretch_both'
                ))

            except Exception as e:
                print(f"Error updating plot: {e}")
                import traceback
                traceback.print_exc()
                plot_container.clear()
                plot_container.append(pn.pane.Markdown(
                    f'## Error Creating Plots\n\n```\n{str(e)}\n```',
                    styles={'color': 'red'}
                ))

    # Watch for state changes
    state.param.watch(update_plot, ['datasets', 'is_loading', 'load_progress', 'load_status'])

    # Create main panel
    panel = pn.Column(
        plot_container,
        sizing_mode='stretch_both'
    )

    return panel
