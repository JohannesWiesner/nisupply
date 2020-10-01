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

def find_files(folder_path,image_extension='.nii',image_prefix=None,modality_dirs='anat'):
    
    if isinstance(modality_dirs,str):
        modality_dirs = [modality_dirs]
    
    folder_path = os.path.normpath(folder_path)
    
    filepath_list = []
    
    for (paths, dirs, files) in os.walk(folder_path):
        if any(path_component in paths.split(os.sep) for path_component in modality_dirs):
            for file in files:
                if file.lower().endswith(image_extension):
                    if image_prefix:
                        if file.lower().startswith(image_prefix):
                            filepath_list.append(os.path.join(paths, file))
                    else:
                        filepath_list.append(os.path.join(paths, file))
    
    return filepath_list

def get_subject_filepaths(subject_ids,subject_folders,
                          image_extension='.nii',image_prefix=None,
                          modality_dirs='anat'):
    
    filepaths_dict = {}
    
    # walk through each subject folder
    for subject_id,subject_folder in zip(subject_ids,subject_folders):
        	
        subject_filepath_list = find_files(folder_path=subject_folder,
                                           image_extension=image_extension,
                                           image_prefix=image_prefix,
                                           modality_dirs=modality_dirs)
                        
        
        filepaths_dict[subject_id] = subject_filepath_list
    
    # create dataframe from dictionary
    filepaths_df = pd.DataFrame([(key, var) for (key, L) in filepaths_dict.items() for var in L],columns=['id', 'filepath'])

    return filepaths_df

# FXME: Makes this function more generic (use function that can uncompress
# files with all kinds of extensions)
# FIXME: Implement this function in get_filepath_df
def uncompress_files(filepath_list,image_extension='.nii'):
    
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
    
def get_timepoint(filepaths_df):
    
    # create timepoints for session dates
    filepaths_df['t'] = filepaths_df.sort_values(['id', 'img_date']).drop_duplicates(['id', 'img_date']).groupby('id').cumcount()
    filepaths_df['t'] = filepaths_df['t'].fillna(method='ffill').astype(int)
    
    return filepaths_df
    
def get_filepath_df(subject_ids,subject_folders,image_extension='.nii',
                  uncompress_files=True,image_prefix=None,modality_dirs='anat',
                  add_img_date=True,add_run_number=True,add_echo_number=True,add_timepoint=True):
    
    # get dataframe with subject ids and filepaths
    filepath_df = get_subject_filepaths(subject_ids=subject_ids,
                                        subject_folders=subject_folders,
                                        image_extension=image_extension,
                                        image_prefix=image_prefix,
                                        modality_dirs=modality_dirs)

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