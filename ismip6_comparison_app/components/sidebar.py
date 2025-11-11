"""
Sidebar component with data selection controls.

This module creates the sidebar UI with dropdowns and multi-selects
for choosing variables, models, and experiments.
"""

import panel as pn
import param
import pandas as pd
from typing import List, Dict, Any, Tuple
from ..config_loader import get_config, load_metadata_yaml


class DataSelectionState(param.Parameterized):
    """
    Parameterized class to manage data selection state.
    """
    # Data index
    file_index = param.DataFrame(default=pd.DataFrame())

    # User selections
    selected_variable = param.Selector(default=None, objects=[])
    selected_models = param.ListSelector(default=[], objects=[])
    selected_experiments = param.ListSelector(default=[], objects=[])

    # Advanced options
    time_step = param.Integer(default=0, bounds=(0, None))
    time_step_mode = param.Selector(default='first', objects=['first', 'last', 'all', 'custom'])
    colormap_mode = param.Selector(default='auto', objects=[
        'auto', 'viridis', 'Blues', 'RdBu_r', 'plasma', 'cividis'
    ])
    nan_values = param.String(default='0')
    auto_range = param.Boolean(default=True)
    vmin_manual = param.Number(default=None)
    vmax_manual = param.Number(default=None)

    # Loading state
    is_loading = param.Boolean(default=False)
    load_progress = param.Number(default=0, bounds=(0, 100))
    load_status = param.String(default='')

    # Loaded data (stored as dictionary)
    datasets = param.Dict(default={})
    vmin = param.Number(default=None)
    vmax = param.Number(default=None)
    colormap = param.String(default='viridis')

    # Time slider state
    time_slider_year = param.Number(default=2015)
    time_range_min = param.Number(default=2015)
    time_range_max = param.Number(default=2100)
    time_slider_visible = param.Boolean(default=False)

    def get_available_variables(self) -> List[str]:
        """Get list of available variables from file index, excluding scalar variables."""
        if self.file_index.empty:
            return []

        # Get all unique variables
        all_variables = self.file_index['variable'].unique().tolist()

        # Load variable metadata to filter out scalar variables
        from ..config_loader import get_config, load_metadata_yaml
        config = get_config()
        variables_data = load_metadata_yaml(config.variables_yaml)

        # Filter out scalar variables (only keep 2D spatial variables)
        spatial_variables = []
        if 'variables' in variables_data:
            for var in all_variables:
                var_info = variables_data['variables'].get(var, {})
                var_type = var_info.get('variable_type', '2D')
                # Only include 2D variables, exclude scalar
                if var_type != 'scalar':
                    spatial_variables.append(var)
        else:
            # If no metadata available, include all variables
            spatial_variables = all_variables

        return sorted(spatial_variables)

    def get_available_models(self) -> List[str]:
        """Get list of available models for selected variable."""
        if self.file_index.empty or self.selected_variable is None:
            return []

        filtered = self.file_index[
            self.file_index['variable'] == self.selected_variable
        ]
        return sorted(filtered['model'].unique().tolist())

    def get_available_experiments(self) -> List[str]:
        """Get list of available experiments for selected variable and models."""
        if self.file_index.empty or self.selected_variable is None:
            return []

        filtered = self.file_index[
            self.file_index['variable'] == self.selected_variable
        ]

        if len(self.selected_models) > 0:
            filtered = filtered[filtered['model'].isin(self.selected_models)]

        return sorted(filtered['experiment'].unique().tolist())

    def get_matched_files(self) -> pd.DataFrame:
        """Get files matching current selection criteria."""
        if self.file_index.empty or self.selected_variable is None:
            return pd.DataFrame()

        filtered = self.file_index[
            (self.file_index['variable'] == self.selected_variable) &
            (self.file_index['model'].isin(self.selected_models)) &
            (self.file_index['experiment'].isin(self.selected_experiments))
        ]

        return filtered

    def get_nan_values_list(self) -> List[float]:
        """Parse NaN values string into list of floats."""
        if not self.nan_values.strip():
            return []

        values = []
        for val in self.nan_values.split(','):
            try:
                values.append(float(val.strip()))
            except ValueError:
                pass
        return values

    def get_time_step_value(self) -> int:
        """Get the actual time step value based on mode."""
        if self.time_step_mode == 'first':
            return 0
        elif self.time_step_mode == 'last':
            return -1
        elif self.time_step_mode == 'all':
            return None
        else:  # custom
            return self.time_step


def load_variable_descriptions() -> Dict[str, str]:
    """Load variable descriptions from YAML."""
    config = get_config()
    variables_data = load_metadata_yaml(config.variables_yaml)

    descriptions = {}
    if 'variables' in variables_data:
        for var_name, var_info in variables_data['variables'].items():
            desc = var_info.get('description', '')
            units = var_info.get('units', '')
            if desc:
                descriptions[var_name] = f"{desc}" + (f" ({units})" if units else "")

    return descriptions


def load_experiment_descriptions() -> Dict[str, str]:
    """Load experiment descriptions from YAML."""
    config = get_config()
    exp_data = load_metadata_yaml(config.experiments_yaml)

    descriptions = {}
    if 'projection_experiments' in exp_data:
        for exp_id, exp_info in exp_data['projection_experiments'].items():
            desc = exp_info.get('description', '')
            if desc:
                descriptions[exp_id] = desc

    if 'initialization_experiments' in exp_data:
        for exp_id, exp_info in exp_data['initialization_experiments'].items():
            desc = exp_info.get('description', '')
            if desc:
                descriptions[exp_id] = desc

    return descriptions


def format_options_with_descriptions(
    options: List[str],
    descriptions: Dict[str, str],
    max_length: int = 60
) -> Dict[str, str]:
    """
    Format options as dict with descriptions for display.

    Parameters
    ----------
    options : List[str]
        List of option values
    descriptions : Dict[str, str]
        Dictionary of descriptions
    max_length : int
        Maximum length for truncated descriptions

    Returns
    -------
    Dict[str, str]
        Dictionary mapping display label to value
    """
    formatted = {}
    for opt in options:
        desc = descriptions.get(opt, '')
        if desc:
            # Truncate long descriptions
            if len(desc) > max_length:
                desc = desc[:max_length-3] + '...'
            label = f"{opt} - {desc}"
        else:
            label = opt
        formatted[label] = opt

    return formatted


def create_sidebar(state: DataSelectionState) -> Tuple[pn.Column, pn.widgets.Button]:
    """
    Create the sidebar component with data selection controls.

    Parameters
    ----------
    state : DataSelectionState
        Application state object

    Returns
    -------
    Tuple[pn.Column, pn.widgets.Button]
        Sidebar panel component and compare button
    """

    # Load metadata
    var_descriptions = load_variable_descriptions()
    exp_descriptions = load_experiment_descriptions()

    # Load config defaults
    config = get_config()
    default_variable = config.get('app.defaults.variable', None)
    default_models = config.get('app.defaults.models', [])
    default_experiments = config.get('app.defaults.experiments', [])

    # Check for URL parameters (override config defaults)
    if pn.state.location:
        url_params = pn.state.location.query_params
        if 'var' in url_params and url_params['var']:
            default_variable = url_params['var']
        if 'models' in url_params and url_params['models']:
            default_models = url_params['models'].split(',')
        if 'exps' in url_params and url_params['exps']:
            default_experiments = url_params['exps'].split(',')
        # Also read other parameters
        if 'cmap' in url_params and url_params['cmap']:
            state.colormap_mode = url_params['cmap']
        if 'nan' in url_params and url_params['nan']:
            state.nan_values = url_params['nan']

    # Variable selection
    variable_select = pn.widgets.Select(
        name='Variable',
        options=state.get_available_variables(),
        value=state.selected_variable,
        sizing_mode='stretch_width',
        description="Choose the variable to visualize"
    )

    # Variable description pane (updates when selection changes)
    var_desc_pane = pn.pane.Markdown(
        '',
        sizing_mode='stretch_width',
        styles={'font-size': '0.85em', 'font-style': 'italic', 'margin-top': '-8px', 'margin-bottom': '8px'}
    )

    # Models multi-select
    models_select = pn.widgets.MultiChoice(
        name='Models',
        options=state.get_available_models(),
        value=list(state.selected_models),
        placeholder='Select models...',
        sizing_mode='stretch_width',
        max_items=20,
        description="Choose one or more ice sheet models"
    )

    # Experiments multi-select
    experiments_select = pn.widgets.MultiChoice(
        name='Experiments',
        options=state.get_available_experiments(),
        value=list(state.selected_experiments),
        placeholder='Select experiments...',
        sizing_mode='stretch_width',
        max_items=20,
        description="Choose one or more experiments"
    )

    # Experiment description pane (updates when selection changes)
    exp_desc_pane = pn.pane.Markdown(
        '',
        sizing_mode='stretch_width',
        styles={'font-size': '0.85em', 'font-style': 'italic', 'margin-top': '-8px', 'margin-bottom': '8px'}
    )

    # Advanced options (collapsible)
    colormap_select = pn.widgets.Select(
        name='Colormap',
        options=['auto', 'viridis', 'Blues', 'RdBu_r', 'plasma', 'cividis'],
        value=state.colormap_mode,
        sizing_mode='stretch_width'
    )

    nan_values_input = pn.widgets.TextInput(
        name='NaN Values (comma-separated)',
        value=state.nan_values,
        placeholder='e.g., 0, -999',
        sizing_mode='stretch_width'
    )

    # Get percentile values from config for label
    percentile_low = config.get('visualization.percentile_range.low', 5.0)
    percentile_high = config.get('visualization.percentile_range.high', 95.0)

    auto_range_checkbox = pn.widgets.Checkbox(
        name=f'Auto color range ({percentile_low:.0f}th-{percentile_high:.0f}th percentile)',
        value=state.auto_range,
        sizing_mode='stretch_width'
    )

    # Manual color range inputs (shown when auto_range is False)
    vmin_input = pn.widgets.FloatInput(
        name='Min Value',
        value=state.vmin_manual,
        placeholder='Enter minimum',
        sizing_mode='stretch_width',
        visible=not state.auto_range
    )

    vmax_input = pn.widgets.FloatInput(
        name='Max Value',
        value=state.vmax_manual,
        placeholder='Enter maximum',
        sizing_mode='stretch_width',
        visible=not state.auto_range
    )

    # Data availability table
    availability_table = pn.pane.HTML(
        '',
        sizing_mode='stretch_width',
        styles={
            'font-size': '0.85em',
            'overflow-x': 'auto'
        }
    )

    def update_availability_table(*events):
        """Update the data availability table based on current selections."""
        if not state.selected_variable or not state.selected_models or not state.selected_experiments:
            availability_table.object = ''
            return

        # Get all files for the selected variable
        var_files = state.file_index[state.file_index['variable'] == state.selected_variable]

        # Create HTML table
        html = '<table style="width:100%; border-collapse: collapse; margin: 10px 0;">'
        html += '<thead><tr style="background-color: #f0f0f0;">'
        html += '<th style="padding: 5px; border: 1px solid #ddd; text-align: left;">Model</th>'

        # Header row with experiments
        for exp in state.selected_experiments:
            html += f'<th style="padding: 5px; border: 1px solid #ddd; text-align: center;">{exp}</th>'
        html += '</tr></thead><tbody>'

        # Row for each model
        for model in state.selected_models:
            html += '<tr>'
            html += f'<td style="padding: 5px; border: 1px solid #ddd; font-weight: bold;">{model}</td>'

            for exp in state.selected_experiments:
                # Check if file exists for this model/experiment combination
                match = var_files[
                    (var_files['model'] == model) &
                    (var_files['experiment'] == exp)
                ]

                if not match.empty:
                    # File exists - show checkmark with link
                    url = match.iloc[0]['url']
                    # Convert gs:// to https:// for browser access
                    https_url = url.replace('gs://', 'https://storage.googleapis.com/')
                    html += f'<td style="padding: 5px; border: 1px solid #ddd; text-align: center;">'
                    html += f'<a href="{https_url}" target="_blank" title="Open data file">✓</a>'
                    html += '</td>'
                else:
                    # File missing - show X
                    html += '<td style="padding: 5px; border: 1px solid #ddd; text-align: center; color: #999;">✗</td>'

            html += '</tr>'

        html += '</tbody></table>'
        availability_table.object = html

    advanced_options = pn.Card(
        colormap_select,
        nan_values_input,
        auto_range_checkbox,
        vmin_input,
        vmax_input,
        title='Advanced Options',
        collapsed=True,
        sizing_mode='stretch_width'
    )

    # Info box
    info_text = pn.pane.Markdown(
        '',
        sizing_mode='stretch_width',
        styles={
            'padding': '10px',
            'border-radius': '4px',
            'border-left': '4px solid #0072B2'
        }
    )

    # Compare button
    compare_button = pn.widgets.Button(
        name='Compare Selected Data',
        button_type='primary',
        sizing_mode='stretch_width',
        disabled=True
    )

    # Time slider (initially hidden)
    time_slider = pn.widgets.IntSlider(
        name='Year',
        start=int(state.time_range_min),
        end=int(state.time_range_max),
        value=int(state.time_slider_year),
        step=1,
        sizing_mode='stretch_width',
        visible=state.time_slider_visible
    )

    # Update functions
    def update_variable_options(*events):
        variable_select.options = state.get_available_variables()
        if state.selected_variable not in variable_select.options:
            state.selected_variable = None

    def update_models_options(*events):
        models_select.options = state.get_available_models()
        # Keep only valid selections
        state.selected_models = [
            m for m in state.selected_models
            if m in models_select.options
        ]
        models_select.value = list(state.selected_models)

    def update_experiments_options(*events):
        experiments_select.options = state.get_available_experiments()
        # Keep only valid selections
        state.selected_experiments = [
            e for e in state.selected_experiments
            if e in experiments_select.options
        ]
        experiments_select.value = list(state.selected_experiments)

    def update_info_box(*events):
        matched_files = state.get_matched_files()
        num_files = len(matched_files)

        if num_files > 0:
            total_size_mb = matched_files['size_bytes'].sum() / (1024 * 1024)
            est_time = max(15, int(total_size_mb / 10))

            info_text.object = f"""
**Files matched:** {num_files}

**Total size:** ~{total_size_mb:.1f} MB

**Est. load time:** {est_time}-{est_time*2} sec
            """
            compare_button.disabled = False
        else:
            info_text.object = "**No files matched**\n\nSelect variable, models, and experiments"
            compare_button.disabled = True

    def update_variable_description(*events):
        """Update variable description when selection changes."""
        var = state.selected_variable
        if var and var in var_descriptions:
            var_desc_pane.object = f"*{var_descriptions[var]}*"
        else:
            var_desc_pane.object = ''

    def update_experiment_descriptions(*events):
        """Update experiment descriptions when selection changes."""
        exps = state.selected_experiments
        if exps:
            desc_list = []
            for exp in exps[:3]:  # Show max 3 to avoid clutter
                if exp in exp_descriptions:
                    desc_list.append(f"**{exp}**: {exp_descriptions[exp][:60]}...")
            if len(exps) > 3:
                desc_list.append(f"*...and {len(exps)-3} more*")
            exp_desc_pane.object = '\n\n'.join(desc_list) if desc_list else ''
        else:
            exp_desc_pane.object = ''

    def update_time_slider_range(*events):
        """Update time slider range when state changes."""
        time_slider.start = int(state.time_range_min)
        time_slider.end = int(state.time_range_max)
        time_slider.value = int(state.time_slider_year)
        time_slider.visible = state.time_slider_visible

    def update_manual_range_visibility(*events):
        """Show/hide manual range inputs based on auto_range checkbox."""
        vmin_input.visible = not state.auto_range
        vmax_input.visible = not state.auto_range

    def apply_manual_color_range(*events):
        """Apply manual color range values when they change (only if auto_range is off)."""
        if not state.auto_range and len(state.datasets) > 0:
            # Update vmin/vmax from manual inputs
            if state.vmin_manual is not None:
                state.vmin = state.vmin_manual
            if state.vmax_manual is not None:
                state.vmax = state.vmax_manual

    def handle_auto_range_toggle(*events):
        """Handle toggling of auto_range checkbox."""
        if state.auto_range and len(state.datasets) > 0:
            # Re-enable auto mode: recalculate color ranges from loaded data
            from .data_loader import calculate_global_ranges
            from ..config_loader import get_config
            config = get_config()
            percentile_low = config.get('visualization.percentile_range.low', 5.0)
            percentile_high = config.get('visualization.percentile_range.high', 95.0)

            if state.colormap_mode == 'auto':
                vmin, vmax, colormap = calculate_global_ranges(
                    state.datasets,
                    percentile_low=percentile_low,
                    percentile_high=percentile_high
                )
                state.vmin = vmin
                state.vmax = vmax
                state.colormap = colormap
            else:
                # Use user-specified colormap but auto-calculate range
                vmin, vmax, _ = calculate_global_ranges(
                    state.datasets,
                    percentile_low=percentile_low,
                    percentile_high=percentile_high
                )
                state.vmin = vmin
                state.vmax = vmax
                state.colormap = state.colormap_mode

            # Update manual inputs to show the auto-calculated values
            state.vmin_manual = state.vmin
            state.vmax_manual = state.vmax

    # Link widgets to state
    variable_select.link(state, value='selected_variable')
    models_select.param.watch(
        lambda event: setattr(state, 'selected_models', list(event.new)),
        'value'
    )
    experiments_select.param.watch(
        lambda event: setattr(state, 'selected_experiments', list(event.new)),
        'value'
    )
    colormap_select.link(state, value='colormap_mode')
    nan_values_input.link(state, value='nan_values')
    auto_range_checkbox.link(state, value='auto_range')
    vmin_input.link(state, value='vmin_manual')
    vmax_input.link(state, value='vmax_manual')
    # Use value_throttled for the slider to only update on mouse release
    time_slider.link(state, value_throttled='time_slider_year')

    # Watch for changes
    state.param.watch(update_variable_options, 'file_index')
    state.param.watch(update_models_options, ['selected_variable', 'file_index'])
    state.param.watch(update_experiments_options, ['selected_variable', 'selected_models', 'file_index'])
    state.param.watch(update_info_box, ['selected_variable', 'selected_models', 'selected_experiments', 'file_index'])
    state.param.watch(update_variable_description, 'selected_variable')
    state.param.watch(update_experiment_descriptions, 'selected_experiments')
    state.param.watch(update_availability_table, ['selected_variable', 'selected_models', 'selected_experiments', 'file_index'])
    state.param.watch(update_time_slider_range, ['time_range_min', 'time_range_max', 'time_slider_year', 'time_slider_visible'])
    state.param.watch(update_manual_range_visibility, 'auto_range')
    state.param.watch(handle_auto_range_toggle, 'auto_range')
    state.param.watch(apply_manual_color_range, ['vmin_manual', 'vmax_manual'])

    # Initial updates
    update_variable_options()
    update_models_options()
    update_experiments_options()

    # Apply default selections from config
    if default_variable and default_variable in variable_select.options:
        state.selected_variable = default_variable
        variable_select.value = default_variable

    # Update models list after variable is set
    update_models_options()

    # Apply default models
    if default_models:
        valid_models = [m for m in default_models if m in models_select.options]
        if valid_models:
            state.selected_models = valid_models
            models_select.value = valid_models

    # Update experiments list after models are set
    update_experiments_options()

    # Apply default experiments
    if default_experiments:
        valid_experiments = [e for e in default_experiments if e in experiments_select.options]
        if valid_experiments:
            state.selected_experiments = valid_experiments
            experiments_select.value = valid_experiments

    update_info_box()
    update_variable_description()
    update_experiment_descriptions()
    update_availability_table()

    # Create sidebar layout
    sidebar = pn.Column(
        pn.pane.Markdown('### Data Selection'),
        variable_select,
        var_desc_pane,
        models_select,
        experiments_select,
        exp_desc_pane,
        availability_table,
        advanced_options,
        info_text,
        compare_button,
        time_slider,
        sizing_mode='stretch_height',
        styles={
            'padding': '15px',
            'background': 'white'
        }
    )

    return sidebar, compare_button
