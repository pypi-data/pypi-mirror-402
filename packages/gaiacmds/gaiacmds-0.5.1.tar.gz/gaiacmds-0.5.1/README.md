# `gaiacmds` [![DOI](https://zenodo.org/badge/812819707.svg)](https://doi.org/10.5281/zenodo.15866953)
*Good enough* simple membership selection to recover color-magnitude diagrams for use in the classroom!


## Installation
To install:

```bash
cd ~

git clone https://github.com/avapolzin/goodenough_gaia_cmds.git

cd gaiacmds

pip install .

````
or 
```bash
pip install gaiacmds
```

## Getting Started

This lightweight code is designed to auto-generate CMDs from Gaia data based on a simple object name search. While not using a sophisticated selection function suited to *research* purposes, results are good enough for pedagogical use, including explaining SSPs (or CSPs as the case may be), "fitting" isochrones, and recovering age/distance/metallicity for nearby stellar populations.

```python
import gaiacmds

# adopting age and distance from Chen+23: https://ui.adsabs.harvard.edu/abs/2023ApJ...948...59C/abstract
gaiacmds.plot('NGC 3532', 5, isos = 'mist', logage = 8.5, feh = 0.25, dist = 484)
```
<img width="789" height="773" alt="NGC3532" src="https://github.com/user-attachments/assets/c4be5543-ffc7-4d57-83ee-80d2d5e59ed2" />


```python
# adopting isochrone properties and membership cut from Griggio+23: https://ui.adsabs.harvard.edu/abs/2023MNRAS.523.5148G/abstract
gaiacmds.plot('M38', 5, isos = 'mist', logage = 8.5, feh = 0.06, dist = 1130, pmra = 1.5, pmd = -4.5)
```
<img width="783" height="773" alt="M38" src="https://github.com/user-attachments/assets/56b54db0-eff5-40c5-9bd0-014d56a401d5" />


`gaiacmds` ships with easy plotting of MIST and PARSEC stellar isochrones for Gaia EDR3. BaSTI may be added in the future.

Stellar isochrone models will not always perfectly align with the CMD, and, for example, [this paper](https://arxiv.org/abs/2411.12987) may be of interest in understanding discrepancies between the CMD and theoretical isochrone positions. Additionally, for consistency between models, all of the synthetic *Gaia* photometry is for EDR3, and all models use solar abundance patterns.

<!-- Could add DR2 isos from Dartmouth, too: https://rcweb.dartmouth.edu/stellar/grid.html -->

## Documentation (of a sort)

Since the options are so minimal/simple, please refer to the docstring for `gaiacmds.plot()` to understand what options exist. The other functions may be used in isolation, too, though only `gaiacmds.plot()` is intended to be user-facing.

In the future, I may add options to make proper motion or other plots to help guide user choices, though this is the intent of the colormaps and spatial plot that are available at the moment. I may also add the ability to correct for reddening, though that would similarly further complicate what is intended to be a simple pedagogical tool.

## Citation

If you use this package or the scripts in this repository in a publication, please add a footnote linking to https://github.com/avapolzin/goodenough_gaia_cmds and/or consider adding this software to your acknowledgments. If you would like to cite `gaiacmds`, please use the Zenodo DOI linked here.
