# nisupply
A python module for dealing with unstructured or semi-structured neuroimaging datasets which do not conform to the [Brain Imaging Data Structure (BIDS)](https://bids.neuroimaging.io/). Although this packages was originall developed for neuroimaging datasets it can work on any file type!

## Installation
Install via pip with: `pip install nisupply`

## Aims
Though more and more datasets become available in the standardized BIDS-format, researchers will still often find themelves in situations, where:

1. The dataset is not BIDS-formatted at all (this is often the case with old 'in-house' datasets that were aquired during a time were BIDS didn't exist yet).

2. The dataset is wrongly BIDS-formatted because it sticks to an outdated BIDS version or because the maintainers made errors (as a consequence, verification tools like the [BIDS-validator](https://bids-standard.github.io/bids-validator/) will throw errors)

3. It is not possible to convert the datasets to BIDS, because you
    1. don't have access to the original DICOM-files
    2. don't have time and ressources to do so
    3. don't have all the information, but the contact to the original maintainer got lost

As a consequence, one cannot use tools from the [BIDS Apps universe](https://bids-apps.neuroimaging.io/apps/) which by default require the files to be BIDS-conform in order to work. The idea behind the nisupply module is to provide helper functions that facilitate the often tedious data-wrangling work that can happen with unstructured data sets.

## Documentation
The nisupply package provides three main modules:

1. `nisupply.io`: for input-output-operations (finding files, copying them over to a different directory)
2. `nisupply.structure`: helper functions to bring the dataset into a new format
3. `nisupply.utils`: helper functions that work on the files themselves (e.g. uncompressing `.nii.gz` to `.nii` as needed for SPM12)

Consider this semistructured dataset as an example:

```
src
├── fmri_nback_subject_3_session_2.nii.gz
├── subject_1
│   ├── fmri_gambling.nii.gz
│   ├── fmri_nback.nii.gz
│   └── session_2
│       └── fmri_nback.nii.gz
├── subject_2_fmri_nback.nii.gz
└── subject_4.txt
```

We can run `nisupply.io.get_filepath_df` on this directory to find all the files that we need and gather the filepaths in a pandas dataframe (that is, search the directory `./src` for files that end with `.nii.gz` and start with `fmri_nback`. Add two new columns `subject_id`
and `task` to it that extract these entities using regular expressions).

```
df = get_filepath_df(src_dir='./src',
                     regex_dict={'subject_id':'subject_(\d)',
                                 'task': 'fmri_(nback|gambling)'},
                     file_suffix='.nii.gz',
                     file_prefix='fmri_nback')
```
This gives you a pandas dataframe that looks like this:

```
                                    filepath subject_id   task
0  src/fmri_nback_subject_3_session_2.nii.gz          3  nback
1            src/subject_1/fmri_nback.nii.gz          1  nback
2  src/subject_1/session_2/fmri_nback.nii.gz          1  nback
```

We can now use `nisupply.structure.get_file_extension` and `nisupply.structure.get_new_filepath` to create a new filepath
for each file:

```
df = get_file_extension(df)
df['dst'] = './dst'
df = get_new_filepath(df,template="{dst}/sub-{subject_id}/sub-{subject_id}_task-{task}{file_extension}")
```

Which outputs:

```
                                    filepath  ...                         filepath_new
0  src/fmri_nback_subject_3_session_2.nii.gz  ...  ./dst/sub-3/sub-3_task-nback.nii.gz
1            src/subject_1/fmri_nback.nii.gz  ...  ./dst/sub-1/sub-1_task-nback.nii.gz
2  src/subject_1/session_2/fmri_nback.nii.gz  ...  ./dst/sub-1/sub-1_task-nback.nii.gz
```

Finally, we can copy over the files using `nisupply.io.copy_files(df,src_col='filepath',tgt_col='filepath_new')` to a new location to obtain a new
tidy dataset:

```
dst/
├── sub-1
│   └── sub-1_task-nback.nii.gz
└── sub-3
    └── sub-3_task-nback.nii.gz
```

## Note
The nisupply module does **not** provide any functions to convert DICOM files to NIFTI files. If you are looking for tools to do that, check out tools like [heudiconv](https://heudiconv.readthedocs.io/en/latest/) or [bidscoin](https://bidscoin.readthedocs.io/en/latest/) that can do that for you.

## Similar Projects
There are similar projects out there following the same idea:
1. Have a look at Stephen Larroque's [pathmatcher](https://github.com/lrq3000/pathmatcher) package which works primarily with regex.
2. The [interfaces.io](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html)  module from `nipype` (especially the [DataFinder](https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.io.html#datafinder) class)

The focus of nisupply is to avoid quite unreadable regex-matches as much as possible. It therefore is best suited for semi-structured datsets that are neither completely unordered but also neither 100% standardized.
