#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input/Output operations (Finding files, copy them to other places, etc.)

@author: johannes.wiesner
"""

import os
import re
from warnings import warn
import numpy as np
import pandas as pd
import shutil

def find_files(src_dir,file_suffix=None,file_prefix=None,
               exclude_dirs=None,must_contain_all=None,must_contain_any=None,
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
        Default: None
    file_prefix: str, tuple of strs
        One or multiple strings on which the beginning of the filepath should match.
        Default: None
    exclude_dirs : str, list of str, None
        Name of single directory or list of directory names that should be ignored when searching for files.
        All of the specified directories and their child directories will be ignored.
        Default: None
    must_contain_all: str, list of str
        Single string or list of strings that must all appear in the filepath
        Default: None
    must_contain_any: str, list of str
        Single string or list of strings where any of those must appear in the filepath
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
    if isinstance(must_contain_all,str):
        must_contain_all = [must_contain_all]
    
    if isinstance(must_contain_any,str):
        must_contain_any = [must_contain_any]

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

            if must_contain_all and not all(element in filepath for element in must_contain_all):
                continue
            
            if must_contain_any and not any(element in filepath for element in must_contain_any):
                continue

            filepath_list.append(filepath)

    # Raise Error if no files where found
    if len(filepath_list) == 0:
        warn(f"No files that match the given criteria where found within {src_dir}")

    return filepath_list

def _regex_extract(filepath,pattern):
    ''' Extract a sub-string from a filepath using a regex-match. If the regex
    pattern contains a capture group the function will return the group and
    not the whole match. If there's no match the function will return np.nan

    Parameters
    ----------
    filepath : str
        filepath.
    pattern : str
        regular expression.
    re_group : int, optional
        If regex-pattern contains capture groups, denotes
        which group should be extracted. The default is 0 which corresponds
        to the whole regex-match

    Returns
    -------
    regex-match, np.nan
    '''

    re_match = re.search(pattern,filepath)

    if re_match:
        # if regex contains a capture group return that group (not the whole match)
        if re_match.groups():
            return re_match.group(1)
        # otherwise return whole match
        else:
            return re_match.group(0)
    else:
        return np.nan

def get_filepath_df(src_dir,regex_dict=None,**kwargs):
    '''Find files in one ore multiple directories. 

    Parameters
    ----------

    src_dir: list-like of str, str
        One or multiple source directories that should be searched for files
    
    regex_dict: dict 
        A dicionary where the keys denote names of new columns that should be
        added to the dataframe and the values denote regex-patterns. If 
        a regex-pattern contains a capture group, the group will be returned,
        otherwise the whole match. If no match could be found np.nan will be
        returned.

    kwargs: key, value mappings
        Other keyword arguments are passed to :func:`nisupply.find_files`

    Returns
    -------
    filepath_df: pd.DataFrame
        A data frame with a 'filepath' column and optionally other columns 
        defined using regular expressions.
    '''


    if isinstance(src_dir,str):
        
        files = find_files(src_dir,**kwargs)
        df = pd.DataFrame({'filepath':files})
    
    elif isinstance(src_dir,list):
        
        dfs = []
        
        for src in src_dir:
            files = find_files(src,**kwargs)
            df = pd.DataFrame({'filepath':files})
            dfs.append(df)
            
        df = pd.concat(dfs,ignore_index=True)
    
    if regex_dict:
        for column,pattern in regex_dict.items():
            df[column] = df['filepath'].apply(lambda filepath: _regex_extract(filepath,pattern))
        
    return df
    
def get_dst_dir(df,src_dir,dst_dir):
    '''Creates a new column 'dst' in the dataframe where the source directory
    gets replaced with the destination directory'''
    
    src_dir = os.path.normpath(src_dir)
    dst_dir = os.path.normpath(dst_dir)
    df['dst'] = df['filepath'].apply(lambda row: os.path.join(dst_dir,row.replace(src_dir,'').lstrip(os.sep)))
    
    return df
    
def copy_files(df,src_col,tgt_col):
    '''Copy files to destination directories using a source and a target
    column in a pandas Dataframe. Nested target directory structures are
    created along the way. Existing files will be overwritten.

    Parameters
    ----------
    df: pd.DataFrame
        A dataframe that holds a column with the source filepaths and one
        column specifying the destination filepaths.

    src: str
        Denotes the column that contains the source filepaths

    tgt: str
        Denotes the column that containes the target filepaths or target
        directories (in latter case, the path must end with a '/').

    '''

    df.apply(lambda row: os.makedirs(os.path.dirname(row[tgt_col]),exist_ok=True),axis=1)
    df.apply(lambda row: shutil.copy2(row[src_col],row[tgt_col]),axis=1)