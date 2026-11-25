#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input/Output operations (Finding files, copy them to other places, etc.)

@author: johannes.wiesner
"""

import os
import subprocess
import tempfile
from pathlib import Path
import re
from warnings import warn
import numpy as np
import pandas as pd
import shutil

def find_files(src_dir,file_suffix=None,file_prefix=None,
               exclude_dirs=None,must_contain_all=None,must_contain_any=None,
               must_not_contain_all=None,must_not_contain_any=None,case_sensitive=True,
               regex_match=None,filename_regex=None,exclude_nested_dirs=None):
    '''Find files in a single source directory. Files are found based on a
    specified file suffix. Optionally, the function can filter for files
    using an optional file prefix and a list of preceding directories that must be
    part of the filepath.

    Parameters
    ----------
    src_dir: path
        A directory that should be searched for files.
        
    regex_match, filename_regex : str, optional
        Regex searches on the full path and basename, respectively.
    exclude_nested_dirs : str or list of str, optional
        Prune directories matching a sequence of adjacent directory names.

    file_suffix: str, tuple of strs
        One or multiple strings on which the end of the filepath should match.
        Default: None
        
    file_prefix: str, tuple of strs
        One or multiple strings on which the beginning of the filepath should match.
        Default: None
        
    exclude_dirs : str, list of str, None
        Name of single directory or list of directory names that should be ignored when searching for files.
        All of the specified directories and their child directories will be ignored. Note that
        this can significantly speed up the search because it prevents the function to walk through directories
        of no interest.
        Default: None
        
    must_contain_all: str, list of str
        Single string or list of strings that must all appear in the filepath
        Default: None
        
    must_contain_any: str, list of str
        Single string or list of strings where any of those must appear in the filepath
        Default: None
        
    must_not_contain_all: str, list of str
        Single string or list of strings. The filepath will be excluded if 
        it contains all of those strings.
        Default: None
        
    must_not_contain_any: str, list of str
        Single string or list of strings. The filepath will be excluded if
        it contains any of those strings.
        Default: None
        
    case_sensitive: Boolean
        If False, all files will be converted to lower-case letters first before
        applying search conditions.
        Default: True

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
        
    if isinstance(must_not_contain_all,str): 
        must_not_contain_all = [must_not_contain_all] 
     
    if isinstance(must_not_contain_any,str): 
        must_not_contain_any = [must_not_contain_any] 

    flags = 0 if case_sensitive else re.IGNORECASE
    path_pattern = re.compile(regex_match, flags) if regex_match is not None else None
    name_pattern = re.compile(filename_regex, flags) if filename_regex is not None else None
    if isinstance(exclude_dirs, str):
        exclude_dirs = [exclude_dirs]
    if isinstance(exclude_nested_dirs, (str, os.PathLike)):
        exclude_nested_dirs = [exclude_nested_dirs]
    excluded = [Path(seq).parts for seq in exclude_nested_dirs or ()]

    filepath_list = []

    # check if filepath against the given criteria and append it to list
    # if it passes all checks
    for (paths, dirs, files) in os.walk(src_dir):

        if exclude_dirs:
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

        if excluded:
            parent = Path(paths).parts
            dirs[:] = [d for d in dirs if not any(
                (parent + (d,))[-len(seq):] == seq for seq in excluded
            )]

        for file in files:

            filepath = os.path.join(paths,file)

            if path_pattern and not path_pattern.search(filepath):
                continue
            if name_pattern and not name_pattern.search(file):
                continue
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
            
            if must_not_contain_all and all(element in filepath for element in must_not_contain_all):
                continue
            
            if must_not_contain_any and any(element in filepath for element in must_not_contain_any):
                continue
            
            filepath_list.append(filepath)

    # Raise warning if no files were found
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

def _scan(roots, working_directory, filters):
    # The working directory distinguishes relative roots in persistent caches.
    return [path for root in roots for path in find_files(root, **filters)]


def get_filepath_df(src_dir,regex_dict=None,cache=False,**kwargs):
    '''Find files in one ore multiple directories. 

    Parameters
    ----------

    src_dir: list-like of str, str
        One or multiple source directories that should be searched for files
        
    cache : bool or path, optional
        Cache searches in a trusted directory. True selects ~/.cache/nisupply.
        Clear the cache after changing the dataset. False performs a fresh scan.
    regex_dict: dict 
        A dicionary where the keys denote names of new columns that should be
        added to the dataframe and the values denote regex-patterns. If 
        a regex-pattern contains capture groups, the first group will be returned,
        otherwise the whole match. If no match could be found np.nan will be
        returned.
        Default: None
        
    regex_match, filename_regex : str, optional
        Regex searches on the full path and basename, respectively.
    exclude_nested_dirs : str or list of str, optional
        Prune directories matching a sequence of adjacent directory names.

    file_suffix: str, tuple of strs
        One or multiple strings on which the end of the filepath should match.
        Default: None
        
    file_prefix: str, tuple of strs
        One or multiple strings on which the beginning of the filepath should match.
        Default: None
        
    exclude_dirs : str, list of str, None
        Name of single directory or list of directory names that should be ignored when searching for files.
        All of the specified directories and their child directories will be ignored. Note that
        this can significantly speed up the search because it prevents the function to walk through directories
        of no interest.
        Default: None
        
    must_contain_all: str, list of str
        Single string or list of strings that must all appear in the filepath
        Default: None
        
    must_contain_any: str, list of str
        Single string or list of strings where any of those must appear in the filepath
        Default: None
        
    must_not_contain_all: str, list of str
        Single string or list of strings. The filepath will be excluded if 
        it contains all of those strings.
        Default: None
        
    must_not_contain_any: str, list of str
        Single string or list of strings. The filepath will be excluded if
        it contains any of those strings.
        Default: None
        
    case_sensitive: Boolean
        If False, all files will be converted to lower-case letters first before
        applying search conditions.
        Default: True

    Returns
    -------
    filepath_df: pd.DataFrame
        A data frame with a 'filepath' column and optionally other columns 
        defined using regular expressions.
    '''
    
    roots = [src_dir] if isinstance(src_dir, (str, os.PathLike)) else src_dir
    roots = tuple(os.fspath(root) for root in roots)
    scan = _scan
    if cache:
        from joblib import Memory
        location = Path.home() / ".cache" / "nisupply" if cache is True else cache
        scan = Memory(location, verbose=0).cache(_scan)
    df = pd.DataFrame({"filepath": scan(roots, os.getcwd(), kwargs)})

    if regex_dict:
        for column,pattern in regex_dict.items():
            df[column] = df['filepath'].apply(lambda filepath: _regex_extract(filepath,pattern))
        
    return df
        
def copy_files(df, src_col, tgt_col, skip_existing=False, verify=False):
    """Copy files, optionally skipping existing targets or comparing their bytes.

    With skip_existing and verify enabled, differing files are recopied.
    A trailing separator or existing directory selects the source basename.
    """
    for src, target in zip(df[src_col], df[tgt_col]):
        target = os.fspath(target)
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        if os.path.isdir(target):
            target = os.path.join(target, os.path.basename(src))
        if skip_existing and os.path.isfile(target):
            if not verify or _same_contents(src, target):
                continue
        if os.path.exists(target) and os.path.samefile(src, target):
            raise shutil.SameFileError(src, target)
        # Publish a complete file even if the transfer is interrupted.
        destination = Path(target).resolve()
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            staging = Path(tmp.name)
        try:
            shutil.copy2(src, staging)
            os.replace(staging, destination)
        finally:
            staging.unlink(missing_ok=True)


def _same_contents(src, target):
    if os.path.getsize(src) != os.path.getsize(target):
        return False
    with open(src, "rb") as left, open(target, "rb") as right:
        while True:
            chunk = left.read(1024 * 1024)
            if chunk != right.read(1024 * 1024):
                return False
            if not chunk:
                return True


def rsync_from_df(df, src_col, src_root, dst_root, verbosity=1,
                  remove_sync_spec_file=True, spec_filename=None,
                  archive=True, mkpath=True):
    """Sync listed files in one rsync call, preserving their relative paths.

    Paths may be absolute or relative to src_root. An explicit spec_filename
    must be unused. Return the manifest path when remove_sync_spec_file=False.
    """
    root = Path(src_root).expanduser().resolve()
    destination = Path(dst_root).expanduser().resolve()
    entries = []
    for value in df[src_col]:
        path = (root / value).resolve()
        relative = path.relative_to(root)
        if not path.is_file():
            raise ValueError(f"Expected a source file: {path}")
        entries.append(os.fsencode(relative) + b"\0")

    manifest = (open(spec_filename, "xb") if spec_filename is not None else
                tempfile.NamedTemporaryFile(dir=".", prefix=".rsync-", delete=False))
    spec = Path(manifest.name).absolute()
    try:
        with manifest:
            manifest.writelines(entries)
        options = ["-a" if archive else "-r"]
        if verbosity > 0:
            options.append("-vv" if verbosity >= 2 else "-v")
        if mkpath:
            options.append("--mkpath")
        subprocess.run(["rsync", *options, "--from0", f"--files-from={spec}",
                        "--", str(root) + os.sep, str(destination) + os.sep], check=True)
    finally:
        if remove_sync_spec_file:
            spec.unlink(missing_ok=True)
    if not remove_sync_spec_file:
        return spec
