#!/usr/bin/env python3
"""
ISMIP6 Interactive Comparison Tool - Main Application

A Panel web application for comparing ISMIP6 ice sheet model outputs.
"""

import panel as pn
import holoviews as hv
import asyncio
from functools import partial
from pathlib import Path

from ismip6_helper import get_file_index
from .components.sidebar import DataSelectionState, create_sidebar
from .components.plot_panel import create_plot_panel
from .components.markdown_page import create_markdown_page
from .components.data_loader import (
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

    # Helper function to safely send notifications
    def safe_notification(level: str, message: str, duration: int = 3000):
        """Send notification if notifications are available."""
        if pn.state.notifications is not None:
            if level == 'success':
                pn.state.notifications.success(message, duration=duration)
            elif level == 'warning':
                pn.state.notifications.warning(message, duration=duration)
            elif level == 'error':
                pn.state.notifications.error(message, duration=duration)
        else:
            # Fallback to console logging
            print(f"[{level.upper()}] {message}")

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

    # Create tabs for navigation (created early so callback can reference it)
    tabs = pn.Tabs(
        dynamic=True,
        sizing_mode='stretch_both',
        active=0  # Start on the About tab (first tab, index 0)
    )

    # Compare button callback
    async def on_compare_click(event, is_auto_load=False):
        """Handle compare button click - load data and create plots."""
        try:
            # Get matched files
            matched_files = state.get_matched_files()

            if matched_files.empty:
                safe_notification('warning', "No files matched the selection criteria", 3000)
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
            datasets, time_range = await load_datasets_async(
                file_list=file_list,
                variable=state.selected_variable,
                nan_values=state.get_nan_values_list(),
                time_step=state.get_time_step_value(),
                progress_callback=update_progress
            )

            if len(datasets) == 0:
                safe_notification('error', "Failed to load any datasets", 5000)
                state.is_loading = False
                compare_button.disabled = False
                return

            # Update time slider if time range is available
            if time_range is not None:
                min_year, max_year = time_range
                state.time_range_min = min_year
                state.time_range_max = max_year
                state.time_slider_year = min_year
                state.time_slider_visible = True
                print(f"Time slider enabled: {min_year} - {max_year}")
            else:
                # No time dimension - hide time slider
                state.time_slider_visible = False
                print("No time dimension found - time slider hidden")

            # Calculate color ranges
            if state.auto_range:
                # Auto mode - calculate from data
                if state.colormap_mode == 'auto':
                    vmin, vmax, colormap = calculate_global_ranges(datasets)
                    state.vmin = vmin
                    state.vmax = vmax
                    state.colormap = colormap
                else:
                    # Use user-specified colormap but auto-calculate range
                    vmin, vmax, _ = calculate_global_ranges(datasets)
                    state.vmin = vmin
                    state.vmax = vmax
                    state.colormap = state.colormap_mode

                # Populate manual inputs with calculated values
                state.vmin_manual = state.vmin
                state.vmax_manual = state.vmax
            else:
                # Manual mode - use user-specified values
                # Only update if manual values are provided
                if state.vmin_manual is not None:
                    state.vmin = state.vmin_manual
                if state.vmax_manual is not None:
                    state.vmax = state.vmax_manual

                # Set colormap
                if state.colormap_mode == 'auto':
                    # If colormap is auto but range is manual, use a default
                    state.colormap = 'viridis'
                else:
                    state.colormap = state.colormap_mode

            # Update state with loaded data
            state.datasets = datasets

            # Update URL parameters to make the view shareable
            if pn.state.location:
                pn.state.location.update_query(
                    var=state.selected_variable,
                    models=','.join(state.selected_models),
                    exps=','.join(state.selected_experiments),
                    cmap=state.colormap_mode,
                    nan=state.nan_values
                )

            # Success notification
            safe_notification('success', f"Successfully loaded {len(datasets)} dataset(s)", 3000)

            # Switch to Comparison Tool tab to show the results (but not on auto-load)
            if not is_auto_load:
                tabs.active = 1  # Index 1 is the Comparison Tool tab

        except Exception as e:
            print(f"Error in compare callback: {e}")
            import traceback
            traceback.print_exc()
            safe_notification('error', f"Error loading data: {str(e)}", 10000)

        finally:
            # Reset loading state
            state.is_loading = False
            compare_button.disabled = False

    # Link button to async callback
    compare_button.on_click(lambda event: asyncio.create_task(on_compare_click(event)))

    # Auto-load default data on first page load
    async def auto_load_defaults():
        """Automatically load default selections on first page load."""
        from .config_loader import get_config
        config = get_config()
        auto_load = config.get('app.defaults.auto_load', False)

        if auto_load and state.selected_variable and state.selected_models and state.selected_experiments:
            print("Auto-loading default data...")
            # Trigger the compare button click (with is_auto_load=True to prevent tab switch)
            await on_compare_click(None, is_auto_load=True)

    # Trigger auto-load on page load using Panel's async execution
    def schedule_auto_load():
        pn.state.execute(auto_load_defaults)

    pn.state.onload(schedule_auto_load)

    # Create callbacks to switch tabs
    def go_to_comparison_tool(event):
        """Switch to the Comparison Tool tab."""
        tabs.active = 1  # Index 1 is the Comparison Tool tab

    def go_to_examples(event):
        """Switch to the Example Comparisons tab."""
        tabs.active = 2  # Index 2 is the Example Comparisons tab

    # Create markdown pages with action buttons for About page
    static_dir = Path(__file__).parent / 'static_content'
    about_page = create_markdown_page(
        str(static_dir / 'about.md'),
        title='About',
        action_button=[
            {
                'label': 'See some examples',
                'callback': go_to_examples,
                'button_type': 'success'
            },
            {
                'label': 'Go to Comparison Tool →',
                'callback': go_to_comparison_tool,
                'button_type': 'primary'
            }
        ]
    )
    examples_page = create_markdown_page(
        str(static_dir / 'example_comparisons.md'),
        title='Example Comparisons'
    )

    # Add pages to tabs
    tabs.extend([
        ('About', about_page),
        ('Comparison Tool', plot_panel),
        ('Example Comparisons', examples_page),
    ])

    # Create GitHub link for header
    github_link = pn.pane.HTML(
        '<a href="https://github.com/englacial/ismip-indexing" target="_blank" '
        'style="color: white; text-decoration: none; padding: 10px; '
        'display: inline-block; opacity: 0.9; transition: opacity 0.2s;" '
        'title="View on GitHub" '
        'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.9">'
        '<svg style="vertical-align: middle;" height="24" width="24" '
        'viewBox="0 0 16 16" fill="white">'
        '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
        '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
        '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
        '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
        '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 '
        '3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 '
        '8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>'
        '</a>',
        sizing_mode='fixed',
        width=44,
        height=40
    )

    # Create main template
    template = pn.template.FastListTemplate(
        title='ISMIP6 Interactive Comparison Tool',
        sidebar=[sidebar],
        main=[tabs],
        header=[github_link],
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
