# AOPERA

**A**daptive
**O**ptics
**P**sf
**E**stimation and
**R**esiduals
**A**nalysis

This package runs fast computation of adaptive optics (SCAO) residuals.
It provides the following outputs:
* PSD of the electromagnetic phase (in rad2.m2) for each AO error term,
* AO error budget (integral of the PSD),
* long exposure PSF at any wavelengths,
* short exposure PSF at any wavelengths,
* fiber coupling efficiency.

AOPERA is particularly designed to manage Fourier Filtering wavefront sensors, such as the pyramid (but any FF-WFS can be implemented), in single conjugated AO (SCAO) mode.
The code deals with the sensitivity of FF-WFS and manages non-linearities through the convolutive formalism (Fauvarque PhD thesis).

AOPERA is compatible with TIPTOP ini files in SCAO mode.

### Repository

Access to the online git repository:

[https://gitlab.lam.fr/lam-grd-public/aopera](https://gitlab.lam.fr/lam-grd-public/aopera)

### Documentation

Access to online documentation on how to install the package, scientific notice on the code and test reports:

[https://gitlab.lam.fr/lam-grd-public/aopera/-/wikis/home](https://gitlab.lam.fr/lam-grd-public/aopera/-/wikis/home)

### References

[Fetick, Chambouleyron, Heritier, 2023, AO4ELT-7 proceedings](https://hal.science/hal-04402859/)

### Authors

Romain Fétick

Vincent Chambouleyron

Arnaud Striffling
