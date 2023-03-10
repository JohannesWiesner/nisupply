# nisupply
A python module for dealing with unstructured or semi-structured neuroimaging datasets which do not conform to the [Brain Imaging Data Structure (BIDS)](https://bids.neuroimaging.io/).

## Installation
Install via pip with: `pip install nisupply`

## Aims
Though more and more datasets become available in the standardized BIDS-format, researchers will still often find themelves in situations, were:
1. The dataset is not BIDS-formatted at all (this is often the case with old 'in-house' datasets that were aquired during a time were BIDS didn't exist yet).
2. It is not possible to convert the datasets to BIDS, because you
    1.) Don't have access to the original DICOM-files
    2.) Not the time and ressources to do so
    3.) Lack information, but the maintainer has left your research department
3. The dataset is wrongly BIDS-formatted because it sticks to an outdated BIDS version or because the maintainers made errors (as a consequence, verification tools like the [BIDS-validator](https://bids-standard.github.io/bids-validator/) will throw errors)

 As a consequence, one cannot use tools from the [BIDS Apps universe](https://bids-apps.neuroimaging.io/apps/) which by default require the files to be BIDS-conform in order to work. The idea behind the nisupply module is to provide helper functions that facilitate the often tedious data-wrangling work that can happen with unstructured data sets.

 ## Docs
The nisupply package provides three main modules:
1. `nisupply.io` for input-output-operations (finding files, renaming them, copying them over to a different directory). The main function within this module is the `nisupply.io.get_filepath_df` function.
2. `nisupply.bids` (helper functions to create a BIDS-like data structures. Note, that without having the original DICOM files one will never be able to create 100% valid BIDS-datasets with this module)
3. `nisupply.utils` (unarchiving files which is needed for neuroimaging software like SPM and other functions that do not fit to the first two modules)

## Note
The nisupply module does **not** provide any functions to convert DICOM files to NIFTI files. If you are looking for tools to do that, check out tools like [heudiconv](https://heudiconv.readthedocs.io/en/latest/) or [bidscoin](https://bidscoin.readthedocs.io/en/latest/) that can do that for you.

## Similar Projects
There are similar projects out there following the same idea:
1. Have a look at Stephen Larroque's [pathmatcher](https://github.com/lrq3000/pathmatcher) package which works primarily with regex.
2. The [interfaces.io](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html)  module from `nipype` (especially the [DataFinder](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html#datafinder) class)

The focus of nisupply is to avoid quite unreadable regex-matches as much as possible. It therefore is best suited for semi-structured datsets that are neither completely unordered but also 100% standardized.
