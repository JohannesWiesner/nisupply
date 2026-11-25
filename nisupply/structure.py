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

def add_new_column(df, template, new_col="filepath_new"):
    """Format a template using each row's named columns."""
    df[new_col] = [template.format_map(row) for row in df.to_dict("records")]
    return df


build_column = add_new_column


def get_new_filepath(df, template):
    """Build the legacy filepath_new column."""
    return add_new_column(df, template)


def join_path(df, *parts, new_col="filepath_new"):
    """Join component templates such as root, '{subject}', and '{session}'."""
    df[new_col] = [os.path.join(*(os.fspath(p).format_map(row) for p in parts))
                   for row in df.to_dict("records")]
    return df


def set_dir(df, dst_dir, src_col="filepath", new_col="dst"):
    """Place each source basename directly under dst_dir."""
    df[new_col] = df[src_col].map(lambda p: os.path.join(dst_dir, os.path.basename(p)))
    return df


def add_match_column(df, src_col, new_col, patterns, regex=False, default=None):
    """Assign the first matching mapping value, or default for unmatched rows."""
    rules = [(re.compile(key if regex else re.escape(key)), value)
             for key, value in patterns.items()]

    def classify(item):
        if isinstance(item, (str, os.PathLike)):
            for pattern, value in rules:
                if pattern.search(os.fspath(item)):
                    return value
        return default

    df[new_col] = df[src_col].map(classify)
    return df
