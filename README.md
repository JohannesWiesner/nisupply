# nisupply
A python module for dealing with (unstructured) neuroimaging datasets that do not conform to the [Brain Imaging Data Structure (BIDS)](https://bids.neuroimaging.io/).

# Motivation
Some currently available neuroscientific tools produce files and directory structures that do not conform to BIDS. As a consequence, one cannot use tools from the [BIDS Apps universe](https://bids-apps.neuroimaging.io/apps/) which by default require the files to be BIDS-conform in order to work. The idea behind the nisupply module is to provide helper functions that facilitate the transformation of unstructured data sets to BIDS-conform data sets.

# Note
The nisupply module requires all the input files to be in the NIFTI format and does not provide any functions to convert DICOM files to NIFTI files. If you are looking for tools to do that, check out [mne-bids](https://mne.tools/mne-bids/stable/index.html), [heudiconv](https://heudiconv.readthedocs.io/en/latest/) and [bidscoin](https://bidscoin.readthedocs.io/en/latest/) that are useful packages along your way to create BIDS-conform data structures.

# Similar Projects
Have a look at Stephen Larroque's [pathmatcher](https://github.com/lrq3000/pathmatcher) library, it might also suit your needs!