#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
An example script on how to use nisupply

@author: johannes.wiesner
"""

from nisupply.io import get_filepath_df

df = get_filepath_df(src_dir='./example_dataset',
                     extract_id=True,
                     id_pattern='subject_\d+',
                     re_group=0,
                     id_column_name='participant',
                     file_suffix='.nii.gz',
                     file_prefix='fmri_nback',
                     must_contain='session_2')





