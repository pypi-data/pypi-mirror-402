"""
JSON Flattener for Kipu API responses
Handles deeply nested JSON structures and converts them to flat pandas DataFrames
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio


class JsonFlattener:
    def __init__(self, sep: str = "_"):
        self.sep = sep

    def flatten_json(
        self, data: Dict[str, Any], parent_key: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Recursive function to flatten the JSON object and build the records in a cartesian product style.
        """
        records: List[Dict[str, Any]] = [
            {}
        ]  # Start with a single empty record (to accumulate parent values)

        for key, value in data.items():
            new_key = f"{parent_key}{self.sep}{key}" if parent_key else key

            if isinstance(value, dict):
                # Flatten nested dictionaries
                nested_records = self.flatten_json(value, new_key)
                records = self._merge_records(records, nested_records)
            elif isinstance(value, list):
                # Handle lists of dictionaries or primitives
                list_records = [{}]
                for sub_item in value:
                    if isinstance(sub_item, dict):
                        # Recursively flatten nested dictionaries within the list
                        sub_item_records = self.flatten_json(sub_item, new_key)
                        list_records.extend(sub_item_records)
                    else:
                        # Handle non-dictionary values (e.g., strings, numbers) within lists
                        list_records.append(
                            {new_key: sub_item}
                        )  # Create a dict with the value

                # Merge the list records with the parent records
                if {} in list_records and len(list_records) > 1:
                    list_records.remove({})
                records = self._merge_records(records, list_records)
            else:
                # Handle simple key-value pairs
                for record in records:
                    record[new_key] = value

        if {} in records and len(records) > 1:
            records.remove({})

        return records

    def _merge_records(
        self, parent_records: List[Dict[str, Any]], child_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge the child records with each of the parent records to create a cartesian product style of flattening.
        """
        merged_records: List[Dict[str, Any]] = [{}]

        for parent in parent_records:
            for child in child_records:
                merged_record = parent.copy()  # Copy parent to avoid modifying original
                merged_record.update(child)  # Merge with child
                merged_records.append(merged_record)

        if {} in merged_records and len(merged_records) > 1:
            merged_records.remove({})

        return merged_records

    # Asynchronous function to flatten each record in parallel using ThreadPoolExecutor
    async def flatten_json_df(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        loop = asyncio.get_event_loop()

        # Use ThreadPoolExecutor for CPU-bound flattening operations
        with ThreadPoolExecutor() as executor:
            futures = [
                loop.run_in_executor(executor, self.flatten_json, record)
                for record in tqdm(data, desc="Processing Flatten futures")
            ]
            result = await tqdm_asyncio.gather(
                *futures, desc="Gathering Flatten futures"
            )

        # Convert results to DataFrame
        df_tmp = [
            pd.DataFrame(flat_data_dict)
            for flat_data_dict in tqdm(result, desc="Converting Dict to DataFrames")
        ]
        master_df = pd.concat(df_tmp, ignore_index=True)
        master_df.replace(
            {
                pd.NaT: None,
                pd.NA: None,
                np.nan: None,
                "None": None,
                "<NA>": None,
                "nan": None,
            },
            inplace=True,
        )
        master_df = master_df[~master_df.isnull().all(axis=1)]

        return master_df
