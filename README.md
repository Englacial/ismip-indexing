# ISMIP6 Model Outputs Indexing and Comparison Tool

TL;DR: Start here: [models.englacial.org](https://models.englacial.org)

## Users

This repository contains two different tools for understanding and visualizing model outputs from the [ISMIP6](https://www.ismip.org/) model comparison project. We're not associated with ISMIP. This are viewer tools for publicly-available data outputs that we hope are intersting and useful to the scientific community.

### ISMIP6 outputs indexing

There is a GitHub workflow in `.github/workflows/deploy-pages.yml` that builds a static site indexing what IMSIP6 outputs are available.

You can find this site here: [https://docs.englacial.org/ismip-indexing/](https://docs.englacial.org/ismip-indexing/)

Note that data files marked "not available" could exist but simply have some formatting issue that prevented us from automatically loading them. We've tried to automatically correct some basic formatting issues, but we may have missed some things. Feel free to [open an issue](https://github.com/englacial/ismip-indexing/issues/new).

In order to make this work, we've hosted a copy of the ISMIP6 outputs (which are [available through Globus](https://theghub.org/accessing-data-with-globus)) on our own Google Cloud Storage bucket. It's located at `gs://ismip6`. This is entirely unofficial, but you're welcome to use it if it helps. No authentication is required. For guidance on citations, please refer to the [ISMIP wiki](https://theghub.org/groups/ismip6/wiki/PublicationsCitationGuidance).

### Interactive ISMIP6 Antarctica outputs comparison tool

This repository also contains a prototype web-based comparison tool for visualizing ISMIP6 Antarctica outputs.

You can find this tool at [models.englacial.org](https://models.englacial.org).

## Developers

If you want to run a local copy, you can setup the tool like this:

```bash
# Install dependencies
uv sync

# Launch web app
uv run panel serve app.py --show --static-dirs static_content=./static_content
```

Visit `http://localhost:5006/app` to explore the data interactively.

### Python API

The core of both tools is a simple Python library for reading and managing ISMIP6 outputs. This library is repsonsible for creating an index of data files and correcting minor formatting errors in the datasets, such as incorrect location information and typos in file names.

```python
from ismip6_index import get_file_index

# Get file index (cached)
df = get_file_index()

# Force rebuild
df = get_file_index(force_rebuild=True)
```

### Data Overview

- **10,034 files** (~1.1 TB total)
- **17 models** from 14 institutions
- **94 experiments**
- **37 variables**
- All Antarctic ice sheet (AIS) data
- Public access via `gs://ismip6` (no authentication required)
