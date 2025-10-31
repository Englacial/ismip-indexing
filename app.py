#!/usr/bin/env python3
"""
ISMIP6 Interactive Comparison Tool - Main Application

A Panel web application for comparing ISMIP6 ice sheet model outputs.
"""

import panel as pn
import holoviews as hv
import asyncio
from functools import partial

from ismip6_index import get_file_index
from app_components.sidebar import DataSelectionState, create_sidebar
from app_components.plot_panel import create_plot_panel
from app_components.data_loader import (
    load_datasets_async,
    calculate_global_ranges,
    get_coordinate_ranges
)

# Initialize Panel and HoloViews
pn.extension(sizing_mode='stretch_width', notifications=True)
hv.extension('bokeh')


def create_app():
    """
    Create and configure the main application.

    Returns
    -------
    pn.template.FastListTemplate
        The configured Panel application template
    """

    # Initialize application state
    state = DataSelectionState()

    # Load file index (cached)
    @pn.cache
    def get_cached_index():
        print("Loading ISMIP6 file index...")
        df = get_file_index()
        # Add 'model' column (institution/model_name)
        df['model'] = df['institution'] + '/' + df['model_name']
        print(f"Loaded {len(df):,} files from index")
        return df

    try:
        state.file_index = get_cached_index()
    except Exception as e:
        print(f"Error loading file index: {e}")
        # Note: notifications may not be available during app initialization
        # pn.state.notifications.error(
        #     f"Failed to load file index: {str(e)}",
        #     duration=10000
        # )

    # Create UI components
    sidebar, compare_button = create_sidebar(state)
    plot_panel = create_plot_panel(state)

    # Compare button callback
    async def on_compare_click(event):
        """Handle compare button click - load data and create plots."""
        try:
            # Get matched files
            matched_files = state.get_matched_files()

            if matched_files.empty:
                pn.state.notifications.warning(
                    "No files matched the selection criteria",
                    duration=3000
                )
                return

            # Prepare file list
            file_list = []
            for _, row in matched_files.iterrows():
                key = f"{row['model']} - {row['experiment']}"
                file_list.append((
                    key,
                    row['model'],
                    row['experiment'],
                    row['url'],
                    row['size_bytes']
                ))

            # Clear previous data
            state.datasets = {}

            # Set loading state
            state.is_loading = True
            state.load_progress = 0
            state.load_status = 'Starting...'

            # Disable button during loading
            compare_button.disabled = True

            # Progress callback
            def update_progress(progress: float, status: str):
                state.load_progress = progress
                state.load_status = status

            # Load datasets asynchronously
            datasets = await load_datasets_async(
                file_list=file_list,
                variable=state.selected_variable,
                nan_values=state.get_nan_values_list(),
                time_step=state.get_time_step_value(),
                progress_callback=update_progress
            )

            if len(datasets) == 0:
                pn.state.notifications.error(
                    "Failed to load any datasets",
                    duration=5000
                )
                state.is_loading = False
                compare_button.disabled = False
                return

            # Calculate color ranges
            if state.colormap_mode == 'auto':
                vmin, vmax, colormap = calculate_global_ranges(datasets)
                state.vmin = vmin
                state.vmax = vmax
                state.colormap = colormap
            else:
                # Use user-specified colormap
                vmin, vmax, _ = calculate_global_ranges(datasets)
                state.vmin = vmin
                state.vmax = vmax
                state.colormap = state.colormap_mode

            # Update state with loaded data
            state.datasets = datasets

            # Success notification
            pn.state.notifications.success(
                f"Successfully loaded {len(datasets)} dataset(s)",
                duration=3000
            )

        except Exception as e:
            print(f"Error in compare callback: {e}")
            import traceback
            traceback.print_exc()
            pn.state.notifications.error(
                f"Error loading data: {str(e)}",
                duration=10000
            )

        finally:
            # Reset loading state
            state.is_loading = False
            compare_button.disabled = False

    # Link button to async callback
    compare_button.on_click(lambda event: asyncio.create_task(on_compare_click(event)))

    # Create main template
    template = pn.template.FastListTemplate(
        title='ISMIP6 Interactive Comparison Tool',
        sidebar=[sidebar],
        main=[plot_panel],
        theme='default',
        accent_base_color='#0072B2',
        header_background='#0072B2',
        sidebar_width=340,
    )

    return template


# Create the application
app = create_app()

# Make it servable
app.servable()


if __name__ == '__main__':
    # Run with: panel serve app.py --show --autoreload
    print("Starting ISMIP6 Interactive Comparison Tool...")
    print("Run with: panel serve app.py --show --autoreload")
