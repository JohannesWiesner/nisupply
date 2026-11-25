nisupply
========

Discover files in a semi-structured dataset, extract entities and build a new
directory layout from the resulting pandas table.

.. code-block:: python

   from nisupply.io import get_filepath_df, copy_files
   from nisupply.structure import join_path

   files = get_filepath_df("src", filename_regex=r"^cat_.*\.xml$",
                           regex_dict={"subject": r"subject_(\d+)"},
                           exclude_nested_dirs=["pre/standard"])
   join_path(files, "out", "sub-{subject}", "report.xml", new_col="target")
   copy_files(files, "filepath", "target", skip_existing=True, verify=True)

Use an output template that uniquely identifies each input you want to retain.
Use filename_regex for a basename and regex_match for the full path.
Both use regex search and combine with the other filters. Extraction uses the
first capture group, or the whole match for patterns without groups.

Repeated searches
-----------------

Pass a trusted cache directory as the cache argument to get_filepath_df, or
use True for ~/.cache/nisupply. Cached searches are snapshots. Clear the
cache directory after changing the dataset, or omit cache for a fresh scan.

Optional integrations
---------------------

Install nisupply[bids] to use PyBIDS entity definitions::

   from nisupply.bids import bids_regex_dict
   files = get_filepath_df("dataset", regex_dict=bids_regex_dict("subject", "task"))

Install nisupply[workflow] to run discovery as a Nipype workflow::

   from nisupply.workflows import discovery_workflow
   workflow = discovery_workflow("dataset", file_suffix=".nii.gz")
   workflow.run()

For bulk syncing, install the rsync command on the host. The default mkpath
option requires rsync 3.2.3 or later. Pass mkpath=False with an existing
destination on older versions.

API
---

.. automodule:: nisupply.io
   :members:

.. automodule:: nisupply.structure
   :members:

.. automodule:: nisupply.bids
   :members:

.. automodule:: nisupply.workflows
   :members:
