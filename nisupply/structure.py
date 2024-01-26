#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities to restructure the filepath dataframe

@author: johannes.wiesner
"""

import re
import os
import pathlib

def get_file_extension(df):
    '''Returns the file extension(s) of a given filepath. This function
    will return all extensions of each filepath (not only the last one)
    
    Parameters
    ----------
    df : pd.DataFrame
        A pandas dataframe that must have a column named 'filepath'.
    
    Returns
    -------
    df: pd.DataFrame
        Returns the dataframe with a new column 'file_extension' that 
        holds the file extension(s) of each filepath.
    
    '''
    
    df['file_extension'] = df['filepath'].apply(lambda filepath: ''.join(pathlib.Path(filepath).suffixes))
    
    return df

def get_dst_dir(df,src_dir,dst_dir):
    '''Creates a new column 'dst' in the dataframe where the source directory
    in each filepath is replaced with the destination directory'''
    
    src_dir = os.path.normpath(src_dir)
    dst_dir = os.path.normpath(dst_dir)
    df['dst'] = df['filepath'].apply(lambda row: os.path.join(dst_dir,row.replace(src_dir,'').lstrip(os.sep)))
    
    return df

def get_new_filepath(df,template):
    '''Helps you to create new directories and new filenames using string formatting.
    
    Parameters
    ----------
    df : pd.DataFrame
        A pandas data frame.
    template : str
        A string that serves as template for the new filepath. The string may 
        contain placeholders in curly brackets that match to a column name in the data frame. 
        
    Returns
    -------
    pd.DataFrame
        The original dataframe with an additional columm 'filepath_new' that
        holds the new filepath for each row

    '''

    def _from_template(row,template):
        return template.format(**row.to_dict())

    df['filepath_new'] = df.apply(lambda row: _from_template(row,template),axis=1)

    return df
