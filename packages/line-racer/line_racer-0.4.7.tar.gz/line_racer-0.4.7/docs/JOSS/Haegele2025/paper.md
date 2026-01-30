---
title: 'line racer: Rapid Calculation of Exoplanetary Radiative Opacities'
tags:
  - Python
  - astronomy
  - exoplanets
  - brown dwarfs
  - atmospheres
  - opacities
  - spectroscopy
languages:
  - Python
  - Fortran
authors:
  - name: David Hägele
    orcid: 0009-0009-7667-7003
    corresponding: true
    affiliation: "1, 2"  # (Multiple affiliations must be quoted)
  - name: Paul Mollière
    orcid: 0000-0003-4096-7067
    affiliation: 1
affiliations:
 - name: Max Planck Institut für Astronomie, Königstuhl 17 D-69117 Heidelberg, Germany
   index: 1
 - name: Ruprecht-Karls-Universität Heidelberg, Fakultät für Physik und Astronomie, Im Neuenheimer Feld 226, 69120 Heidelberg, Germany
   index: 2
   
submitted_at: '2026-01-19'
software_repository_url: "https://gitlab.com/David_Haegele/line_racer"
bibliography: paper.bib

# Optional fields if submitting to an AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
# aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary
`line racer` is a Python package intended to tackle the challenge of computing high-resolution opacities from large molecular and atomic line lists in an effective manner.
It offers users a wide range of options to customize opacity calculations to their needs and available hardware. 
The code is designed for efficient parallelization on multi-core and multi-node systems and can produce outputs compatible with popular atmospheric modeling and retrieval tools.


# Statement of need
With the expected revolution in high-resolution spectroscopy of exoplanet and brown dwarf atmospheres in the coming years, highly accurate knowledge of the opacities of various molecular and atomic species is crucial.
The opacities are computed from line lists, which contain the information about the transitions between different energy levels of the molecules and atoms. 


As a result, the line lists, are growing rapidly in size and databases like ExoMol [@Tennyson2024] now have line lists for multiple molecules with billions of lines. 
For example, the latest ExoMol methane line list MM [@Yurchenko2024] contains 50 billion lines.
Therefore, it is challenging to compute the opacities accurately from these line lists in a reasonable time. 
`line racer` is explicitly designed to calculate high-resolution opacities from large line lists in a very efficient manner.
To achieve this, it uses a combination of two different algorithms for the line calculation:

1. A line profile calculation based on the algorithm by @Humlicek1982 with a speedup proposed by @Molliere2015.
2. A sampling technique of the line profiles based on the algorithm proposed by @Min2017.

This combination allows for a very fast calculation while maintaining a high accuracy. 
Compared to existing tools, `line racer` has a calculation time per line that is dependent on the importance of the line, which is a significant advantage for the largest line lists.
Moreover, it is automatically parallelized to be used on multiple nodes and cores, dependent on the user's needs and available hardware.

Due to the increasing resolution of observations, it is also becoming relevant how exactly the line profiles are treated in the opacity calculations. 
In particular, the line wings treatment can have a significant impact on the resulting opacities at high resolution. 
Therefore, `line racer` includes different options for the line wing treatment, such as a simple cutoff at a user-specified distance from the line center or a sub-Lorentzian treatment following @Hartmann2002.

The opacities calculated with `line racer` can be used for various applications in the field of exoplanet and brown dwarf atmospheres.
To be directly compatible with one of the most used atmospheric modeling and retrieval codes, `line racer` can output the opacities in petitRADTRANS [@Molliere2019] format in addition to a simple standard format.

# Line profile calculation
As already mentioned, the line profile calculation in `line racer` is split up into two different algorithms. The decision of which algorithm to use for the lines is based on their strength and the size of the line list.

For the strongest lines of a large line list, or for small line lists, the line profiles are calculated with the Humlicek algorithm [@Humlicek1982] combined with a speed-up proposed by @Molliere2015.
The speedup is achieved by calculating the line wings on a coarser grid and interpolating them to the fine grid.

The weaker lines of large line lists are calculated with a modified version of the line profile sampling technique proposed by @Min2017.
This technique is not calculating the line profiles on every grid point but instead samples them to a precision that is determined by the importance of the line. 
For example, if the line is only contributing to the continuum background of the opacity, it is sampled with just a few or one sample to reproduce the overall opacity, but minimizing the calculation time.

The sampling technique of Voigt profiles is based on the idea of sampling the individual distributions of the convolution separately for each sample. 
To get the location of their contribution to the overall opacity, they are added to the line center.
The amount of contribution is determined by a weight that is distributed over an interval defined by the pressure broadening sample $\Delta\nu_\mathrm{press}$.
@Min2017 defined a weight $w$ that reproduces the shape of the line but requires a normalization after the line profile is constructed.
The normalization afterward is very time-consuming, which is why we introduced a new form of this weight that already preserves the integrated intensity of the line directly.

$$
w = \frac{2\Delta\nu_\mathrm{press}^2}{\Delta\nu_\mathrm{press}^2 + \gamma^2}\frac{S}{\mathrm{N_{samples}}}\frac{R}{\nu_\mathrm{eff}}
$$

The first term is adapted from @Min2017 to preserve the shape of the line and includes the pressure broadening width of the line $\gamma$. 
The other terms represent the contribution of the number of samples $\mathrm{N_{samples}}$, the intensity $S$, the resolution $R$, and the effective wavenumber $\nu_\mathrm{eff}$ of the line.

The direct normalization is introducing a small uncertainty in the integrated intensity because the weight and therefore the contribution are dependent on the random samples. 
But since it scales inversely with the number of lines and samples and the technique is only used for huge line lists, it is negligible.

In addition to the improved weight, we also enhanced the number of samples for each line, enabling a better performance overall and especially for the low-pressure cases.
More about that can be found in the documentation of the code, together with benchmark results and timing information. 

We note that there are other tools to compute opacities for exoplanet atmospheres, such as [`HELIOS-K`](https://helios-k2.readthedocs.io/en/latest/) [@Grimm2021], [`Cthulhu`](https://cthulhu.readthedocs.io/en/latest/) [@Agrawal2024], [`ExoCross`](https://exocross.readthedocs.io/en/latest/) [@Yurchenko2018], and [`pyROX`](https://py-rox.readthedocs.io/en/latest/) [@deRegt2025].

# Acknowledgements
We thank M. Min for helpful discussions about the sampling technique of the line profiles.
Additionally, we thank Jerry Xuan for testing the early versions of this code and providing valuable feedback to the code and the documentation.

# References


