import logging
import warnings
from typing import Any, Dict, List

import lasio
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

logger = logging.getLogger(__name__)


class DataLoader(object):
    """
    A helper class that performs the data loading part of processing MLPet data.
    This is an **internal** class only. It is **strictly** to be used as a super
    of the Dataset class.

    """

    def save_df_to_cls(self, df: DataFrame) -> DataFrame:
        """
        Simple wrapper function to save a df to the class instance

        Args:
            df (DataFrame): Dataframe to be saved to class instance

        Returns:
            DataFrame: Returns the passed dataframe.
        """
        self.df_original = df
        return df

    def load_from_las(
        self, filepaths: List[str], metadata=None, **kwargs: Any
    ) -> DataFrame:
        """
        Loads data from las file(s)

        Note:
            This function does not support las files containing multiple wells!

        Warning:
            This function expects the LAS file to represent a well log set where the
            reference is always depth. As such it automatically inserts a column
            called "DEPTH" if DEPTH does not exist in the LAS file. The values
            of DEPTH are the same as the index retrieved from the LAS file.

        Args:
            filepaths (list of strings): paths to las files
            metadata (list of strings): attributes to extract from las file. These
                must match header item names!

        Returns:
            DataFrame: Returns the data loaded from the provided las files.
        """
        if metadata is None:
            metadata = ["WELL", "SET"]
        dfs = []
        for path in filepaths:
            las = lasio.read(path)
            las_data = las.df()
            reference_name = las_data.index.name
            if reference_name != "DEPTH":
                logger.warning(
                    f"Could not find a curve called DEPTH in {path}! "
                    f"The reference curve for this file is called {reference_name}."
                    " Initialising a column called 'DEPTH' in the dataframe for"
                    f" this file with the same values as the {reference_name} column.",
                    stacklevel=2,
                )
                las_data["DEPTH"] = las_data.index
            las_data = las_data.reset_index()
            for attr in metadata:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        category=FutureWarning,
                        message=(
                            ".*The default dtype for empty Series will be 'object'.*"
                        ),
                    )
                    try:
                        las_data[attr] = las.well[attr].value
                    except KeyError:
                        try:
                            las_data[attr] = las.params[attr].value
                        except KeyError:
                            logger.warning(
                                f"Attribute {attr} not found in las file {path}. "
                                f"Available attributes are {sorted({*las.well.keys(), *las.params.keys()})}",
                                stacklevel=2,
                            )
                            las_data[attr] = np.nan
            dfs.append(las_data)
        return self.save_df_to_cls(pd.concat(dfs, axis=0))

    def load_from_csv(self, filepath: str, **kwargs: Any) -> DataFrame:
        """
        Loads data from csv files

        Args:
            filepath (string): path to csv file

        Returns:
            DataFrame: Returns the data loaded from the provided csv file.
        """
        return self.save_df_to_cls(pd.read_csv(filepath, **kwargs))

    def load_from_pickle(self, filepath: str, **kwargs: Any) -> DataFrame:
        """
        Loads data from pickle files

        Args:
            filepath (string): path to pickle file

        Returns:
            DataFrame: Returns the data loaded from the provided csv file.
        """
        return self.save_df_to_cls(pd.read_pickle(filepath, **kwargs))

    def load_from_dict(self, data_dict: Dict[str, Any], **kwargs: Any) -> DataFrame:
        """
        Loads data from a dictionary

        Args:
            data_dict (dict): dictionary with data

        Returns:
            DataFrame: Returns the data loaded from the provided dictionary.
        """
        return self.save_df_to_cls(pd.DataFrame.from_dict(data_dict, **kwargs))
