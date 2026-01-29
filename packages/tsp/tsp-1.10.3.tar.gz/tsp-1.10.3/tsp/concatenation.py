from __future__ import annotations

import numpy as np
import pandas as pd

from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from tsp import TSP


def _tsp_concat(tsp_list: "list[TSP]", on_conflict="error", metadata='first') -> dict[str, Any]:
    """ Helper for core.tsp_concat """
    # Validate the TSPs in the list
    _validate_tsp_list(tsp_list)
    
    # Combine the TSPs
    dfs = [t.wide for t in tsp_list]
    combined_df = _concat_deduplicate(dfs, on_conflict=on_conflict)
    combined_counts = _concat_deduplicate([pd.DataFrame(t.counts, columns=t.depths, index=t.wide.index) for t in tsp_list], on_conflict=on_conflict).values
    
    # Combine metadata
    if metadata == 'first':
        metadata = {key:val for key, val in tsp_list[0].metadata.items()}
        latitude = tsp_list[0].latitude
        longitude = tsp_list[0].longitude
        site_id = tsp_list[0].site_id

    elif metadata == 'identical':
        metadata = {key:val for key, val in tsp_list[0].metadata.items()}
        for key, val in metadata.items():
            for t in tsp_list[1:]:
                if key not in t.metadata or t.metadata[key] != val:
                    _ = metadata.pop(key)
        latitude = _none_if_not_identical([t.latitude for t in tsp_list])
        longitude = _none_if_not_identical([t.longitude for t in tsp_list])
        site_id = _none_if_not_identical([t.site_id for t in tsp_list])
            
    elif metadata == 'none':
        metadata = None
        latitude, longitude, site_id = None, None, None
    
    else:
        raise ValueError(f"Unknown metadata method: {metadata}")
    
    #final_tsp = TSP(times=combined_df.index, values=combined_df.values, depths=combined_df.columns, 
    #                latitude=latitude, longitude=longitude,
   #                 site_id=site_id, metadata=metadata)
    try:
        combined_df.drop('time', axis=1, inplace=True)
    except KeyError:
        Warning("Deprecation Error: The 'time' column is no longer used in TSP objects. Please update your code to avoid this warning.")

    tsp_dict = {
        'times': combined_df.index,
        'values': combined_df.values,
        'depths': combined_df.columns,
        'latitude': latitude,
        'longitude': longitude,
        'site_id': site_id,
        'metadata': metadata,
        'counts': combined_counts
    }
    return tsp_dict


def _none_if_not_identical(list):
    """Check if all elements in the list are identical. If they are, return the first element; otherwise, return None."""
    first = list[0]
    for item in list[1:]:
        if item != first:
            return None
    return first


def _validate_tsp_list(tsp_list: "list[TSP]"):
    """Check that all TSPs in the list have the same depths."""
    depths0 = tsp_list[0].depths
    for t in tsp_list[1:]:
        if not np.array_equal(depths0, t.depths):
            raise ValueError("All TSPs must have the same depths.")
        

def _concat_deduplicate(df_list, on_conflict='error'):
    """
    Concatenates a list of DataFrames, handling duplicate indices based on row values.

    Args:
        df_list (list): A list of pandas DataFrames. Assumes they have identical
                        column names.
        on_conflict (str): Specifies how to handle duplicate indices with
                           unequal row values.
                           - 'error': Raise a ValueError (default).
                           - 'keep_first': Keep the row corresponding to the first
                                           DataFrame in the list where the index appeared.
                           - 'keep_last': Keep the row corresponding to the last
                            DataFrame in the list where the index appeared.

    Returns:
        pandas.DataFrame: The concatenated DataFrame with duplicates handled
                          according to the specified rules.

    Raises:
        ValueError: If df_list is empty.
        ValueError: If on_conflict is not 'error', 'keep_first', or 'keep_last'.
        ValueError: If on_conflict='error' and duplicate indices with
                    non-identical row values are found.
    """
    if not df_list:
        raise ValueError("Input DataFrame list cannot be empty.")

    if on_conflict not in ['error', 'keep_first', 'keep_last']:
        raise ValueError("on_conflict must be either 'error', 'keep_first', or 'keep_last'")

    # Store original index name if it exists
    original_index_name = df_list[0].index.name

    # Concatenate all DataFrames. The order is preserved.
    combined_df = pd.concat(df_list, ignore_index=False) # Keep original indices

    temp_index_col = "__temp_index__"
    combined_reset = combined_df.reset_index(names=temp_index_col)

    # Drop rows that are duplicates based on *all* columns
    deduplicated_reset = combined_reset.drop_duplicates(keep='first')

    # Check for remaining duplicates *only* in the original index column. 
    remaining_duplicates_mask = deduplicated_reset.duplicated(subset=temp_index_col, keep=False)

    if remaining_duplicates_mask.any():
        # We have indices that appeared multiple times with different values.
        if on_conflict == 'error':
            conflicting_indices = deduplicated_reset.loc[remaining_duplicates_mask, temp_index_col].unique()
            raise ValueError(
                f"Duplicate indices with non-identical values found: "
                f"{list(conflicting_indices)}. Use on_conflict='keep_first' to keep "
                f"the first occurrence."
            )
        elif on_conflict == 'keep_first':
            # Drop the later occurrences of these conflicting index values.
            # Since 'deduplicated_reset' preserved the first unique (index, row_value)
            # combination, dropping duplicates based solely on the index column
            # while keeping the first achieves the desired outcome.
            final_reset = deduplicated_reset.drop_duplicates(subset=temp_index_col, keep='first')
        elif on_conflict == 'keep_last':
            final_reset = deduplicated_reset.drop_duplicates(subset=temp_index_col, keep='last')
        else: 
            pass
    else:
        # No conflicting duplicates (duplicate indices with different values) were found.
        final_reset = deduplicated_reset

    final_df = final_reset.set_index(temp_index_col)
    final_df.index.name = original_index_name
    # Sort by time, ascending
    final_df.sort_index(inplace=True)

    return final_df
