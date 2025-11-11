# What is this?

This is a very early proof-of-concept visualization tool for exploring and comparing model outputs from the Ice Sheet Model Intercomparison Project for CMIP6 (ISMIP6). [ISMIP](https://www.ismip.org/) is an international collaborative effort to compare the behavior of ice sheet models under a standardized set of experiments. This tool is not affiliated with ISMIP -- it's just a visualizer of publicly-available ISMIP6 outputs.

The tool is a prototype article for a larger push we're working on to build backend infrastrcuture for model-data comparisons. If you're intersted in that, feel free to check back here as we add more information or reach out to thomas.teisberg@astera.org.

We hope this tool is useful and intersting to the scientific community. If you find it useful or you find issues, we encourage you to email us or [open an issue](https://github.com/englacial/ismip-indexing/issues/new).

## More about ISMIP6 and the context behind these models

This tool visualizes only model outputs from the ISMIP6 Antarctica ensemble for now. The general structure of those experiments is described [on the ISMIP6 wiki](https://theghub.org/groups/ismip6/wiki/MainPage/ISMIP6ProjectionsAntarctica). For details, please read the [ISMIP6 Antartica results paper](https://tc.copernicus.org/articles/14/3033/2020/) in *The Cryosphere*.

## Open Source

This tool is open source. Visit the [GitHub repository](https://github.com/englacial/ismip-indexing) to contribute or report issues.

## Getting started

The sidebar on the left allows you to select a variable of interest and one or more models and experiments to visualize. Not all modeling groups submitted data for all experiments and variables, so a table will display ✓ icons for each available data product. Click "Compare Selected Data" to load visualizations of the selected data. You can zoom and interact with the plots on the right after loading some data. Keep in mind that data is loaded dynamically on request and large data requests may take some time to load.

Click on the "Example Comparisons" tab for some suggested starting points or the "Comparison Tool" tab to get started.
