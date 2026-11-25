"""Optional Nipype workflow for discovering files."""


from os.path import abspath


def _file_list(src_dir, filters):
    from nisupply.io import find_files
    return find_files(src_dir, **filters)


def discovery_workflow(src_dir, name="nisupply_discovery", **filters):
    """Build a Nipype workflow with a discover node exposing a files output."""
    from nipype import Node, Workflow
    from nipype.interfaces.utility import Function

    node = Node(Function(input_names=["src_dir", "filters"],
                         output_names=["files"], function=_file_list), name="discover")
    node.inputs.src_dir = abspath(src_dir)
    node.inputs.filters = filters
    workflow = Workflow(name=name)
    workflow.add_nodes([node])
    return workflow
