"""
Configuration loader for ISMIP6 Interactive Comparison Tool.

Loads configuration from config.yaml and provides access to settings.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from YAML file.

        Parameters
        ----------
        config_path : str, optional
            Path to configuration YAML file. If not provided, looks for config.yaml
            in the project root (parent of ismip6_comparison_app directory).
        """
        if config_path is None:
            # Look for config.yaml in project root (parent of ismip6_comparison_app)
            pkg_dir = Path(__file__).parent
            project_root = pkg_dir.parent
            config_path = project_root / "config.yaml"

        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Parameters
        ----------
        key : str
            Dot-notation key (e.g., 'app.title', 'data_sources.gcs_bucket')
        default : Any
            Default value if key not found

        Returns
        -------
        Any
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Parameters
        ----------
        section : str
            Section name (e.g., 'app', 'visualization')

        Returns
        -------
        Dict[str, Any]
            Configuration section dictionary
        """
        return self._config.get(section, {})

    # Convenience properties for commonly used settings
    @property
    def gcs_bucket(self) -> str:
        """GCS bucket URL."""
        return self.get('data_sources.gcs_bucket', 'gs://ismip6')

    @property
    def cache_dir(self) -> str:
        """Cache directory path."""
        return self.get('data_sources.cache_dir', '.cache')

    @property
    def index_cache_file(self) -> str:
        """Index cache file path."""
        return self.get('data_sources.index_cache_file', '.cache/ismip6_index.parquet')

    @property
    def variables_yaml(self) -> str:
        """Variables YAML file path."""
        return self.get('data_sources.variables_yaml', 'ismip_metadata/variables.yaml')

    @property
    def experiments_yaml(self) -> str:
        """Experiments YAML file path."""
        return self.get('data_sources.experiments_yaml', 'ismip_metadata/experiments.yaml')

    @property
    def app_title(self) -> str:
        """Application title."""
        return self.get('app.title', 'ISMIP6 Interactive Comparison Tool')

    @property
    def app_port(self) -> int:
        """Application port."""
        return self.get('app.port', 5006)

    @property
    def theme_name(self) -> str:
        """Theme name."""
        return self.get('app.theme.name', 'default')

    @property
    def accent_color(self) -> str:
        """Theme accent color."""
        return self.get('app.theme.accent_color', '#0072B2')

    @property
    def header_background(self) -> str:
        """Header background color."""
        return self.get('app.theme.header_background', '#0072B2')

    @property
    def sidebar_width(self) -> int:
        """Sidebar width in pixels."""
        return self.get('app.sidebar.width', 340)

    @property
    def plot_width(self) -> int:
        """Plot width in pixels."""
        return self.get('visualization.plot_width', 450)

    @property
    def plot_height(self) -> int:
        """Plot height in pixels."""
        return self.get('visualization.plot_height', 450)

    @property
    def aspect_ratio(self):
        """Plot aspect ratio."""
        return self.get('visualization.aspect_ratio', 'equal')

    @property
    def data_aspect(self) -> float:
        """Data aspect ratio."""
        return self.get('visualization.data_aspect', 1)

    @property
    def default_nan_values(self) -> list:
        """Default NaN values."""
        return self.get('data_loading.default_nan_values', [0])

    @property
    def colormap_options(self) -> list:
        """Available colormap options."""
        return self.get('data_loading.colormap_options', ['auto', 'viridis', 'Blues', 'RdBu_r'])

    @property
    def time_step_modes(self) -> list:
        """Available time step modes."""
        return self.get('data_loading.time_step_modes', ['first', 'last', 'all', 'custom'])

    @property
    def netcdf_engine(self) -> str:
        """NetCDF reading engine."""
        return self.get('data_loading.netcdf_engine', 'h5netcdf')

    @property
    def plot_tools(self) -> list:
        """Plot interaction tools."""
        return self.get('visualization.tools', ['hover', 'pan', 'wheel_zoom', 'box_zoom', 'reset'])

    @property
    def toolbar_position(self) -> str:
        """Toolbar position."""
        return self.get('visualization.toolbar', 'above')

    @property
    def layout_columns(self) -> int:
        """Number of columns in plot layout."""
        return self.get('visualization.layout.columns', 2)

    @property
    def shared_axes(self) -> bool:
        """Whether to share axes across plots."""
        return self.get('visualization.layout.shared_axes', True)

    @property
    def percentile_low(self) -> float:
        """Low percentile for color range."""
        return self.get('visualization.percentile_range.low', 5.0)

    @property
    def percentile_high(self) -> float:
        """High percentile for color range."""
        return self.get('visualization.percentile_range.high', 95.0)

    @property
    def url_params_enabled(self) -> bool:
        """Whether URL parameters are enabled."""
        return self.get('url_params.enabled', True)

    @property
    def url_param_names(self) -> Dict[str, str]:
        """URL parameter names mapping."""
        return self.get('url_params.param_names', {})

    @property
    def url_list_delimiter(self) -> str:
        """Delimiter for list parameters in URL."""
        return self.get('url_params.list_delimiter', ',')

    @property
    def verbose_logging(self) -> bool:
        """Whether verbose logging is enabled."""
        return self.get('debug.verbose', True)

    @property
    def notifications_enabled(self) -> bool:
        """Whether notifications are enabled."""
        return self.get('ui.notifications.enabled', True)

    @property
    def success_duration(self) -> int:
        """Success notification duration (ms)."""
        return self.get('ui.notifications.success_duration', 3000)

    @property
    def warning_duration(self) -> int:
        """Warning notification duration (ms)."""
        return self.get('ui.notifications.warning_duration', 5000)

    @property
    def error_duration(self) -> int:
        """Error notification duration (ms)."""
        return self.get('ui.notifications.error_duration', 10000)


# Global config instance
_config_instance: Optional[Config] = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    Get global configuration instance.

    Parameters
    ----------
    config_path : str
        Path to configuration file

    Returns
    -------
    Config
        Configuration instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(config_path)

    return _config_instance


def load_metadata_yaml(yaml_path: str) -> Dict[str, Any]:
    """
    Load metadata from YAML file.

    Parameters
    ----------
    yaml_path : str
        Path to YAML file (relative to project root)

    Returns
    -------
    Dict[str, Any]
        Loaded YAML data
    """
    yaml_file = Path(yaml_path)

    # If path is relative, resolve from project root
    if not yaml_file.is_absolute():
        pkg_dir = Path(__file__).parent
        project_root = pkg_dir.parent
        yaml_file = project_root / yaml_path

    if not yaml_file.exists():
        print(f"Warning: Metadata file not found: {yaml_file}")
        return {}

    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    return data


if __name__ == '__main__':
    # Test configuration loading
    config = get_config()
    print(f"App title: {config.app_title}")
    print(f"GCS bucket: {config.gcs_bucket}")
    print(f"Cache file: {config.index_cache_file}")
    print(f"Variables YAML: {config.variables_yaml}")
    print(f"Experiments YAML: {config.experiments_yaml}")
    print(f"Plot size: {config.plot_width}x{config.plot_height}")
    print(f"Aspect ratio: {config.aspect_ratio}")
