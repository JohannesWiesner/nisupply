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
def find_files(src_dir,file_suffix='.nii.gz',file_prefix=None,preceding_dirs=None,exclude_dirs=None,case_sensitive=True):
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
    exclude_dirs : str, list of str, None
        Name of single directory of list of directory names that should be ignored when searching for files.
        All of the specified directories and their children directories will be
        ignored (Default: None)
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
            
    # search for files that match the given file extension.
    # if prefix is defined, only append files that match the given prefix
    for (paths, dirs, files) in os.walk(src_dir):
        
        if exclude_dirs:
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
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
        warn('No files that match the given filter(s) where found within this directory {}'.format(src_dir))
    
    return filepath_list

def get_participant_id(filepath,pattern='(sub-)([a-zA-Z0-9]+)',regex_group=2):
    '''Extract a participant ID from a filepath using a regex-match'''
    
    match = re.search(pattern,filepath)
    
    if match:
        if regex_group:
            return match.group(regex_group)
        else:
            return match.group()
    else:
        warn(f"Could not extract participant ID from {filepath}")
        return np.nan
    
# FIXME: If scr_dir is list-like, perform sanity check and ensure that
# each participant id is mapped on one and only one source directory (aka.
# both arrays must be the same length). 
# FIXME: Both particpant_ids and list-like src_dir should be checked for NaNs. 
def get_filepath_df(src_dirs,participant_ids=None,id_pattern='(sub-)([a-zA-Z0-9]+)',regex_group=2,**kwargs):
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
    
    regex_group: int, or None
        If int, match the int-th group of the regex match. If none, just return
        match.group(). Default: 2
        
    kwargs: key, value mappings
        Other keyword arguments are passed to :func:`nisupply.find_files`
        
    Returns
    -------
    filepath_df: pd.DataFrame
        A data frame with the provided participant IDs in the first column 
        and all corresponding filepaths in the second column.

    '''
    
    if not isinstance(participant_ids,(str,list,pd.Series)):
        
        if isinstance(src_dirs,str):
            
            filepath_list = find_files(src_dir=src_dirs,**kwargs)
            participant_ids = [get_participant_id(filepath,id_pattern,regex_group) for filepath in filepath_list]
            filepath_df = pd.DataFrame({'participant_id':participant_ids,'filepath':filepath_list})
            
        if isinstance(src_dirs,(list,pd.Series)):
            
            filepath_df = pd.DataFrame()
            
            for src_dir in src_dirs:
            
                filepath_list = find_files(src_dir=src_dir,**kwargs)
                participant_ids = [get_participant_id(filepath,id_pattern,regex_group) for filepath in filepath_list]
                participant_filepath_df = pd.DataFrame({'participant_id':participant_ids,'filepath':filepath_list})
                
                filepath_df = filepath_df.append(participant_filepath_df)
                
    if isinstance(participant_ids,(str,list,pd.Series)):
        
        if isinstance(participant_ids,str):
            participant_ids = [participant_ids]
            
        if isinstance(src_dirs,str):
            
            filepath_dict = {participant_id: [] for participant_id in participant_ids}
            filepath_list = find_files(src_dir=src_dirs,**kwargs)
            
            for filepath in filepath_list:
                
                participant_id = get_participant_id(filepath,id_pattern,regex_group)
                                
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

# FIXME: Allow user to define own regex pattern. The current pattern assumes BIDS-conformity.
# FIXME: if match is None, the function should return a NaN value and raise a warning. 
def get_data_type(filepath):
    
    valid_data_types = ['func','dwi','fmap','anat','meg','eeg','ieeg','beh']
    
    return([data_type for data_type in valid_data_types if (data_type in filepath.split(os.sep))])[0]

# FIXME: Allow user to define own regex pattern. The current pattern assumes BIDS-conformity.
# FIXME: if match is None, the function should return a NaN value and raise a warning
def get_session_label(filepath):
    
    pattern = '(_ses-)(\d+)'
    match = re.search(pattern,filepath)
    
    if match is None:
        return 'no_session_label'
    else:
        return match.group(2)
    
# FIXME: 't' should start from 1 and not from 0 in order to stick to BIDS convention
# In BIDS, lists start from 1 (e.g. runs also start from 1 and not from 0). 
def get_timepoint(filepath_df):
    '''Derive timepoints from session labels. This function assumes that the session 
    labels can be sorted alphanumerically and that there is some sort of 'time logic' encoded in the session labels'''
    
    # create timepoints for session dates
    filepath_df['t'] = filepath_df.sort_values(['participant_id','session_label']).drop_duplicates(['participant_id', 'session_label']).groupby('participant_id').cumcount()
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
def get_bids_df(src_dirs,participant_ids=None,id_pattern='(sub-)([a-zA-Z0-9]+)',regex_group=2,
                add_data_type=True,add_session_label=True,add_timepoint=True,add_run_number=True,
                add_echo_number=True,**kwargs):
    '''Get filepaths for all participants and add BIDS-information using information
    from filepaths. The default extraction of entities and their labels 
    assumes the filepaths to be in BIDS-specification.
    
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
        
    regex_group: int, or None
        If int, match the int-th group of the regex match. If none, just return
        match.group(). Default: 2
        
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
    filepath_df = get_filepath_df(src_dirs=src_dirs,
                                  participant_ids=participant_ids,
                                  id_pattern=id_pattern,
                                  regex_group=regex_group,
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

<<<<<<< HEAD
def extract_entities(recipe):
    '''Extract characters inside curly braces in a tuple of strs. Strings 
    that do not contain curly braces are ignored
    E.g. ["sub-{subject_id}","session-{session}"] becomes ['subject_id','session']
    '''
    
    entities = [re.findall("\{(.*?)\}",entity) for entity in recipe]
    entities = [e for entity in entities for e in entity]
    return entities


def get_bids_structure(df,bids_recipe_dir,bids_recipe_file,dst_dir):
    '''Adds columns for BIDS-conform destination directories, filenames and 
    destination paths to an input dataframe. The columns are created using an 
    overall input destination directory for all files and information from BIDS-columns in the input bids_df.
    
    Parameters
    ----------
    df : pd.DataFrame
        A pandas data frame that has columns that which contain information
        about files. Currently the dataframe MUST contain a column that is
        named 'file_suffix' and contains the file-extension (without the period)
        of each row
    bids_recipe_dir : tuple of str
        A tuple of strs that is used to create a template for a destination directory
        Each string may contain placeholders in curly strings that match to a column 
        name in the data frame. bids_recipe_dir is used to create a template 
        for the destination directory 
    bids_recipe_file : tuple of str
        A tuple of strs that is used to create a template for a destination filename
        Each string may contain placeholders in curly strings that match to a column 
        name in the data frame. bids_recipe_file is used to create a template 
        for the destination filename
    dst_dir: path
        A path to the destination directory where the BIDS-structure should
        be created.

    Returns
    -------
    pd.DataFrame
        The original dataframe with three added columns:
            bids_dir (describes the destination directory)
            bids_file (desribes the destination filename)
            bids_dst (describes the whole path)

    '''

    # extract entities from recipes
    entities_dir = extract_entities(bids_recipe_dir)
    entities_file = extract_entities(bids_recipe_file)

    # create BIDS templates for directories and files
    bids_template_dir = '/'.join(bids_recipe_dir)
    bids_template_file = '_'.join(bids_recipe_file)

    def from_template(row,template):
        return template.format(**row.to_dict())

    df['bids_dir'] = df[entities_dir].apply(lambda row: from_template(row,bids_template_dir),axis=1)
    df['bids_file'] = df[entities_file].apply(lambda row: from_template(row,bids_template_file),axis=1)
    df['bids_dst'] = df.apply(lambda row: os.path.join(dst_dir,row['bids_dir'],row['bids_file']) + '.' + row['file_suffix'],axis=1)

    return df

def copy_files(df,src,tgt):
    '''Copy files to BIDS-conform destination directories.
    
    Parameters
    ----------
    df: pd.DataFrame
        A dataframe that holds a column with the source filepaths and one
        column specifying the destination filepaths.
    
    src: str
        Denotes the column that denotes the source filepath
    
    tgt: str
        Denotes the column that enotes the target filepath
    
    '''
    
    df.apply(lambda row: os.makedirs(os.path.dirname(row[tgt]),exist_ok=True),axis=1)
    df.apply(lambda row: shutil.copy2(row[src],row[tgt]),axis=1)

###############################################################################
## Datalad ####################################################################
###############################################################################

def replace_datalad_symlinks(dataset_path):
    '''Convert the symbolic links in a datalad dataset with the actual files
    themselves. After that, get rid of all the datalad folders (.git, .datalad,
    .gitattrbiutes), leaving only the files themselves. Use case: Windows cannot 
    read the symbolic links from Linux. This function should be used carefully 
    since it (purposely) wbreaks the logic from datalad (which saves the actual 
    files in the annex folder whereas the data structure itself only contains
    directories with symbolic links pointing to the annex)
    
    Parameters
    ----------
    dataset_path : str
        Path to a datalad dataset.

    Returns
    -------
    None.

    '''

    for dirpath, dirnames, filenames in os.walk(dataset_path):
        
        # ignore datalad directories when searching for symbolic links
        dirnames[:] = [d for d in dirnames if d not in ['.datalad','.git']]
        
        for filename in filenames:
            
            # get full filepath
            filepath = os.path.join(dirpath,filename)
    
            # check if file is a symbolic link 
            if os.path.islink(filepath):
                # read link path 
                link_tgt = os.readlink(filepath)
                # delete symbolic link
                os.remove(filepath)
                # copy link target to location of (now deleted) symbolic link
                shutil.move(link_tgt,filepath)
    
    # delete datalad stuff
    shutil.rmtree(os.path.join(dataset_path,'.datalad'))
    os.remove(os.path.join(dataset_path,'.gitattributes'))
    
    # removing the .git directory using shutil.rmtree raises Permission 13 error, 
    # so we use this workaround:
    # https://stackoverflow.com/questions/58878089/how-to-remove-git-repository-in-python-on-windows
    # See also: https://stackoverflow.com/questions/1889597/deleting-read-only-directory-in-python
    for root, dirs, files in os.walk(os.path.join(dataset_path,'.git')):  
        for d in dirs:
            os.chmod(os.path.join(root, d), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
            
    shutil.rmtree(os.path.join(dataset_path,'.git'))



if __name__ == '__main__':
    pass