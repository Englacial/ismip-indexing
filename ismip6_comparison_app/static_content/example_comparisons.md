# Example Comparisons

This page provides some starting points for interesting comparisons to look at.

## Subglacial temperature

<img src="/static_content/example-temperature.png" alt="Basal temperature comparison screenshot" style="width: 100%; max-width: 50em; height: auto;">

* **Variable:** `litempbotgr` Basal temperature beneath grounded ice sheet (K)
* **Models:** `AWI/PISM1`, `DOE/MALI`, `LSCE/GRISLI2`, `NCAR/CISM`
* **Experiment:** `exp05`

There are few direct measurements of the temperature profile within on beneath ice sheets. As a result, basal temperature (temperate at the ice-bedrock interface) is poorly constrained. Models resolve a wide range of temperatures, ranging from deeply frozen to at or near the pressure melting point.

<a href="/app?var=litempbotgr&models=NCAR%2FCISM%2CDOE%2FMALI%2CAWI%2FPISM1%2CLSCE%2FGRISLI2&exps=exp05&cmap=auto&nan=0" style="display: inline-block; padding: 10px 20px; background-color: #0072B2; color: white; text-decoration: none; border-radius: 4px; font-weight: 500; margin: 10px 0;">Load this comparison</a>

For an accessible introduction to this topic, see Bethan Davie's page on [glacier thermal regimes](https://www.antarcticglaciers.org/glacier-processes/glacier-flow-2/glacial-processes/).

## Grounding line retreat and sub-ice shelf melt

<img src="/static_content/example-floatingmelt.png" alt="Floating basal mass balance comparison screenshot" style="width: 100%; max-width: 50em; height: auto;">

* **Variable:** `libmassbffl` Basal mass balance flux beneath floating ice (kg m-2 s-1)
* **Model:** `DOE/MALI`
* **Experiments:** `exp05`, `exp07`

`libmassbffl` shows the melt rates under floating ice shelves. It's a good way to look at a major component of Antarctic mass loss and also visualize grounding line retreat. Experiments 5 and 7 represent the same assumptions but with different climate forcings. `exp05` is a high-emissions scenario (RCP 8.5) while `exp07` is a low-emission scenario (RCP 2.6).

This is a good comparison to zoom in on, play with the time slider on the left to see how grounding lines evolve over time, and to use the color scale options under "Advanced Options" as needed.

<a href="/app?var=libmassbffl&models=DOE%2FMALI&exps=exp05%2Cexp07&cmap=auto&nan=0" style="display: inline-block; padding: 10px 20px; background-color: #0072B2; color: white; text-decoration: none; border-radius: 4px; font-weight: 500; margin: 10px 0;">Load this comparison</a>

For an accessible introduction to this topic, see Bethan Davie's pages on [grounding lines](https://www.antarcticglaciers.org/glacier-processes/grounding-lines/) and [ice shelves](https://www.antarcticglaciers.org/glaciers-and-climate/changing-antarctica/shrinking-ice-shelves/).

## Surface mass balance

<img src="/static_content/example-smb.png" alt="Surface mass balance comparison screenshot" style="width: 100%; max-width: 50em; height: auto;">

* **Variable:** `acabf` Surface mass balance flux (kg m-2 s-1)
* **Models:** `DOE/MALI`, `AWI/PISM1`
* **Experiments:** `exp05`, `exp07`

Surface mass balance refers to the net accumulation and ablation occurring at the surface of an ice sheet. In most of Antarctica, this primarily means "how much snow is falling?" Antarctica is huge, so small differences in snowfall over big areas can make an enormous difference. Patterns of surface mass balance change over time and vary with the selected climate forcing, so be sure to explore the time slider and look at differences between the low-emission (`exp07`) and high-emisssions (`exp05`) experiments.

<a href="/app?var=acabf&models=DOE%2FMALI%2CAWI%2FPISM1&exps=exp05%2Cexp07&cmap=auto&nan=0" style="display: inline-block; padding: 10px 20px; background-color: #0072B2; color: white; text-decoration: none; border-radius: 4px; font-weight: 500; margin: 10px 0;">Load this comparison</a>

For an accessible introduction to this topic, see Bethan Davie's page on [Antarctic Ice Sheet mass balance](https://www.antarcticglaciers.org/glaciers-and-climate/changing-antarctica/antarctic-ice-sheet-surface-mass-balance/).