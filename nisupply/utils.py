#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
General utilties

@author: johannes.wiesner
"""

import os
import pathlib
import gzip
import shutil
import stat

# FIXME: Should operate on the 'filepath' column of pandas dataframe
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