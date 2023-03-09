#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input/Output operations (Finding files, copy them to other places, etc.)

@author: johannes.wiesner
"""

import os
from warnings import warn
import re
import numpy as np
import pandas as pd

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