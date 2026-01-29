#!/usr/bin/env python3
###########################################################################################
#  package:   pNbody
#  file:      lazy_loading.py
#  brief:     Defines HDF5 lazy loading utils
#  copyright: GPLv3
#             Copyright (C) 2025 EPFL (Ecole Polytechnique Federale de Lausanne)
#             LASTRO - Laboratory of Astrophysics of EPFL
#  author:    Darwin Roduit <darwin.roduit@alumni.epfl.ch>
#
# This file is part of pNbody.
###########################################################################################
import h5py
import numpy as np
import re


def _to_snake_case(name):
    """
    Convert a string to snake_case.

    Handles spaces, dashes, periods, and correctly preserves consecutive capitals (acronyms).
    """
    # 1. Replace existing separators (spaces, dashes, periods, slashes) with a
    # single underscore.
    s1 = re.sub(r"[ \-()\[\]\.\/]", "_", name)

    # 2. Insert an underscore only at casing transitions to prevent splitting acronyms:
    #    a) Insert '_' where a lowercase letter or digit is followed by an
    #    uppercase letter (camelCase transition: 'gitBranch' -> 'git_Branch').
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)

    #    b) Insert '_' where an uppercase letter is followed by an acronym-end
    #       transition (uppercase followed by lowercase: 'HDF5Library' ->
    #       'HDF5_Library').
    #       This is done on the result of step (a) to ensure correct ordering.
    s2 = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", s2)

    # 3. Collapse multiple underscores (resulting from original separators
    # combined with new ones).
    s3 = re.sub(r"__+", "_", s2)

    # 4. Strip leading/trailing underscores and convert the entire string to
    # lowercase.
    s4 = s3.strip("_").lower()
    return s4


class MetadataWrapper:
    """
    Wraps nested dictionaries of metadata (attributes) to allow access
    using dot notation (e.g., obj.group.attribute) and converts keys to snake_case.

    This optimized version eliminates data duplication by only storing the
    original HDF5 structure (`raw_data`) and performing snake_case lookups
    on the fly, thus using `raw_data` as the single source of truth for values.
    """

    def __init__(self, data_dict):
        # 1. Store the original dictionary (the single source of truth for data values)
        self._raw_data = data_dict

        # 2. Build the reverse mapping: snake_case_key -> Original_HDF5_Key
        # This mapping is small and only stores strings (keys), not the large values.
        self._snake_to_hdf5 = {}
        for hdf5_key in data_dict.keys():
            snake_key = _to_snake_case(hdf5_key)

            # Avoid ambiguous access if two HDF5 keys map to the same snake_case key
            if snake_key not in self._snake_to_hdf5:
                self._snake_to_hdf5[snake_key] = hdf5_key

    @property
    def raw_data(self):
        """Returns the original, unmodified HDF5 dictionary structure."""
        return self._raw_data

    def __getstate__(self):
        """
        Return state for pickling (and deepcopy).

        Only save the internal raw data dictionary, which contains the entire state.
        This explicitly tells deepcopy what to serialize, breaking the recursion.
        """
        # Only save the internal raw data dictionary
        return {"_raw_data": self._raw_data}

    def __setstate__(self, state):
        """
        Restore state from pickling (and deepcopy).

        Re-initialize the wrapper using the loaded raw data to rebuild
        the necessary snake_case lookup map.
        """
        # Re-run the standard initialization logic using the loaded state
        self.__init__(state["_raw_data"])

    def __getattr__(self, name):
        """
        Retrieves the value corresponding to a snake_case key.
        Unwraps the data from the 'value' or 'dataset' tag.
        """
        # 3. Handle snake_case attribute access by looking up the original key
        if name in self._snake_to_hdf5:
            original_key = self._snake_to_hdf5[name]
            wrapped_value = self.raw_data[original_key]

            # Check for a nested dictionary which represents a group (not a value or dataset tag)
            if isinstance(wrapped_value, dict) and not any(
                k in wrapped_value for k in ("value", "dataset")
            ):
                # Recursively wrap nested dictionaries (structure access)
                return MetadataWrapper(wrapped_value)

            # Extract the actual value (X or Y) from the wrapper dict
            if "value" in wrapped_value:
                value = wrapped_value["value"]
            elif "dataset" in wrapped_value:
                value = wrapped_value["dataset"]
            else:
                # Should not happen, but return raw for safety
                value = wrapped_value

            # --- Handle value extraction (to avoid returning raw numpy types) ---
            if isinstance(value, np.ndarray) and value.size == 1:
                # Extract scalar numpy array items
                return value.item()
            elif isinstance(value, np.ndarray) and value.dtype.kind in ("S", "U"):
                # Handle string arrays
                decoded = [
                    s.decode("utf-8") if isinstance(s, bytes) else s for s in value
                ]
                return decoded[0] if len(decoded) == 1 else decoded
            elif isinstance(value, bytes):
                # Handle scalar bytes
                return value.decode("utf-8")
            else:
                # Return the raw array/list/scalar
                return value

        # 4. Handle direct access to the raw template (for the writer)
        if name == "raw_data":
            return self.raw_data

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __repr__(self):
        return f"MetadataWrapper(keys={list(self._snake_to_hdf5.keys())})"

    def __dir__(self):
        # Provides the public snake_case keys for tab completion
        return super().__dir__() + list(self._snake_to_hdf5.keys()) + ["raw_data"]


def _read_all_metadata_to_dict(file_or_path, exclude_list):
    """
    Reads all attributes and datasets from specified non-excluded groups
    in the HDF5 file and returns them as a nested dictionary, tagging
    each value with its HDF5 source ('value' for attribute, 'dataset' for dataset).

    Parameters
    ----------
    file_or_path : str or h5py.File
        The HDF5 file path or an open h5py.File object.
    exclude_list : list of str
        A list of group names or prefixes to exclude from reading.
        Defaults to ['PartType'] if None is passed.

    Returns
    -------
    dict
        A dictionary containing the metadata, with values wrapped to indicate
        if they were HDF5 attributes or datasets.
    """
    temp_metadata = {}
    h5_file = None
    close_file = False

    if isinstance(file_or_path, str):
        # If a string (path) is passed, open the file
        try:
            h5_file = h5py.File(file_or_path, "r")
            close_file = True
        except Exception as e:
            print(f"Error opening HDF5 file {file_or_path}: {e}")
            return {}
    elif isinstance(file_or_path, h5py.File):
        # If an open file object is passed, use it directly
        h5_file = file_or_path
    else:
        # Unexpected input type
        print(
            f"Warning: Expected str or h5py.File, got {type(file_or_path)}. Skipping metadata reading."
        )
        return {}

    # Define a helper function to check for exclusion
    def is_excluded(item_name):
        return item_name in exclude_list

    def traverse_group(h5_group, data_dict):
        # Process group attributes
        for attr in h5_group.attrs:
            # ATTRIBUTE: Tagged with 'value'
            data_dict[attr] = {"value": h5_group.attrs[attr]}

        # Traverse group members (datasets and subgroups)
        for item_name, item in h5_group.items():
            if is_excluded(item_name):
                continue

            if isinstance(item, h5py.Group):
                sub_data_dict = {}
                data_dict[item_name] = sub_data_dict
                # Only traverse if not an excluded group
                traverse_group(item, sub_data_dict)
            elif isinstance(item, h5py.Dataset):
                # DATASET: Tagged with 'dataset'. Read data as array.
                data = item[()]
                data_dict[item_name] = {"dataset": data}

    # Traverse all top-level groups
    if h5_file:
        for group_name in h5_file.keys():
            group = h5_file[group_name]
            # Check for exclusion on top-level group names (and ensure it's a Group)
            if not is_excluded(group_name) and isinstance(group, h5py.Group):
                group_data = {}
                temp_metadata[group_name] = group_data
                traverse_group(group, group_data)

        # Also include attributes of the root group ('/')
        for attr in h5_file.attrs:
            # ROOT ATTRIBUTE: Tagged with 'value'
            temp_metadata[attr] = {"value": h5_file.attrs[attr]}

        if close_file:
            h5_file.close()

    return temp_metadata

def _write_metadata_group(Nbody, h5_group, data_dict, trans, prefix=""):
        """
        Recursively writes metadata from a dictionary to HDF5 attributes/groups,
        distinguishing between attributes and datasets based on the stored tag.

        Parameters
        ----------
        h5_group : h5py.Group
            The current HDF5 group object to write into.
        data_dict : dict
            The dictionary representing the metadata structure of the current group.
        trans : dict
            The translation dictionary mapping HDF5 paths to pNbody attributes.
        prefix : str, optional
            The full HDF5 path of the current group (used for translation lookup).
        """

        for key, value in data_dict.items():
            full_hdf5_path = f"{prefix}/{key}" if prefix else key

            # 1. Determine the effective template value and if it was an original HDF5 Dataset
            original_is_dataset = False
            effective_template_value = value

            if isinstance(value, dict):
                if 'value' in value:
                    effective_template_value = value['value']
                elif 'dataset' in value:
                    effective_template_value = value['dataset']
                    original_is_dataset = True
                # If it's a dict but not tagged, we assume it's a nested group (and handle it below)

            # --- Check if we are recursing into a group ---
            # If the item is a dictionary AND it was NOT a wrapped data item, it is a nested group.
            if isinstance(value, dict) and not ('value' in value or 'dataset' in value):
                # This is a sub-group, recurse
                if key not in h5_group:
                    new_h5_group = h5_group.create_group(key)
                else:
                    new_h5_group = h5_group[key]

                _write_metadata_group(Nbody, new_h5_group, value, trans, full_hdf5_path)

            # --- Otherwise, this is a data item (Attribute or Dataset) ---
            else:
                pnbody_attr_name = trans.get(full_hdf5_path)
                value_to_write = None

                # Prioritization Check: Use the pNbody attribute if it exists (takes precedence).
                if pnbody_attr_name and hasattr(Nbody, pnbody_attr_name):
                    value_to_write = getattr(Nbody, pnbody_attr_name)
                    # (Special handling for MPI/npart_tot goes here if applicable)
                else:
                    # Use the template value (which is already unwrapped or was a raw value)
                    value_to_write = effective_template_value


                if original_is_dataset:
                    # Case 1: Write as HDF5 Dataset (Array/Large Data)

                    # Ensure value_to_write is a NumPy array
                    if not isinstance(value_to_write, np.ndarray):
                        value_to_write = np.array(value_to_write)

                    # Overwrite/Create the Dataset
                    if key in h5_group:
                         # In 'w' mode this is fine, but checking avoids potential issues
                        del h5_group[key]

                    h5_group.create_dataset(key, data=value_to_write)

                else:
                    # Case 2: Write as HDF5 Attribute (Scalar/Metadata)

                    # Prepare the value for HDF5 attribute writing
                    if value_to_write is None:
                        value_to_write = "None"

                    # Convert to appropriate HDF5 attribute type
                    if isinstance(value_to_write, str):
                        # Convert string to fixed-length HDF5 string type
                        value_to_write = np.array(value_to_write, dtype="S")
                    elif not isinstance(value_to_write, np.ndarray):
                        # Convert non-string scalars/lists/tuples to numpy array for attribute writing
                        # This ensures single values are wrapped correctly, but preserves the original
                        # *intent* to be an attribute.
                        value_to_write = np.array(value_to_write)

                    # Write the attribute to the current group
                    h5_group.attrs[key] = value_to_write
