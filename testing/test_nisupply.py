"""
Create an unordered example dataset and run nisupply on it to check 
if everything works

@author: johannes.wiesner
"""


import os
import shutil
import pathlib
import sys

# in case nisupply is already installed via pip, we want to force the current
# python session to prioritize the local package over the pip-installed one
local_path_nisupply = str(pathlib.Path(__file__).parent.parent)
sys.path.insert(0,local_path_nisupply)

from nisupply.io import get_filepath_df
from nisupply.structure import get_file_extension
from nisupply.structure import get_new_filepath
from nisupply.io import copy_files

###############################################################################
## Create an unordered dataset ################################################
###############################################################################

# start with a clean directory
if os.path.isdir('./src'):
    shutil.rmtree('./src')
if os.path.isdir('./dst'):
    shutil.rmtree('./dst')
    
# create test files with different sizes
os.makedirs('./src')

# specify filenames and directories
files = ['./src/fmri_nback_subject_3_session_2.nii.gz',
          './src/subject_4.txt',
          './src/subject_2_fmri_nback.nii.gz',
          './src/subject_1/fmri_gambling.nii.gz',
          './src/subject_1/fmri_nback.nii.gz',
          './src/subject_1/session_2/fmri_nback.nii.gz',]

# dummy files will be created (each 1MB in size)
for file in files:
    os.makedirs(os.path.dirname(file),exist_ok=True)
    with open(f"{file}", 'wb') as file:
        file.seek(1048575)
        file.write(b'0')

##############################################################################
# Run nisupply ##############################################
##############################################################################

df = get_filepath_df(src_dir='./src',
                     regex_dict={'subject_id':'subject_(\d)',
                                 'task': 'fmri_(nback|gambling)'},
                     file_suffix='.nii.gz',
                     file_prefix='fmri_nback')


# create new filepaths
df = get_file_extension(df)
df['dst'] = './dst'
df = get_new_filepath(df,template="{dst}/sub-{subject_id}/sub-{subject_id}_task-{task}{file_extension}")

# copy files over to new destination
copy_files(df,src_col='filepath',tgt_col='filepath_new')