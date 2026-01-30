import os


def get_base_path():
    """Return the directory containing this module."""
    return os.path.dirname(os.path.abspath(__file__))


def get_jre_home():
    """Return the absolute path to the bundled JRE HOME."""
    # Structure: <pkg>/dependencies/jre/<unzipped_folder>/...
    # Since the zip names vary (jdk-17...), we might need to look for the first child
    jre_root = os.path.join(get_base_path(), 'dependencies', 'jre')

    if not os.path.exists(jre_root):
        raise FileNotFoundError(f"JRE directory not found at {jre_root}")

    # Assuming the zip extracts to a single folder inside 'jre'
    # or the files are directly in jre. Adjust based on zip structure.
    # If the zip contains a root folder (e.g., 'jdk-17.0.1'), find it:
    entries = os.listdir(jre_root)
    for entry in entries:
        full_path = os.path.join(jre_root, entry)
        if os.path.isdir(full_path):
            return full_path

    # Fallback if extracted flat
    return jre_root


# def get_qps_path():
#     """Return the absolute path to the QPS jar or executable."""
#     # Adjust 'QPS.jar' to the actual entry point filename
#     qps_root = os.path.join(get_base_path(), 'dependencies', 'qps')
#
#     if not os.path.exists(qps_root):
#         raise FileNotFoundError(f"QPS directory not found at {qps_root}")
#
#     return qps_root
