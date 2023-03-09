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