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

from nisupply.io import get_filepath_df

df = get_filepath_df(src_dir='./src',
                      extract_id=True,
                      id_pattern='subject_\d+',
                      re_group=0,
                      id_column_name='participant',
                      file_suffix='.nii.gz',
                      file_prefix='fmri_nback',
                      must_contain_all='session_2',
                      must_contain_any='subject_3')
