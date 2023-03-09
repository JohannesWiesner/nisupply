#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilties to handle BIDS-information

@author: johannes.wiesner
"""

from .io import regex_extract
import re
import os

# TODO: Should be grabbed as .json from pybids to be always conform with upstream
BIDS_ENTITY_REGEX_DICT={'session':('(_ses-)(\d+)',2),
                        'run':('(_run-)(\d+)',2),
                        'data_type':('func|dwi|fmap|anat|meg|eeg|ieeg|beh',0),
                        'echo':('(_echo-)(\d+)',2)}

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

def get_file_extension(filepath):
    '''Returns the file extension(s) of a given filepath. 
    https://stackoverflow.com/a/35188296/8792159'''
    file_suffix = ''.join(pathlib.Path(filepath).suffixes)
    return file_suffix

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