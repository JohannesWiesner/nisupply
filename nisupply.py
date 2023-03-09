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
import stat

# TODO: Should be grabbed as .json from pybids to be always conform with upstream
BIDS_ENTITY_REGEX_DICT={'session':('(_ses-)(\d+)',2),
                        'run':('(_run-)(\d+)',2),
                        'data_type':('func|dwi|fmap|anat|meg|eeg|ieeg|beh',0),
                        'echo':('(_echo-)(\d+)',2)}

def find_files(src_dir,file_suffix=None,file_prefix=None,exclude_dirs=None,must_contain=None,case_sensitive=True):
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
        Default: None
    file_prefix: str, tuple of strs
        One or multiple strings on which the beginning of the filepath should match.
        Default: None
    exclude_dirs : str, list of str, None
        Name of single directory or list of directory names that should be ignored when searching for files.
        All of the specified directories and their children directories will be ignored.
        Default: None
    must_contain: list of str
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

    # check if the source directory exists
    if not os.path.isdir(src_dir):
        raise OSError(f"Directory {src_dir} does not exist")

    # convert to appropriate data types
    if isinstance(must_contain,str):
        must_contain = [must_contain]

    filepath_list = []

    # search for files that match the given file extension.
    # if prefix is defined, only append files that match the given prefix
    for (paths, dirs, files) in os.walk(src_dir):

        if exclude_dirs:
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:

            filepath = os.path.join(paths,file)

            if not case_sensitive:
                file = file.lower()

            if file_suffix and not file.endswith(file_suffix):
                continue

            if file_prefix and not file.startswith(file_prefix):
                continue

            if must_contain and not all(element in filepath for element in must_contain):
                continue

            filepath_list.append(filepath)

    # Raise Error if no files where found
    if len(filepath_list) == 0:
        warn(f"No files that match the given criterions where found within {src_dir}")

    return filepath_list

def regex_extract(filepath,pattern,re_group=0):
    ''' Extract a sub-string from a filepath using a regex-match.

    Parameters
    ----------
    filepath : str
        filepath
    pattern : regex-pattern
        DESCRIPTION.
    re_group : int, optional
        If regex-pattern contains capture groups, denotes
        which group should be extracted. The default is 0 which corresponds
        to the whole regex-match

    Returns
    -------
    regex-match, np.nan
    '''

    match = re.search(pattern,filepath)

    if match:
        return match.group(re_group)
    else:
        return np.nan

# FIXME: If scr_dir is list-like, perform sanity check and ensure that
# each participant id is mapped on one and only one source directory (aka.
# both arrays must be the same length), because right now both can have
# different lengths, but no error is thrown meaning that it can happen
# that files or ids simply won't appear
# FIXME: Both particpant_ids and list-like src_dir should be checked for NaNs.
def get_filepath_df(src_dir,subject_ids=None,extract_id=False,id_pattern='(sub-)([a-zA-Z0-9]+)',re_group=2,id_column_name='subject_id',**kwargs):
    '''Find files for multiple participants in one or multiple source directories.

    Parameters
    ----------

    src_dir: list-like of str, str
        One or multiple source directories that should be searched for files

    subject_ids: list-like or None
        A list-like object of subject ids. If src_dir is a list-like object
        and subject_ids is provided, each subject id is mapped on one src dir.

        Default: None

    extract_id: boolean, optional
        If True, extract subject id using id_pattern and re_group from each
        found filepath.
        Default: False

    id_pattern: regex-pattern
        The regex-pattern that is used to extract the participant ID from
        each filepath. By default, this pattern uses a BIDS-compliant regex-pattern.
        Default: '(sub-)([a-zA-Z0-9]+)'

    re_group: int, or None
        If int, match the int-th group of the regex match. If None, just return
        match.group(). Default: 2

    id_column_name: str
        Optional different name for the column that contains the subject ids.
        Default: 'subject_id'

    kwargs: key, value mappings
        Other keyword arguments are passed to :func:`nisupply.find_files`

    Returns
    -------
    filepath_df: pd.DataFrame
        A data frame with at least one column that holds the filepaths to found
        files and and optional second column with subject ids
    '''


    if isinstance(src_dir,str):

        files = find_files(src_dir,**kwargs)
        df = pd.DataFrame({'filepath':files})

        if extract_id == True:
            df[id_column_name] = df['filepath'].apply(regex_extract,pattern=id_pattern,re_group=re_group)

        return df

    else:
        files = [find_files(src_dir,**kwargs) for src_dir in src_dir]

        if extract_id == True:
            files = [file for sublist in files for file in sublist]
            df = pd.DataFrame({'filepath':files})
            df[id_column_name] = df['filepath'].apply(regex_extract,pattern=id_pattern,re_group=re_group)
            return df

        if subject_ids:
            files = dict(zip(subject_ids,files))
            df = pd.DataFrame([(s,f) for s,sublist in files.items() for f in sublist],columns=[id_column_name,'filepath'])
            return df

        files = [file for sublist in files for file in sublist]
        df = pd.DataFrame({'filepath':files})
        return df

# TO-DO: Put this in a separate utils module
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


# FIXME: 't' should start from 1 and not from 0 in order to stick to BIDS convention
# In BIDS, lists start from 1 (e.g. runs also start from 1 and not from 0).
def get_timepoint(filepath_df):
    '''Derive timepoints from session labels. This function assumes that the session
    labels can be sorted alphanumerically and that there is some sort of 'time logic' encoded in the session labels'''

    # create timepoints for session dates
    filepath_df['t'] = filepath_df.sort_values(['participant_id','session_label']).drop_duplicates(['participant_id', 'session_label']).groupby('participant_id').cumcount()
    filepath_df['t'] = filepath_df['t'].fillna(method='ffill').astype(int)

    return filepath_df

def add_bids_info(df,regex_dict=None):
    '''Adds new columns corresponding to standard BIDS-entities to dataframe

    Parameters
    ----------
    df : pd.DataFrame
        A dataframe with a 'filepath' column
    regex_dict : dict of tuples of str and int, optional
        A dictionary where the keys correspond to new columns that should
        be added to the dataframe and the values are tuples where the
        first entry is a regex-pattern and the second entry is an integer
        corresponding to a capture group (set to 0 if you want to match
        the whole regex)

    Returns
    -------
    df : pd.DataFrame
        Input dataframe with added columns.


    '''

    if not regex_dict:
        regex_dict = BIDS_ENTITY_REGEX_DICT

    for entity,regex_info in BIDS_ENTITY_REGEX_DICT.items():
        df[entity] = df['filepath'].apply(regex_extract,args=(regex_info[0],regex_info[1]))
    return df


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
    '''Copy files to destination directories using a source and a target
    column in a pandas Dataframe. Nested target directory structures are
    created along the way.

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
