"""
Sidebar component with data selection controls.

This module creates the sidebar UI with dropdowns and multi-selects
for choosing variables, models, and experiments.
"""

import panel as pn
import param
import pandas as pd
from typing import List, Dict, Any, Tuple
from config_loader import get_config, load_metadata_yaml


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

    # Loading state
    is_loading = param.Boolean(default=False)
    load_progress = param.Number(default=0, bounds=(0, 100))
    load_status = param.String(default='')

    # Loaded data (stored as dictionary)
    datasets = param.Dict(default={})
    vmin = param.Number(default=None)
    vmax = param.Number(default=None)
    colormap = param.String(default='viridis')

    def get_available_variables(self) -> List[str]:
        """Get list of available variables from file index."""
        if self.file_index.empty:
            return []
        return sorted(self.file_index['variable'].unique().tolist())

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


def create_sidebar(state: DataSelectionState) -> pn.Column:
    """
    Create the sidebar component with data selection controls.

    Parameters
    ----------
    state : DataSelectionState
        Application state object

    Returns
    -------
    pn.Column
        Sidebar panel component
    """

    # Load metadata
    var_descriptions = load_variable_descriptions()
    exp_descriptions = load_experiment_descriptions()

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
        styles={'font-size': '0.85em', 'color': '#666', 'font-style': 'italic', 'margin-top': '-8px', 'margin-bottom': '8px'}
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
        styles={'font-size': '0.85em', 'color': '#666', 'font-style': 'italic', 'margin-top': '-8px', 'margin-bottom': '8px'}
    )

    # Advanced options (collapsible)
    time_step_mode_select = pn.widgets.Select(
        name='Time Step',
        options=['first', 'last', 'all', 'custom'],
        value=state.time_step_mode,
        width=280,
        sizing_mode='stretch_width'
    )

    time_step_input = pn.widgets.IntInput(
        name='Custom Time Step',
        value=state.time_step,
        start=0,
        width=280,
        sizing_mode='stretch_width',
        visible=False
    )

    colormap_select = pn.widgets.Select(
        name='Colormap',
        options=['auto', 'viridis', 'Blues', 'RdBu_r', 'plasma', 'cividis'],
        value=state.colormap_mode,
        width=280,
        sizing_mode='stretch_width'
    )

    nan_values_input = pn.widgets.TextInput(
        name='NaN Values (comma-separated)',
        value=state.nan_values,
        placeholder='e.g., 0, -999',
        width=280,
        sizing_mode='stretch_width'
    )

    auto_range_checkbox = pn.widgets.Checkbox(
        name='Auto color range (5th-95th percentile)',
        value=state.auto_range,
        width=280,
        sizing_mode='stretch_width'
    )

    advanced_options = pn.Card(
        time_step_mode_select,
        time_step_input,
        colormap_select,
        nan_values_input,
        auto_range_checkbox,
        title='Advanced Options',
        collapsed=True,
        width=300,
        sizing_mode='stretch_width'
    )

    # Info box
    info_text = pn.pane.Markdown(
        '',
        width=280,
        sizing_mode='stretch_width',
        styles={
            'background-color': '#e8f4f8',
            'padding': '10px',
            'border-radius': '4px',
            'border-left': '4px solid #0072B2'
        }
    )

    # Compare button
    compare_button = pn.widgets.Button(
        name='Compare Selected Data',
        button_type='primary',
        width=280,
        sizing_mode='stretch_width',
        disabled=True
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

    def update_time_step_input(*events):
        time_step_input.visible = (time_step_mode_select.value == 'custom')

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
    time_step_mode_select.link(state, value='time_step_mode')
    time_step_input.link(state, value='time_step')
    colormap_select.link(state, value='colormap_mode')
    nan_values_input.link(state, value='nan_values')
    auto_range_checkbox.link(state, value='auto_range')

    # Watch for changes
    state.param.watch(update_variable_options, 'file_index')
    state.param.watch(update_models_options, ['selected_variable', 'file_index'])
    state.param.watch(update_experiments_options, ['selected_variable', 'selected_models', 'file_index'])
    state.param.watch(update_info_box, ['selected_variable', 'selected_models', 'selected_experiments', 'file_index'])
    state.param.watch(update_variable_description, 'selected_variable')
    state.param.watch(update_experiment_descriptions, 'selected_experiments')
    time_step_mode_select.param.watch(update_time_step_input, 'value')

    # Initial updates
    update_variable_options()
    update_models_options()
    update_experiments_options()
    update_info_box()
    update_variable_description()
    update_experiment_descriptions()

    # Create sidebar layout
    sidebar = pn.Column(
        pn.pane.Markdown('### Data Selection'),
        variable_select,
        var_desc_pane,
        models_select,
        experiments_select,
        exp_desc_pane,
        advanced_options,
        info_text,
        compare_button,
        width=320,
        sizing_mode='stretch_height',
        styles={
            'padding': '15px',
            'background': 'white'
        }
    )

    return sidebar, compare_button
