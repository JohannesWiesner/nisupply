# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 11:11:28 2020

@author: johwi
"""

import numpy as np
import pandas as pd
import os
import gzip
import shutil
import re

# TO-DO: It should also be allowed to not define preceding directories
def find_files(src_dir,file_extension='.nii',file_prefix=None,preceding_dirs='anat'):
    
    # if only one preceding dir provided as string, convert to list
    if isinstance(preceding_dirs,str):
        preceding_dirs = [preceding_dirs]
    
    # change provided scr_dir path to os-specific slash type
    src_dir = os.path.normpath(src_dir)
    
    filepath_list = []
    
    for (paths, dirs, files) in os.walk(src_dir):
        
        # only further examination of file if its path contains one of
        # the given preceding directories
        if any(path_component in paths.split(os.sep) for path_component in preceding_dirs):
            for file in files:
                if file.lower().endswith(file_extension):
                    if file_prefix:
                        if file.lower().startswith(file_prefix):
                            filepath_list.append(os.path.join(paths, file))
                    else:
                        filepath_list.append(os.path.join(paths, file))
    
    return filepath_list

def get_subject_filepaths(subject_ids,subject_folders,file_extension='.nii',
                          file_prefix=None,preceding_dirs='anat'):
    
    filepaths_dict = {}
    
    # walk through each subject folder
    for subject_id,subject_folder in zip(subject_ids,subject_folders):
        	
        subject_filepath_list = find_files(src_dir=subject_folder,
                                           file_extension=file_extension,
                                           file_prefix=file_prefix,
                                           preceding_dirs=preceding_dirs)
                        
        
        filepaths_dict[subject_id] = subject_filepath_list
    
    # create dataframe from dictionary
    filepaths_df = pd.DataFrame([(key, var) for (key, L) in filepaths_dict.items() for var in L],columns=['id', 'filepath'])

    return filepaths_df

# FXME: Makes this function more generic (use function that can uncompress
# files with all kinds of extensions)
# FIXME: Implement this function in get_filepath_df
def uncompress_files(filepath_list,file_extension='.nii'):
    
    filepath_list_uncompressed = []

    # decompress NIFTI Files, but only if there's not alreay an 
    # uncompressed version of the nifti file.
    for f in filepath_list:
        if os.path.exists(f.replace('.nii.gz','.nii')):
            pass
        else:
            with gzip.open(f, 'rb') as f_in:
                # create new name for this file (that is compressed
                # filename without last three letters '.xx')
                with open(f[:-3], 'wb') as f_out:
                    shutil.copyfileobj(f_in,f_out)
        
        filepath_list_uncompressed.append(f)
        
    return filepath_list_uncompressed

def get_session_date(filepath):
    
    pattern = '(ses-)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return np.nan
    else:
        return match.group(2)
    
def get_run_number(filepath):
    
    pattern = '(_run-)(0)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return '1'
    else:
        return match.group(3)
    
# add echo number to 
def get_echo_number(filepath):
    
    pattern = '(_echo-)(0)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return 'no_echo_number'
    else:
        return match.group(3)
    
# get session dates as ascending integer timepoints (starting from 1)
def get_timepoint(filepaths_df):
    
    # create timepoints for session dates
    filepaths_df['t'] = filepaths_df.sort_values(['subject', 'session']).drop_duplicates(['subject', 'session']).groupby('subject').cumcount()
    filepaths_df['t'] = filepaths_df['t'].fillna(method='ffill').astype(int)
    
    return filepaths_df
    
def get_filepath_df(subject_ids,subject_folders,file_extension='.nii',
                  uncompress_files=True,file_prefix=None,preceding_dirs='anat',
                  add_img_date=True,add_run_number=True,add_echo_number=True,add_timepoint=True):
    
    # get dataframe with subject ids and filepaths
    filepath_df = get_subject_filepaths(subject_ids=subject_ids,
                                        subject_folders=subject_folders,
                                        file_extension=file_extension,
                                        file_prefix=file_prefix,
                                        preceding_dirs=preceding_dirs)

    # add further information
    if add_img_date == True:
        filepath_df['img_date'] = filepath_df['filepath'].map(get_session_date)
    
    if add_run_number == True:
        filepath_df['run_number'] = filepath_df['filepath'].map(get_run_number)
    
    if add_echo_number == True:
        filepath_df['echo_number'] = filepath_df['filepath'].map(get_echo_number)
    
    if add_timepoint == True:
        filepath_df = get_timepoint(filepath_df)
    
    return filepath_df

if __name__ == '__main__':
    pass