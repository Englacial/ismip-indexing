"""
Generic markdown page component.

This module creates a static page from a markdown file,
allowing easy creation of documentation, examples, or other static content.
"""

import panel as pn
from pathlib import Path
from typing import Optional, Dict, Callable, Any, List, Union


def create_markdown_page(
    markdown_file: str,
    title: Optional[str] = None,
    styles: Optional[Dict[str, str]] = None,
    action_button: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
) -> pn.Column:
    """
    Create a page from a markdown file.

    Parameters
    ----------
    markdown_file : str
        Path to the markdown file (relative to project root)
    title : str, optional
        Title to display if file is not found
    styles : dict, optional
        Custom CSS styles for the markdown pane
        Default: {'padding': '20px', 'max-width': '900px', 'margin': '0 auto'}
    action_button : dict or list of dict, optional
        Button configuration(s): {'label': str, 'callback': callable, 'button_type': str}
        Can be a single dict or a list of dicts for multiple buttons
        If provided, adds button(s) at the bottom of the page

    Returns
    -------
    pn.Column
        The markdown page component

    Examples
    --------
    >>> page = create_markdown_page('docs/examples.md', title='Examples')
    >>> page = create_markdown_page('README.md', styles={'padding': '10px'})
    >>> page = create_markdown_page('about.md', action_button={'label': 'Get Started', 'callback': my_func})
    """
    # Load markdown content from file
    md_path = Path(markdown_file)

    if md_path.exists():
        with open(md_path, 'r') as f:
            content = f.read()
    else:
        # Fallback content if file not found
        file_title = title or md_path.stem.replace('_', ' ').title()
        content = f"""
# {file_title}

*Content file not found: `{markdown_file}`*

Please create the file to add content to this page.
        """

    # Default styles
    default_styles = {
        'padding': '20px',
        'max-width': '900px',
        'margin': '0 auto'
    }

    # Merge with custom styles if provided
    if styles:
        default_styles.update(styles)

    # Create markdown pane with styling
    markdown_pane = pn.pane.Markdown(
        content,
        sizing_mode='stretch_width',
        styles=default_styles
    )

    # Prepare page components
    page_components = [markdown_pane]

    # Add action button(s) if provided
    if action_button:
        # Normalize to list if single button provided
        buttons_config = action_button if isinstance(action_button, list) else [action_button]

        # Create buttons
        buttons = []
        for btn_config in buttons_config:
            button_label = btn_config.get('label', 'Continue')
            button_callback = btn_config.get('callback')
            button_type = btn_config.get('button_type', 'primary')

            button = pn.widgets.Button(
                name=button_label,
                button_type=button_type,
                width=200,
                margin=(0, 10, 0, 10)  # Add horizontal spacing between buttons
            )

            if button_callback:
                button.on_click(button_callback)

            buttons.append(button)

        # Add spacing and buttons in a centered row
        page_components.append(pn.layout.Spacer(height=20))

        # Wrap buttons in a row with center alignment
        button_row = pn.Row(
            pn.layout.HSpacer(),  # Left spacer to push buttons to center
            *buttons,
            pn.layout.HSpacer(),  # Right spacer to keep buttons centered
            sizing_mode='stretch_width'
        )
        page_components.append(button_row)

    # Wrap in column
    page = pn.Column(
        *page_components,
        sizing_mode='stretch_both'
    )

    return page
