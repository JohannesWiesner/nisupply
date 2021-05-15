# -*- coding: utf-8 -*-
"""
Nisupply: A repository for finding and managing files in 
(unstructured) neuroimaging datasets.

@author: Johannes.Wiesner
"""


import numpy as np
import pandas as pd
import os
import gzip
import shutil
import re
import pathlib
from warnings import warn

# TO-DO: File extensions should be optional = just return all files you can find
# TO-DO: Searching for a specific order of directories should be included 
# (e.g. search for files that contain '\session_1\anat\)
# For that maybe this stackoverflow post helps: 
# https://stackoverflow.com/questions/5141437/filtering-os-walk-dirs-and-files
# TO-DO: Allow user also to define regex. You might want to use the pathmatcher
# module for that. For example, this is the offical CAT12
# regex that is also used in CAT12 to find .xml files: ^cat_.*\.xml$
# Using regex instead (or in combination) with/of file_prefix + file_extension 
# might be more 'fail-safe' to find exactly the files, that the user is looking for
def find_files(src_dir,file_suffix='.nii.gz',file_prefix=None,preceding_dirs=None,
                case_sensitive=True):
    '''Find files in a single source directory. Files are found based on a 
    specified file suffix. Optionally, the function can filter for files
    using an optional file prefix and a list of preceding directories that must be 
    part of the filepath.
    
    Parameters
    ----------
    src_dir: path
        A directory that should be searched for files.
    
    file_suffix: str, tuple of strs
        One or multiple strings on which the end of the filepath should match.
        Default: '.nii.gz'
    
    file_prefix: str, tuple of strs
        One or multiple strings on which the beginning of the filepath should match.
        Default: None
    
    preceding_dirs: str, list of strs or None
        Single name of a directory or list of directories that must be 
        components of each filepath
        Default: None
    
    case_sensitive: Boolean
        If True, matching is done by the literal input of file suffixes and
        prefixes and files. If False, both the inputs and the files are converted
        to lowercase first in order to match on characters only regardless of lower-
        or uppercase-writing. 
        
    Returns
    -------
    filepath_list: list
        A list containing filepaths for the found files.

    '''
    
    # change provided scr_dir path to os-specific slash type
    src_dir = os.path.normpath(src_dir)
    
    filepath_list = []
    
    if not case_sensitive:
        file_suffix = file_suffix.lower()
        file_prefix = file_prefix.lower()
        
    # search for files that match the given file extension.
    # if prefix is defined, only append files that match the given prefix
    for (paths, dirs, files) in os.walk(src_dir):
        for file in files:
            if not case_sensitive:
                file = file.lower()
            if file.endswith(file_suffix):
                if file_prefix:
                    if file.startswith(file_prefix):
                        filepath_list.append(os.path.join(paths,file))
                else:
                    filepath_list.append(os.path.join(paths,file))
                    
    # Filter list of found files by deleting filepaths from list whose path 
    # components do not match any of the given preceding directories
    if preceding_dirs:
        
        # if only one preceding_dirs is provided as string, convert to list
        # of single string
        if isinstance(preceding_dirs,str):
            preceding_dirs = [preceding_dirs]
    
        tagged_files_indices = []
        
        for idx,filepath in enumerate(filepath_list):
            if not any(path_component in filepath.split(os.sep) for path_component in preceding_dirs):
                tagged_files_indices.append(idx)
                
        for idx in sorted(tagged_files_indices,reverse=True):
            del filepath_list[idx]
    
    # Raise Error if no files where found
    if len(filepath_list) == 0:
        raise ValueError('No files that match the given filter(s) where found within this directory {}'.format(src_dir))
    
    return filepath_list

def get_participant_id(filepath,pattern='(sub-)([a-zA-Z0-9]+)'):
    '''Extract a participant ID from a filepath using a regex-match'''
    
    match = re.search(pattern,filepath)
    
    if match:
        return match.group()
    else:
        warn(f"Could not extract participant ID from {filepath}")
        return np.nan
    
# FIXME: If scr_dir is list-like, perform sanity check and ensure that
# each participant id is mapped on one and only one source directory (aka.
# both arrays must be the same length). 
# FIXME: Both particpant_ids and list-like src_dir should be checked for NaNs. 
def get_filepath_df(src_dirs,participant_ids=None,id_pattern='(sub-)([a-zA-Z0-9]+)',**kwargs):
    '''Find files for multiple participants in one or multiple source directories. 
    
    Parameters
    ----------

    src_dirs: list-like of str, str

        If provided without participant IDS, the function will map each found file
        to a participant ID using the given regex pattern. 

        If a list of directories is provided together with a list of participant
        IDs, it is assumed that each directory only contains files for that 
        particular participant, thus the files are mapped to the respective 
        participant ID without a regex match.
        
        If provided as a single directory together with a list of participant
        IDs, it is assumed that all files of the participants are in the same directory.
        The function will then map each found file to one of the given participant IDs using a 
        specified regex pattern.
        
    
    participant_ids: list-like, None
        A list-like object of unique participant IDs or None
        Default: None
        
    id_pattern: regex-pattern 
        The regex-pattern that is used to extract the participant ID from
        each filepath. By default, this pattern uses a BIDS-compliant regex-pattern. 
        Default: '(sub-)([a-zA-Z0-9]+)'
        
    kwargs: key, value mappings
        Other keyword arguments are passed to :func:`nisupply.find_files`
        
    Returns
    -------
    filepath_df: pd.DataFrame
        A data frame with the provided participant IDs in the first column 
        and all corresponding filepaths in the second column.

    '''
    
    if not participant_ids:
        
        if isinstance(src_dirs,str):
            
            filepath_list = find_files(src_dir=src_dirs,**kwargs)
            participant_ids = [get_participant_id(filepath,id_pattern) for filepath in filepath_list]
            filepath_df = pd.DataFrame({'participant_id':participant_ids,
                                        'filepath':filepath_list})
            
        if isinstance(src_dirs,(list,pd.Series)):
            
            filepath_df = pd.DataFrame()
            
            for src_dir in src_dirs:
            
                filepath_list = find_files(src_dir=src_dir,**kwargs)
                participant_ids = [get_participant_id(filepath,id_pattern) for filepath in filepath_list]
                participant_filepath_df = pd.DataFrame({'participant_id':participant_ids,
                                                        'filepath':filepath_list})
                
                filepath_df = filepath_df.append(participant_filepath_df)
                
    if participant_ids:
        
        if isinstance(participant_ids,str):
            participant_ids = [participant_ids]
            
        if isinstance(src_dirs,str):
            
            filepath_dict = {participant_id: [] for participant_id in participant_ids}
            filepath_list = find_files(src_dir=src_dirs,**kwargs)
            
            for filepath in filepath_list:
                
                participant_id = get_participant_id(filepath,id_pattern)
                                
                try:
                    filepath_dict[participant_id].append(filepath)
                    
                except KeyError:
                    warn(f"No matching ID in provided IDs found for this extracted ID: {participant_id}")
    
        if isinstance(src_dirs,(list,pd.Series)):
            
            if not len(src_dirs) == len(participant_ids):
                raise ValueError('Participant IDs and source directories must be of the same length')
            
            filepath_dict = {}
            
            for participant_id,participant_dir in zip(participant_ids,src_dirs):
                filepath_list = find_files(src_dir=participant_dir,**kwargs)
                filepath_dict[participant_id] = filepath_list
    
    
        filepath_df = pd.DataFrame.from_dict(filepath_dict,orient='index')
        filepath_df = filepath_df.stack().to_frame().reset_index().drop('level_1', axis=1)
        filepath_df.columns = ['participant_id', 'filepath']
    
    return filepath_df

# TO-DO: Implement this function in get_bids_df
def uncompress_files(filepath_list,dst_dir=None):
    '''Uncompress files and obtain a list of the uncompressed files.
    
    Parameters
    ----------
    filepath_list : list of str
        A list of paths of the the compressed files. The function
        assumes that the filename has exactly two extensions: The first
        extension represents the native extension of the file, the second extension 
        represents the compression extension (i.e. 'nii.gz').
    
    dst_dir: str
        A path to a destination directory. If None, uncompressed files are 
        saved in the source directory of each file. If specified, uncompressed
        files will be saved in the specified destination directory.

    Returns
    -------
    filepath_list_uncompressed : list
        A list of paths pointing to the uncompressed files

    '''

    filepath_list_uncompressed = []
    
    for f in filepath_list:
        
        # get all necessary extensions
        file_extensions = pathlib.Path(f).suffixes
        file_extension = file_extensions[0]
        both_extensions = ''.join(file_extensions)
    
        filepath_uncompressed = f.replace(both_extensions,file_extension)
        
        if dst_dir:
            dst_dir = os.path.normpath(dst_dir)
            uncompressed_filename = os.path.basename(filepath_uncompressed)
            filepath_uncompressed = os.path.join(dst_dir,uncompressed_filename)
        
        # if compressed file already exists do nothing
        if os.path.exists(filepath_uncompressed):
            pass
        # uncompress file and save it without the compression extension
        # in either the same folder or, if specfied in a destination directory
        else:
            with gzip.open(f,'rb') as f_in:
                with open(filepath_uncompressed,'wb') as f_out:
                    shutil.copyfileobj(f_in,f_out)
            
        filepath_list_uncompressed.append(filepath_uncompressed)
            
    return 

def get_data_type(filepath):
    
    valid_data_types = ['func','dwi','fmap','anat','meg','eeg','ieeg','beh']
    
    return([data_type for data_type in valid_data_types if (data_type in filepath.split(os.sep))])[0]

# FIXME: Allow user to define own regex pattern. The current pattern assumes BIDS-conformity.
# FIXME: if match is None, the function should return a NaN value. 
def get_session_label(filepath):
    
    pattern = '(_ses-)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return 'no_session_label'
    else:
        return match.group(2)
    
# Derive integer timepoints from session labels
# NOTE: this function assumes that the session labels can be sorted alphanumerically and
# that there is some sort of 'time logic' encoded in the session labels
# FIXME: 't' should start from 1 and not from 0 in order to stick to BIDS convention
# In BIDS, lists start from 1 (e.g. runs also start from 1 and not from 0). 
def get_timepoint(filepath_df):
    
    # create timepoints for session dates
    filepath_df['t'] = filepath_df.sort_values(['participant_id', 'session_label']).drop_duplicates(['participant_id', 'session_label']).groupby('participant_id').cumcount()
    filepath_df['t'] = filepath_df['t'].fillna(method='ffill').astype(int)
    
    return filepath_df

# FIXME: Allow user to define own regex pattern. The current pattern assumes BIDS-conformity.
# FIXME: if match is None, the function should return a NaN value. 
def get_run_number(filepath):
    
    pattern = '(_run-)(0)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return 'no_run_number'
    else:
        return match.group(3)

# FIXME: Allow user to define own regex pattern. The current pattern assumes BIDS-conformity.
# FIXME: if match is None, the function should return a NaN value. 
def get_echo_number(filepath):
    
    pattern = '(_echo-)(0)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return 'no_echo_number'
    else:
        return match.group(3)

# TO-DO: Implement boolean keyword argument 'bids_conformity' (True/False)'. 
# -> Running add_data_type, add_session_label, etc. only makes sense if the filepaths 
# themselves are BIDS-conform.
# IDEA: If participants_ids is provided together with list-like src_dir, it should
# also be possible to just pass a pd.DataFrame to this function? 
# TO-DO: The regex patterns for the 'bids-entity-extraction' functions like get_echo_number,
# get run_number, etc. should be based on the offical .json file from pybids. As a consequence,
# this function should always have the newest .json file available. 
# FIXME: In case the dataset is bids_conform it would be more handy to just
# rely on the input keyword-argument bids_conformity (see above) and then just
# automatically run all extraction-functions (add_data_type,add_session_label,etc.)
# If the user only wants to extract certain entities, a input dictionary of
# booleans should be passed (e.g. {'data_type':True,'echo_number':False})
def get_bids_df(participant_ids,src_dir,add_data_type=True,add_session_label=True,
                add_timepoint=True,add_run_number=True,add_echo_number=True,**kwargs):
    '''Get filepaths for all participants and add BIDS-information using information
    from filepaths. The following extraction of entities and their labels 
    requires the filepaths to follow BIDS-specification.
    
    Parameters
    ----------
    participant_ids: list
        A list of unique participant IDs.
        
    src_dir: str, or list of str
        If provided as a single directory, it is assumed that all files of the
        participants are in the same directory. It is assumed that each filename
        contains a BIDS-conform subject id. In consequence, the function will match files and 
        participant_ids using a regex match.
        
        If a list of directories is provided, it is assumed that each directory 
        only contains files for that particular participant, thus the files
        are mapped to the respective participant id without a regex match.
        
    add_data_type : bool, optional
        Extract the data type from the filepath. The default is False.
    
    add_session_label : bool, optional
        Extract the session label from the filepath. The default is False.
    
    add_timepoint : bool, optional
        Add the timepoint based on the session label. It is assumed
        that session label follows alphanumeric convention. The default is False.
        
    add_run_number : bool, optional
        Extract the run number from the filepath. The default is False.
        
    add_echo_number : TYPE, optional
        Extract the echo number from the filepath. The default is False.
        
    **kwargs : key,value mappings
        Other keyword arguments are passed to :func:`nisupply.find_files`.

    Returns
    -------
   bids_df : pd.DataFrame
        A dataframe that contains columns containing BIDS-conform information.

    '''
    
    # get dataframe with participant ids and filepaths
    filepath_df = get_filepath_df(participant_ids=participant_ids,
                                  src_dir=src_dir,
                                  **kwargs)

    if add_data_type == True:
        filepath_df['data_type'] = filepath_df['filepath'].map(get_data_type)
        
    if add_session_label == True:
        filepath_df['session_label'] = filepath_df['filepath'].map(get_session_label)
    
    if add_timepoint == True:
        if add_session_label != True:
            raise ValueError('In order to add timepoint, you must set add_session_label == True')
            
        filepath_df = get_timepoint(filepath_df)
    
    if add_run_number == True:
        filepath_df['run_number'] = filepath_df['filepath'].map(get_run_number)
    
    if add_echo_number == True:
        filepath_df['echo_number'] = filepath_df['filepath'].map(get_echo_number)
    
    return filepath_df

def add_bids_dst_dirs(dst_dir,bids_df):
    '''Adds a column of BIDS-conform destination directories for each file.
    The destination directories will be build using an overall input destination 
    directory for all files and information from BIDS-columns in the input bids_df.
    
    Parameters
    ----------
    dst_dir: path
        A path to the destination directory where the BIDS-structure should
        be created.
        
    bids_df: pd.DataFrame
        A dataframe as returned by :func:`nisupply.get_bids_df`
        
    Returns
    -------
    bids_df: pd.DataFrame
        bids_df with an additional column 'bids_dst_dir'.

    '''
    dst_dir = os.path.normpath(dst_dir)
    bids_df['bids_dst_dir'] =  bids_df.apply(lambda row: os.path.join(dst_dir,'sub-'+ row['participant_id'],row['session_label'],row['data_type']),axis=1)
    
    return bids_df

def create_bids_dst_dirs(bids_df):
    '''Create BIDS-conform directory structure 
    
    Parameters
    ----------
    bids_df: pd.DataFrame
        A data frame that contains a column 'bids_dirs' that contains
        BIDS-conform directory paths which will be created.
        
    Returns
    -------
    None.

    '''
    
    for bids_dir in bids_df['bids_dst_dir']:
        if not os.path.isdir(bids_dir):
            os.makedirs(bids_dir)

# FIXME: DEPRECATED
def copy_files_to_bids_dst_dirs(filepath_df,bids_df):
    '''Copy files to BIDS-conform destination directories.
    
    Parameters
    ----------
    filepath_df: A dataframe containing a column 'participant_id' and a column
    'filepath' that points to the file which should be copied.
    
    bids_df: A dataframe containg a column 'participant_id' and a column
    'bids_dir' that points to a directory where the file should be copied to.
    
    Returns
    ------
    
    
    '''

    bids_df_src_filepaths = pd.merge(bids_df,filepath_df,on='participant_id')
    
    for idx,row in bids_df_src_filepaths.iterrows():
        shutil.copy2(row['filepath'],row['bids_dst_dir'])

if __name__ == '__main__':
    pass