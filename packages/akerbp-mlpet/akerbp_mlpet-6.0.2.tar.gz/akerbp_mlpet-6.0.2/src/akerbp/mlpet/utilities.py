import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
from numpy import float64
from sklearn.metrics import DistanceMetric
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


def _first_non_null_by_row(values: pd.DataFrame) -> pd.Series:
    """
    Return the first non-null value per row, respecting column order.

    Args:
        values (pd.DataFrame): Source values ordered by priority left to right.

    Returns:
        pd.Series: First non-null entry per row, aligned to the input index.
    """
    if values.shape[1] == 0:
        return pd.Series(pd.NA, index=values.index, dtype=object)
    if values.shape[0] == 0:
        return values.iloc[:, 0].copy()
    arr = values.to_numpy(copy=False)
    valid = ~pd.isna(arr)
    first_idx = valid.argmax(axis=1)
    result = pd.Series(arr[np.arange(arr.shape[0]), first_idx], index=values.index)
    return result.infer_objects(copy=False)


def drop_rows_wo_label(df: pd.DataFrame, label_column: str, **kwargs) -> pd.DataFrame:
    """
    Removes columns with missing targets.

    Now that the imputation is done via pd.df.fillna(), what we need is the constant filler_value
    If the imputation is everdone using one of sklearn.impute methods or a similar API, we can use
    the indicator column (add_indicator=True)

    Args:
        df (pd.DataFrame): dataframe to process
        label_column (str): Name of the label column containing rows without labels

    Keyword Args:
        missing_label_value (str, optional): If nans are denoted differently than np.nans,
            a missing_label_value can be passed as a kwarg and all rows containing
            this missing_label_value in the label column will be dropped


    Returns:
        pd.DataFrame: processed dataframe
    """
    missing_label_value = kwargs.get("missing_label_value")
    if missing_label_value is not None:
        return df.loc[df[label_column] != missing_label_value, :]
    return df.loc[~df[label_column].isna(), :]


def normalize_zonation_columns(
    df: pd.DataFrame,
    hierarchy_df: pd.DataFrame,
    zonation_columns_to_normalize: List[str],
) -> pd.DataFrame:
    """
    A helper function to normalize lithostratigraphic columns such that they adhere to
    a lithostratigraphic hierarchical scheme.

    By normalize we mean that we combine all zonation_columns_to_normalize into a single
    column and then standardize the names and apply the hierarchical mapping provided in
    mapping_df to ensure that the lithostratigraphic units in the dataframe are consistent
    with the lithostratigraphic scheme defined in mapping_df.

    Warning:
        Since we are merging multiple columns into one, the order of the columns in
        zonation_columns_to_normalize matters. The first column in the list has the
        highest priority and the last column the lowest. For example, if zonation_columns_to_normalize
        is ["FORMATION", "GROUP"], then if a row has a value in the FORMATION column, it will be
        used as the normalized value. If the FORMATION column is NaN, then the value from the
        GROUP column will be used.

    Args:
        df_ (pd.DataFrame): The dataframe containing both the GROUP and FORMATION
            columns to be normalized
        hierarchy_df (pd.DataFrame): A dataframe containing a lithostratigraphic hierarchical mapping
            It must be structured as follows (column names are in caps):
                - UNIQUE_LSU_NAME: The standardized LSU_NAME (the output of the standardize_lsu_names function)
                - * columns for each lithostratigraphic level (e.g. SYSTEM, GROUP, FORMATION, MEMBER)
            An example of such a table is the akerbp_best_stratigraphy_wide table in our Fabric workspace
        zonation_columns_to_normalize (list): A list of column names to be normalized.
            See the docstring for more info about this.

    Returns:
        pd.DataFrame: The dataframe with the normalization applied
    """
    # Merge user-provided zonation data columns where the order they are provided in
    # is important.
    # However, if we have unknown zones at a lower level e.g. formation but known zones
    # one step up in the hierarchy we want to keep the known zone. Therefore we remove
    # UNKNOWN FM & GP if present, fillna and then put back if the fillna did not fill
    # anything
    # 1) Build a boolean DataFrame that marks any cell starting with "UNKNOWN" among those columns
    zonation_df = df[zonation_columns_to_normalize]  # noqa: PD013, PD010
    unknown_pattern = r"UNKNOWN|UNDEFINED|NO\s+FORMAL"
    zonation_values = zonation_df.astype(str).to_numpy()
    flattened = pd.Series(zonation_values.ravel())
    is_unknown = pd.DataFrame(
        flattened.str
        .upper()
        .str.strip()
        .str.contains(unknown_pattern)
        .to_numpy()
        .reshape(zonation_values.shape),
        index=zonation_df.index,
        columns=zonation_df.columns,
    )

    with pd.option_context("future.no_silent_downcasting", True):
        # 2) Create a unknown-free merged_zonation column
        merged_clean_zonations = _first_non_null_by_row(
            zonation_df.where(~is_unknown, np.nan)
        )

        # 3) Create a merged unknown column
        unknown_zonations = _first_non_null_by_row(
            zonation_df.where(is_unknown, np.nan)
        )

    # 4) Merge the two together and set it back to df
    merged_zonations = merged_clean_zonations.combine_first(unknown_zonations)
    df = df.assign(MERGED_ZONATION=merged_zonations.to_numpy())

    # 5) Remove the columns that were used for merging
    df = df.drop(columns=zonation_columns_to_normalize)

    # 6) Standardize the merged zonation column
    df = df.assign(UNIQUE_LSU_NAME=standardize_lsu_names(df["MERGED_ZONATION"]))

    # Log any unknowns
    added_join_columns = [c for c in hierarchy_df.columns if c != "UNIQUE_LSU_NAME"]
    unknown_lsus = set(df["UNIQUE_LSU_NAME"].dropna().unique()).difference(
        hierarchy_df["UNIQUE_LSU_NAME"].dropna().unique()
    )
    if unknown_lsus:
        logger.warning(
            f"Found {len(unknown_lsus)} unique lithostratigraphic units that are not present in the provided hierarchy mapping. These will be mapped to all zonation columns ({added_join_columns}): {unknown_lsus}",
            stacklevel=2,
        )

    # Merge with the hierarchy_df
    if pd.isna(df["UNIQUE_LSU_NAME"]).all():
        df.loc[:, added_join_columns] = pd.NA
    else:
        df = df.merge(
            hierarchy_df,
            on="UNIQUE_LSU_NAME",
            how="left",
            validate="many_to_one",
        )

    # Backfill all columns with merged_zonation to not lose any information if
    # the lithostratigraphic scheme in hierarchy_df does not include an entry
    # for certain lithostratigraphic units present in df
    if unknown_lsus:
        lsus_to_persist = df["MERGED_ZONATION"].copy()
        lsus_to_persist.loc[~df["UNIQUE_LSU_NAME"].isin(unknown_lsus)] = pd.NA
        for col in added_join_columns:
            df[col] = df[col].combine_first(lsus_to_persist)

    df = df.drop(columns=["MERGED_ZONATION", "UNIQUE_LSU_NAME"])

    return df


def standardize_lsu_names(lsu_names: pd.Series) -> pd.Series:
    """
    Performs several string operations to standardize lithostratigraphic unit names
    for later categorisation.

    Args:
        lsu_names (pd.Series): A series of lithostratigraphic unit names

    Returns:
        pd.Series: Returns a series of standardized lithostratigraphic unit names
    """
    megasequence_pat = re.compile(r"\b[A-Z]{2}\d{1,2}\b")
    tuff_pat = re.compile(r"\bTUFF\b")

    def _standardize(name: str):
        # First perform some formatting to ensure consistencies in the checks
        name = str(name).upper().strip()

        # Tuff members are special cases - Take BALDER TUFF for example. We need to keep tuff
        if tuff_pat.search(name) is not None:
            tuff_zone = True
        else:
            tuff_zone = False

        # Split and keep only the actual lsu name
        # lsus with megasequences in their name have to be handled as is unfortunately...
        if megasequence_pat.search(name) is not None:
            max_split = None
        # Intra members are special cases where we want to keep the first two words
        elif "INTRA" in name:
            max_split = 2
        else:
            max_split = 1

        allowed_delimiters = [" ", "_"]
        for d in allowed_delimiters:
            name = "|".join(name.split(d)[:max_split])

        # Special case for TUFF
        if tuff_zone:
            name += "|TUFF"

        # Replace special characters
        replacements = {"AA": "A", "Å": "A", "AE": "A", "Æ": "A", "OE": "O", "Ø": "O"}
        for old, new in replacements.items():
            name = name.replace(old, new)
        return name

    isna = pd.isna(lsu_names)
    unique_lsu_map = {lsu: _standardize(lsu) for lsu in lsu_names.loc[~isna].unique()}
    with pd.option_context("mode.copy_on_write", True):
        lsu_names.loc[~isna] = (
            lsu_names.loc[~isna].astype(str).map(unique_lsu_map).fillna(pd.NA)
        )
        lsu_names.loc[isna] = pd.NA
    return lsu_names


def remove_sidetrack_from_wellbore_name(wellbore_name: str) -> str:
    """Return a wellbore name without sidetrack suffix.

    Parses a wellbore name assumed to contain a whitespace separating the base
    well name from an identifier that may include a sidetrack part (e.g. 'T2').
    Everything from the first 'T' onward in the identifier (if present) is removed.
    The remaining base well name and numeric identifier are joined by a single
    space.

    Example:
        Input: 'WELL_123 T2'  -> Output: 'WELL 123'
        Input: 'FIELD-1_45 T01' -> Output: 'FIELD-1 45'
        Input: 'WELL_789' -> Output: 'WELL 789'

    Args:
        wellbore_name (str): Original wellbore name in the format
            '<well>_<identifier>[T<sidetrack>]'. Must contain at least one underscore.

    Returns:
        str: Normalized wellbore name without sidetrack suffix, with a single space
        separating the well name and numeric identifier.

    Notes:
        - If there is no 'T' in the identifier part, the identifier is returned as-is.
        - Only the first whitespace is considered; additional whitespaces (if any)
          remain in the well name portion.
    """
    well, *sidetrack = wellbore_name.split(" ", maxsplit=1)
    wellbore_id = "".join(sidetrack).split("T")[0]
    return " ".join([well, wellbore_id]).strip()


def standardize_names(
    names: List[str], mapper: Dict[str, str]
) -> Tuple[List[str], Dict[str, str]]:
    """
    Standardize curve names in a list based on the curve_mappings dictionary.
    Any columns not in the dictionary are ignored.

    Args:
        names (list): list with curves names
        mapper (dictionary): dictionary with mappings. Defaults to curve_mappings.

    Returns:
        list: list of strings with standardized curve names
    """
    standardized_names = []
    for name in names:
        mapped_name = mapper.get(name)
        if mapped_name:
            standardized_names.append(mapped_name)
        else:
            standardized_names.append(name)
    old_new_cols = {n: o for o, n in zip(names, standardized_names, strict=False)}
    return standardized_names, old_new_cols


def standardize_curve_names(df: pd.DataFrame, mapper: Dict[str, str]) -> pd.DataFrame:
    """
    Standardize curve names in a dataframe based on the curve_mappings dictionary.
    Any columns not in the dictionary are ignored.

    Args:
        df (pd.DataFrame): dataframe to which apply standardization of columns names
        mapper (dictionary): dictionary with mappings. Defaults to curve_mappings.
            They keys should be the old curve name and the values the desired
            curved name.

    Returns:
        pd.DataFrame: dataframe with columns names standardized
    """
    return df.rename(columns=mapper)


def get_col_types(
    df: pd.DataFrame, categorical_curves: Optional[List[str]] = None, warn: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Returns lists of numerical and categorical columns

    Args:
        df (pd.DataFrame): dataframe with columns to classify
        categorical_curves (list): List of column names that should be considered as
            categorical. Defaults to an empty list.
        warn (bool): Whether to warn the user if categorical curves were
            detected which were not in the provided categorical curves list.

    Returns:
        tuple: lists of numerical and categorical columns
    """
    if categorical_curves is None:
        categorical_curves = []
    cat_original: Set[str] = set(categorical_curves)
    # Make sure we are comparing apples with apples. Sometimes cat_original
    # will contain column names that are no longer in the passed df and this
    # will cause a false positive and trigger the first if check below. So
    # ensure that all cols in cat_original are in the df before proceeding.
    cat_original = {c for c in cat_original if c in df.columns}
    num_cols = set(df.select_dtypes(include="number").columns)
    cat_cols = set(df.columns) - num_cols
    if warn:
        if cat_cols != cat_original:
            extra = cat_original - cat_cols
            if extra:
                logger.warning(
                    f"Cols {extra} were specified as categorical by user even though"
                    " they are numerical. Note: These column names are the names"
                    " after they have been mapped using the provided mappings.yaml!"
                    " So it could be another column from your original data that"
                    " triggered this warning and instead was mapped to one of the"
                    " names printed above.",
                    stacklevel=2,
                )
            extra = cat_cols - cat_original
            if extra:
                logger.warning(
                    f"Cols {extra} were identified as categorical and are being"
                    " treated as such. Note: These column names"
                    " are the names after they have been mapped using the provided"
                    " mappings.yaml! So it could be another column from your"
                    " original data that triggered this warning and instead was"
                    " mapped to one of the names printed above.",
                    stacklevel=2,
                )
    cat_cols = cat_original.union(cat_cols)
    # make sure nothing from categorical is in num cols
    num_cols = num_cols - cat_cols
    return list(num_cols), list(cat_cols)


def wells_split_train_test(
    df: pd.DataFrame, id_column: str, test_size: float, **kwargs
) -> Tuple[List[str], List[str], List[str]]:
    """
    Splits wells into two groups (train and val/test)

    NOTE: Set operations are used to perform the splits so ordering is not
        preserved! The well IDs will be randomly ordered.

    Args:
        df (pd.DataFrame): dataframe with data of wells and well ID
        id_column (str): The name of the column containing well names which will
            be used to perform the split.
        test_size (float): percentage (0-1) of wells to be in val/test data

    Returns:
        wells (list): well IDs
        test_wells (list): wells IDs of val/test data
        training_wells (list): wells IDs of training data
    """
    wells = set(df[id_column].unique())
    rng: np.random.Generator = np.random.default_rng()
    test_wells = set(rng.choice(list(wells), int(len(wells) * test_size)))
    training_wells = wells - test_wells
    return list(wells), list(test_wells), list(training_wells)


def df_split_train_test(
    df: pd.DataFrame,
    id_column: str,
    test_size: float = 0.2,
    test_wells: Optional[List[str]] = None,
    **kwargs,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Splits dataframe into two groups: train and val/test set.

    Args:
        df (pd.Dataframe): dataframe to split
        id_column (str): The name of the column containing well names which will
            be used to perform the split.
        test_size (float, optional): size of val/test data. Defaults to 0.2.
        test_wells (list, optional): list of wells to be in val/test data. Defaults to None.

    Returns:
        tuple: dataframes for train and test sets, and list of test well IDs
    """
    if test_wells is None:
        test_wells = wells_split_train_test(df, id_column, test_size, **kwargs)[1]
        if not test_wells:
            raise ValueError(
                "Not enough wells in your dataset to perform the requested train "
                "test split!"
            )
    df_test = df.loc[df[id_column].isin(test_wells)]
    df_train = df.loc[~df[id_column].isin(test_wells)]
    return df_train, df_test, test_wells


def train_test_split(
    df: pd.DataFrame, target_column: str, id_column: str, **kwargs
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits a dataset into training and val/test sets by well (i.e. for an
    80-20 split, the provided dataset would need data from at least 5 wells).

    This function makes use of several other utility functions. The workflow it
    executes is:

        1. Drops row without labels
        2. Splits into train and test sets using df_split_train_test which in
            turn performs the split via wells_split_train_test

    Args:
        df (pd.DataFrame, optional): dataframe with data
        target_column (str): Name of the target column (y)
        id_column (str): Name of the wells ID column. This is used to perform
            the split based on well ID.

    Keyword Args:
        test_size (float, optional): size of val/test data. Defaults to 0.2.
        test_wells (list, optional): list of wells to be in val/test data. Defaults to None.
        missing_label_value (str, optional): If nans are denoted differently than np.nans,
            a missing_label_value can be passed as a kwarg and all rows containing
            this missing_label_value in the label column will be dropped

    Returns:
        tuple: dataframes for train and test sets, and list of test wells IDs
    """
    df = drop_rows_wo_label(df, target_column, **kwargs)
    df_train, df_test, _ = df_split_train_test(df, id_column, **kwargs)
    return df_train, df_test


def feature_target_split(
    df: pd.DataFrame, target_column: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits set into features and target

    Args:
        df (pd.DataFrame): dataframe to be split
        target_column (str): target column name

    Returns:
        tuple: input (features) and output (target) dataframes
    """
    X = df.loc[:, ~df.columns.isin([target_column])]  # noqa: N806
    y = df[target_column]
    return X, y


def normalize(
    col: pd.Series, ref_min: float64, ref_max: float64, col_min: float, col_max: float
) -> pd.Series:
    """
    Helper function that applies min-max normalization on a pandas series and
    rescales it according to a reference range according to the following formula:

        ref_low + ((col - col_min) * (ref_max - ref_min) / (col_max - col_min))

    Args:
        col (pd.Series): column from dataframe to normalize (series)
        ref_low (float): min value of the column of the well of reference
        ref_high (float): max value of the column of the well of reference
        well_low (float): min value of the column of well to normalize
        well_high (float): max value of the column of well to normalize

    Returns:
        pd.Series: normalized series
    """
    diff_ref = ref_max - ref_min
    diff_well = col_max - col_min
    with np.errstate(divide="ignore", invalid="ignore"):
        norm = ref_min + diff_ref * (col - col_min) / diff_well
    return norm


def calculate_sampling_rate(array: pd.Series, max_sampling_rate=1):
    """
    Calculates the sampling rate of an array by calculating the weighed
    average diff between the array's values.

    Args:
        array (pd.Series): The array for which the sampling rate should be calculated
        max_sampling_rate: The maximum acceptable sampling rate above which the
            the calculated sampling rates should not be included in the weighted
            average calculation (defined in unit length/sample e.g. m). Defaults
            to max 1 m per sample (where m is the assumed unit of the provided array)
    """
    if array.empty or array.isna().all():
        raise ValueError(
            "The provided array is empty or contains only NaNs! Cannot calculate sampling rate!"
        )
    diffs = pd.Series(np.diff(array.to_numpy())).value_counts(normalize=True)
    # Ensure big holes in the index don't affect the weighted average
    # Asumming 1 is a good enough threshold for now
    diffs.loc[diffs.index.to_series().abs().gt(max_sampling_rate)] = np.nan
    sampling_rate = (diffs * diffs.index).sum()
    return sampling_rate


def estimate_parameter(
    df_query: pd.DataFrame,
    df_train: pd.DataFrame,
    id_column: str,
    coordinate_columns: List[str],
    zone_column_name: str,
    parameter_column_name: str,
    distance_metric: Union[str, DistanceMetric, Callable[..., Any]] = "nan_euclidean",
    aggregation_method: Union[str, Callable[[Any], Any]] = "weighted_mean",
    scale_coordinate_columns: bool = True,
    remove_current_well: bool = True,
    nearest_neighbours: Optional[int] = None,
    **kwargs,
) -> pd.DataFrame:
    """Estimate parameter values for query points using spatial interpolation from training data.

    This function performs spatial parameter estimation by finding nearest neighbors within
    geological zones and applying various aggregation methods. It supports different distance
    metrics and can optionally scale coordinates and remove the current well from training data.

    Warning:
        This function is intended to be used **per well**. It assumes that df_query
        contains data for a single well. You can use this function in a groupby operation
        to scale to a df containing multiple wells.

    Args:
        df_query (pd.DataFrame): DataFrame containing query points where parameters need to be estimated.
        df_train (pd.DataFrame): DataFrame containing training data with known parameter values.
        id_column (str): Name of the column containing unique identifiers for wells.
        coordinate_columns (List[str]): List of column names representing spatial coordinates.
        zone_column_name (str): Name of the column containing geological zone information.
        parameter_column_name (str): Name of the column containing the parameter to be estimated.
        distance_metric (Union[str, DistanceMetric, Callable[..., Any]], optional):
            Distance metric for neighbor search. Defaults to "nan_euclidean".
        aggregation_method (Union[str, Callable[[Any], Any]], optional):
            Method for aggregating neighbor values. Options: "weighted_mean", "mean", "median",
            or callable function. Defaults to "weighted_mean".
        scale_coordinate_columns (bool, optional): Whether to scale coordinate columns using
            MinMaxScaler. Defaults to True.
        remove_current_well (bool, optional): Whether to exclude the current well from
            training data during estimation. Defaults to True.
        nearest_neighbours (Optional[int], optional): Number of nearest neighbors to consider.
            If None, uses all available points in the zone. Defaults to None.
        **kwargs: Additional keyword arguments passed to KNeighborsRegressor, such as
            'weights', 'p', 'n_jobs'.

    Returns:
        pd.DataFrame: The input query DataFrame with estimated parameter values filled in
            the parameter_column_name column.

    Raises:
        NotImplementedError: If an unsupported aggregation method is specified.

    Warns:
        UserWarning: If no calibration points are found for a specific zone.

    Note:
        - Parameter estimation is performed separately for each geological zone
        - If scaling is enabled, the same scaler fitted on training data is applied to query data
        - For zones without training data, parameter values remain as NaN with a warning logged
    """
    ids = df_query[id_column].to_numpy()
    if not (ids.shape[0] == 0 or (ids[0] == ids).all()):
        raise ValueError(
            f"This function is intended to be used per well. Please ensure that df_query contains data for a single well only. Values found: {ids.unique()}"
        )
    # Process kwargs and setup parameters for estimation
    current_well_df = None
    if remove_current_well:
        parameter_lookup = df_train.loc[df_train[id_column].ne(ids[0]), :]
    else:
        current_well_df = df_train.loc[df_train[id_column].eq(ids[0]), :]
        if current_well_df.empty:
            current_well_df = None
        parameter_lookup = df_train.loc[:, :]

    df_query = df_query.assign(**{parameter_column_name: np.nan})
    aggregation_axis = 0
    for zone, zone_df in df_query.groupby(zone_column_name, dropna=True):
        if current_well_df is not None:
            y_pred = current_well_df.loc[
                current_well_df[zone_column_name].eq(zone), parameter_column_name
            ].squeeze()
            if isinstance(y_pred, float):
                df_query.loc[zone_df.index, parameter_column_name] = y_pred
                continue

        zone_train = parameter_lookup.loc[
            parameter_lookup[zone_column_name].eq(zone), :
        ]
        if zone_train.empty:
            logger.warning(
                f"No calibration points were found for zone: {zone} in the provided calibration dataset. Cannot predict {parameter_column_name} for this zone!",
                stacklevel=2,
            )
            continue

        x_train, y_train = (
            zone_train[coordinate_columns].to_numpy(),
            zone_train[parameter_column_name].to_numpy(),
        )
        x_pred = zone_df[coordinate_columns].to_numpy()
        y_pred = None
        if nearest_neighbours is not None or aggregation_method == "weighted_mean":
            num_train_samples = len(x_train)
            aggregation_axis = 1
            if nearest_neighbours is None:
                n_neighbors = num_train_samples
            else:
                if nearest_neighbours > num_train_samples:
                    n_neighbors = num_train_samples
                    logger.warning(
                        f"Requested number of neighbors ({nearest_neighbours}) is greater than available calibration points ({num_train_samples}) in zone {zone}. Using {n_neighbors} neighbors instead.",
                        stacklevel=2,
                    )
                else:
                    n_neighbors = nearest_neighbours
            if scale_coordinate_columns:
                if num_train_samples < 2:
                    logger.warning(
                        f"Not enough calibration points ({num_train_samples}) in zone {zone} to scale coordinates! At least 2 points are required for scaling. Skipping scaling for this zone.",
                    )
                else:
                    scaler = MinMaxScaler()
                    x_train = scaler.fit_transform(x_train)
                    x_pred = scaler.transform(zone_df[coordinate_columns].to_numpy())
            else:
                x_pred = zone_df[coordinate_columns].to_numpy()

            # Define the KNN model
            knn = KNeighborsRegressor(
                n_neighbors=n_neighbors,
                weights=kwargs.get("weights", "distance"),
                metric=distance_metric,
                metric_params=kwargs.get("metric_params", None),
                p=kwargs.get("p", 2),
                n_jobs=kwargs.get("n_jobs", -1),
            )
            knn.fit(x_train, y_train)

            if aggregation_method == "weighted_mean":
                y_pred = knn.predict(x_pred)
            else:
                indices = knn.kneighbors(x_pred, return_distance=False)
                calibration_point_parameters = y_train[indices]
        else:
            calibration_point_parameters = y_train

        if y_pred is None:
            if aggregation_method == "mean":
                y_pred = np.mean(calibration_point_parameters, axis=aggregation_axis)
            elif aggregation_method == "median":
                y_pred = np.median(calibration_point_parameters, axis=aggregation_axis)
            elif callable(aggregation_method):
                y_pred = aggregation_method(calibration_point_parameters)
            else:
                raise NotImplementedError(
                    f"Aggregation method '{aggregation_method}' is not implemented."
                )

        df_query.loc[zone_df.index, parameter_column_name] = y_pred

    return df_query
