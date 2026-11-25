"""Patterns from the installed PyBIDS version."""


def bids_regex_dict(*names):
    """Return official BIDS entity patterns for use with get_filepath_df."""
    from bids.layout import Config

    entities = Config.load("bids").entities
    return {name: entities[name].pattern for name in names or entities
            if entities[name].pattern is not None}
