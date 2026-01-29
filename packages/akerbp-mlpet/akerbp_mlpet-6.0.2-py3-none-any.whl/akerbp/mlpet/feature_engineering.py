import logging
import sqlite3
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

import akerbp.mlpet.petrophysical_features as petro
import akerbp.mlpet.utilities as utilities

logger = logging.getLogger(__name__)


def add_log_features(
    df: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    # TODO: Remove the + 1 in the logs? Should negative values be returned as np.nan or 0?
    """
    Creates columns with log10 of curves. All created columns are suffixed with
    '_log'. All negative values are set to zero and 1 is added to all values. In
    other words, this function is synonymous of numpy's log1p.

    Args:
        df (pd.DataFrame): dataframe with columns to calculate log10 from

    Keyword Args:
        log_features (list, optional): list of column names for the columns that should be
            loggified. Defaults to None
        num_filler (float, optional): value to fill NaNs with. Defaults to None

    Returns:
        pd.DataFrame: New dataframe with calculated log columns
    """
    log_features: Optional[List[str]] = kwargs.get("log_features", None)
    num_filler: Optional[float] = kwargs.get("num_filler", None)
    if log_features is not None:
        if num_filler is not None:
            nf_masks = {}
            for col in log_features:
                if pd.isna(num_filler):
                    mask = df[col].isna()
                else:
                    mask = df[col].eq(num_filler)
                nf_masks[col] = mask
                df.loc[nf_masks[col], col] = np.nan
        log_cols = [col + "_log" for col in log_features]
        df[log_cols] = np.log10(df[log_features].clip(lower=0) + 1)
        if num_filler is not None:
            for col, mask in nf_masks.items():
                df.loc[mask, col] = num_filler  # Set back
                df.loc[mask, col + "_log"] = num_filler  # Ensure log corresponds
    return df


def add_gradient_features(
    df: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    """
    Creates columns with gradient of curves. All created columns are suffixed with
    '_gradient'.

    Args:
        df (pd.DataFrame): dataframe with columns to calculate gradient from
    Keyword Args:
        gradient_features (list, optional): list of column names for the columns
            that gradient features should be calculated for. Defaults to None.

    Returns:
        pd.DataFrame: New dataframe with calculated gradient feature columns
    """
    gradient_features: Optional[List[str]] = kwargs.get("gradient_features", None)
    if gradient_features is not None:
        gradient_cols = [col + "_gradient" for col in gradient_features]
        for i, feature in enumerate(gradient_features):
            df[gradient_cols[i]] = np.gradient(df[feature])
    return df


def add_rolling_features(
    df: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    """
    Creates columns with centered window/rolling features of curves. All created columns
    are suffixed with '_window_mean' / '_window_max' / '_window_min'.

    Args:
        df (pd.DataFrame): dataframe with columns to calculate rolling features from

    Keyword Args:
        rolling_features (list): columns to apply rolling features to. Defaults to None.
        depth_column (str): The name of the column to use to determine the sampling
            rate. Without this kwarg no rolling features are calculated.
        window (float): The window size to use for calculating the rolling
            features. **The window size is defined in distance**! The sampling rate
            is determined from the depth_column kwarg and used to transform the window
            size into an index based window. If this is not provided, no rolling features are calculated.
        calculate_mean (bool): Whether to calculate the mean of the window. Defaults to True.
        calculate_max (bool): Whether to calculate the max of the window. Defaults to True.
        calculate_min (bool): Whether to calculate the min of the window. Defaults to True.
        calculate_var (bool): Whether to calculate the variance of the window. Defaults to False.
        calculate_norm_dist (bool): Whether to calculate the normalized distance the current point is from the window min and max. Defaults to False.
            calculate_min and calculate_max must be True for this to work.

    Returns:
        pd.DataFrame: New dataframe with calculated rolling feature columns
    """
    rolling_features: Optional[List[str]] = kwargs.get("rolling_features", None)
    window: Optional[float] = kwargs.get("window", None)
    depth_column: Optional[str] = kwargs.get("depth_column", None)
    calculate_mean: bool = kwargs.get("calculate_mean", True)
    calculate_max: bool = kwargs.get("calculate_max", True)
    calculate_min: bool = kwargs.get("calculate_min", True)
    calculate_var: bool = kwargs.get("calculate_var", False)
    calculate_norm_dist: bool = kwargs.get("calculate_norm_dist", False)
    if rolling_features is not None and window is not None and depth_column is not None:
        curves_to_drop = []
        sampling_rate = utilities.calculate_sampling_rate(df[depth_column])
        window_size = int(window / sampling_rate)
        if calculate_mean:
            mean_cols = [col + "_window_mean" for col in rolling_features]
            df[mean_cols] = (
                df[rolling_features]
                .rolling(center=True, window=window_size, min_periods=1)
                .mean()
            )
        if calculate_min or calculate_norm_dist:
            min_cols = [col + "_window_min" for col in rolling_features]
            df[min_cols] = (
                df[rolling_features]
                .rolling(center=True, window=window_size, min_periods=1)
                .min()
            )
            if not calculate_min:
                curves_to_drop.extend(min_cols)
        if calculate_max or calculate_norm_dist:
            max_cols = [col + "_window_max" for col in rolling_features]
            df[max_cols] = (
                df[rolling_features]
                .rolling(center=True, window=window_size, min_periods=1)
                .max()
            )
            if not calculate_max:
                curves_to_drop.extend(max_cols)
        if calculate_var:
            var_cols = [col + "_window_var" for col in rolling_features]
            df[var_cols] = (
                df[rolling_features]
                .rolling(center=True, window=window_size, min_periods=1)
                .var()
            )
        if calculate_norm_dist:
            for col in rolling_features:
                df[col + "_window_norm_dist"] = (df[col] - df[col + "_window_min"]) / (
                    df[col + "_window_max"] - df[col + "_window_min"]
                )
        if curves_to_drop:
            df = df.drop(columns=curves_to_drop, errors="ignore")
    return df


def add_sequential_features(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Adds n past values of columns (for sequential models modelling). All created
    columns are suffixed with '_1' / '_2' / ... / '_n'.

    Args:
        df (pd.DataFrame): dataframe to add time features to

    Keyword Args:
        sequential_features (list, optional): columns to apply shifting to. Defaults to None.
        shift_size (int, optional): Size of the shifts to calculate. In other words, number of past values
            to include. If this is not provided, no sequential features are calculated.

    Returns:
        pd.DataFrame: New dataframe with sequential gradient columns
    """
    sequential_features: Optional[List[str]] = kwargs.get("sequential_features", None)
    shift_size: Optional[int] = kwargs.get("shift_size", None)
    if sequential_features and shift_size is not None:
        for shift in range(1, shift_size + 1):
            sequential_cols = [f"{c}_{shift}" for c in sequential_features]
            df[sequential_cols] = df[sequential_features].shift(periods=shift)
    return df


def add_petrophysical_features(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Creates petrophysical features according to relevant heuristics/formulas.

    The features created are as follows (each one can be toggled on/off via the
    'petrophysical_features' kwarg)::

        - VPVS = ACS / AC
        - PR = (VP ** 2 * 2 * VS ** 2) / (2 * (VP ** 2 * VS ** 2)) where
        - VP = 304.8 / AC
        - VS = 304.8 / ACS
        - RAVG = AVG(RDEP, RMED, RSHA), if at least two of those are present
        - LFI = 2.95 * ((NEU + 0.15) / 0.6) * DEN, and
            - LFI < *0.9 = 0
            - NaNs are filled with 0
        - FI = (ABS(LFI) + LFI) / 2
        - LI = ABS(ABS(LFI) * LFI) / 2
        - AI = DEN * ((304.8 / AC) ** 2)
        - CALI*BS = CALI * BS, where
            - BS is calculated using the guess_BS_from_CALI function from this
            module it is not found in the pass dataframe
        - VSH = Refer to the calculate_VSH docstring for more info on this
        - diffRes = Refer to the calculate_diffRes docstring for more info on this

    Args:
        df (pd.DataFrame): dataframe to which add features from and to

    Keyword Args:
        petrophysical_features (list): A list of all the petrophysical features
            that should be created (see above for all the potential features
            this method can create). This defaults to an empty list (i.e. no
            features created).

    Returns:
        pd.DataFrame: dataframe with added features
    """
    petrophysical_features: Optional[List[str]] = kwargs.get(
        "petrophysical_features", None
    )

    if petrophysical_features is not None:
        # Calculate relevant features
        if "VP" in petrophysical_features:
            df = petro.calculate_VP(df, **kwargs)

        if "VS" in petrophysical_features:
            df = petro.calculate_VS(df, **kwargs)

        if "VPVS" in petrophysical_features:
            df = petro.calculate_VPVS(df)

        if "PR" in petrophysical_features:
            df = petro.calculate_PR(df)

        if "RAVG" in petrophysical_features:
            df = petro.calculate_RAVG(df)

        if "LFI" in petrophysical_features:
            df = petro.calculate_LFI(df, **kwargs)

        if "FI" in petrophysical_features:
            df = petro.calculate_FI(df)

        if "LI" in petrophysical_features:
            df = petro.calculate_LI(df)

        if "AI" in petrophysical_features:
            df = petro.calculate_AI(df)

        if "CALI-BS" in petrophysical_features:
            df = petro.calculate_CALI_BS(df)

        if "VSH" in petrophysical_features:
            df = petro.calculate_VSH(df, **kwargs)

        if "diffRes" in petrophysical_features:
            df = petro.calculate_diffRes(df, **kwargs)

    return df


def add_zonation_tops(
    df: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    """
    Adds zonation columns based on a dataframe containing lithostratographic unit tops.

    This function adds geological zonation information (formations, groups, etc.) to the input
    dataframe by matching depth intervals with lithostratographic unit data. The function
    performs SQL-based joins to efficiently map depth ranges to geological units.

    It does NOT however enforce a hierarchical standard between the different lsu_types.
    Refer to the normalize_zonation_columns utility for this.

    Warning:
        If the well is not found in the tops dataframe, the code will log a warning
        and continue to the next well without adding zonation data for that well.

    Example:
        For a tops_df containing lithostratographic units::

            tops_df = pd.DataFrame({
                'WELL_ID': ['31/6-6', '31/6-6', '31/6-6'],
                'TOP_MD': [336.0, 531.0, 650.0],
                'BASE_MD': [531.0, 650.0, 798.0],
                'LSU_NAME': ['Nordland Group', 'Hordaland Group', 'Balder Formation'],
                'LSU_TYPE': ['GROUP', 'GROUP', 'FORMATION'],
            })

        The function will classify depths in well 31/6-6:
        - Depths 336-531: Nordland Group
        - Depths 531-650: Hordaland Group
        - Depths 650-798: Balder Formation

    Args:
        df (pd.DataFrame): The dataframe to which zonation columns should be added.
            Must contain the specified depth column and well ID column (if provided).

        id_column (str, optional): The name of the column containing well IDs. If None,
            zonation will not be applied. Default is None.
            mappings. Default is "DEPTH".
        tops_df (pd.DataFrame): A dataframe containing lithostratographic unit information.
            Must contain columns: [id_column, 'TOP_MD', 'BASE_MD', 'LSU_NAME', 'LSU_TYPE', 'PARENT'].

    Raises:
        ValueError: If depth_column is not in df.columns, if tops_df is empty,
            or if required columns are missing from tops_df.

    Returns:
        pd.DataFrame: Original dataframe with additional columns for each LSU_TYPE
            (e.g., 'FORMATION', 'GROUP')
    """
    id_column: Optional[str] = kwargs.get("id_column", None)
    depth_column: str = kwargs.get("depth_column", "DEPTH")
    tops_df: pd.DataFrame = kwargs.get("tops_df", pd.DataFrame())

    if id_column is None:
        raise ValueError(
            "Cannot add formations and groups metadata without an id_column! "
            "Please provide an id_column kwarg to the add_formations_and_groups "
            " specifying which column to use as the well identifier."
        )

    if depth_column not in df.columns:
        raise ValueError(
            "Cannot add formations and groups metadata without a depth_column! "
            "Please provide a depth_column kwarg to the add_formations_and_groups "
            " specifying which column to use as the depth column."
        )

    if tops_df.empty:
        raise ValueError(
            "No tops information was provided! Please provide a tops_df "
            "kwarg to the add_formations_and_groups function."
        )
    # Validate the tops dataframe
    required_columns = [
        id_column,
        "TOP_MD",
        "BASE_MD",
        "LSU_NAME",
        "LSU_TYPE",
        "PARENT",
    ]
    for col in required_columns:
        if col not in tops_df.columns:
            raise ValueError(
                f"The provided tops_df does not contain the required column {col}! "
                f"Please provide a tops_df containing the following columns: {required_columns}"
            )

    # Initialize the output columns
    # initiate a conn for executing sql query for special types of joins not
    # supported by pandas
    conn = sqlite3.connect(":memory:")
    df.to_sql("well_df", conn, index=False, if_exists="replace")
    df.loc[:, tops_df["LSU_TYPE"].unique().tolist() + ["PARENT"]] = pd.NA
    for lsu_type, lsu_df in tops_df.groupby("LSU_TYPE"):
        cols_to_add = [lsu_type]
        if lsu_type.upper().strip() == "GROUP":
            cols_to_add.append("PARENT")
        # We need to drop rows where we don't have a top or base md because it is unclear
        # how to resolve this. Filling with the start or the end of the well is not safe
        lsu_df = lsu_df.rename(
            columns={"LSU_NAME": lsu_type},
            errors="ignore",
        ).dropna(subset=["TOP_MD", "BASE_MD"], how="any")
        lsu_df.to_sql("lsu_df", conn, index=False, if_exists="replace")
        well_df_with_tops = pd.read_sql_query(
            f"""
            SELECT w.*, l.[{"], l.[".join(cols_to_add)}]
            FROM well_df w
            LEFT JOIN lsu_df l
            ON (w.{id_column} = l.{id_column} AND w.[{depth_column}] >= l.TOP_MD AND w.[{depth_column}] < l.BASE_MD)
            """,
            conn,
        )
        df.loc[:, cols_to_add] = well_df_with_tops[cols_to_add]

    conn.close()
    df = df.rename(columns={"PARENT": "SYSTEM"}, errors="ignore")

    return df


def add_tophole_metadata(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Add tophole metadata to a DataFrame containing wellbore data.

    This function merges tophole metadata (coordinates, well names, etc.) with the input
    DataFrame. It first attempts to merge on the wellbore level using the specified ID
    column. For records that don't match, it falls back to merging on the well level
    by extracting the well name from the wellbore ID for the passed dataframe. The well_column_name
    is expected to exist in the passed tophole_df.

    Args:
        df (pd.DataFrame): Input DataFrame containing wellbore data to be enriched.
        **kwargs: Keyword arguments containing:
            id_column (str): Name of the column in df to use as wellbore identifier.
            tophole_columns (list): List of columns from tophole_df to include in the output.
            tophole_df (pd.DataFrame): DataFrame containing tophole metadata with
                required columns: id_column, well_column_name, and tophole_columns.

    Returns:
        pd.DataFrame: Input DataFrame enriched with tophole metadata. The "X" and "Y"
            columns from tophole_df are renamed to "X_TOPHOLE" and "Y_TOPHOLE".

    Raises:
        ValueError: If id_column is not provided in kwargs.
        ValueError: If well_column_name is not provided in kwargs.
        ValueError: If tophole_columns is not provided in kwargs.
        ValueError: If tophole_df is not provided or is empty.
        ValueError: If tophole_df is missing any required columns.

    Note:
        For wellbores that don't have direct matches, the function attempts to match
        on well level by taking the first part of the wellbore ID. When multiple
        tophole entries exist for the same well, statistics on coordinate variation
        are logged and duplicates are dropped.
    """
    id_column = kwargs.get("id_column", None)
    tophole_columns = kwargs.get("tophole_columns", None)
    tophole_df: pd.DataFrame = kwargs.get("tophole_df", pd.DataFrame())

    if id_column is None:
        raise ValueError(
            "Cannot add tophole metadata without an id_column! "
            "Please provide an id_column kwarg to the add_tophole_metadata "
            " specifying which column to use as the well identifier."
        )

    if tophole_columns is None:
        raise ValueError(
            "Cannot add tophole metadata without specifying which columns to include! "
            "Please provide a tophole_columns kwarg to the add_tophole_metadata "
            "function."
        )

    if tophole_df.empty:
        raise ValueError(
            "No tophole metadata was provided! Please provide a tophole_df "
            "kwarg to the add_tophole_metadata function."
        )

    # Validate the tops dataframe
    required_columns = [
        id_column,
        *tophole_columns,
    ]
    for col in required_columns:
        if col not in tophole_df.columns:
            raise ValueError(
                f"The provided tophole_df does not contain the required column {col}! "
                f"Please provide a tophole_df containing the following columns: {required_columns}"
            )

    # The tophole table only contains wellbore IDs, so we need to remove any sidetrack
    # info from the wellbore ids
    wellbore_id_map = {
        w: utilities.remove_sidetrack_from_wellbore_name(w.strip())
        for w in df[id_column].unique()
    }
    new_col_name = f"{id_column}_SIDETRACK_CLEANED"
    df[new_col_name] = df[id_column].map(wellbore_id_map)
    if df[new_col_name].isna().any():
        raise ValueError(
            "NaNs were detected in your id_column! Cannot proceed with adding tophole metadata."
        )

    # Merge new_col_name
    wellbore_merge = df.merge(
        tophole_df[[id_column, *tophole_columns]].rename(
            columns={id_column: new_col_name}
        ),
        on=new_col_name,
        how="left",
        validate="m:1",
    )

    # Check for missing matches
    still_missing_mask = wellbore_merge[tophole_columns[0]].isna()
    if still_missing_mask.any():
        still_missing = wellbore_merge.loc[still_missing_mask, id_column].unique()
        logger.warning(
            f"Could not find matches for the following {len(still_missing)} wellbores: {still_missing}",
            stacklevel=2,
        )

    return wellbore_merge.drop(columns=[new_col_name])


def add_trajectories(
    df: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    """Add trajectory data to the provided dataframe.
    The type of trajectory data added is governed by the keyword argument 'trajectory_type', and
    the default behaviour is to add both wellbore coordinates and vertical depths.

    Args:
        df (pd.DataFrame): input data. Must contain the columns specified in the id_column and depth_column kwargs.

    Keyword Args:
        depth_column (str): Name of the column containing the measured depth values
            Defaults to None
        id_column (str): Name of the column containing the well names
            Defaults to None
        trajectory_columns (List[str]): List of trajectory columns to interpolate and add to the input dataframe.
        trajectory_df pd.DataFrame: A dataframe containing trajectory data with the following columns:
            - id_column: Name of the well (should match the values in the id_column of
                the input dataframe)
            - depth_column: The depth column in the mapping dataframe to use for interpolation
            - trajectory_columns: List of trajectory columns to interpolate and add to the input dataframe

            For example::

                trajectory_df = pd.DataFrame({
                    'WELL': ['well-name', 'well-name', 'well-name', ...],
                    'DEPTH': [0.0, 1.0, 2.0, ...],
                    'X': [0.0, 1.0, 2.0, ...],
                    'Y': [0.0, 1.0, 2.0, ...],
                    'TVD': [0.0, 1.0, 2.0, ...],
                })

                This would interpolate the x, y, and tvd columns for the well-name well
                based on the depth_column column in the dataframe and the corresponding
                depth_column in the mapping.

    Raises:
        ValueError: Due to missing or invalid specification of keyword arguments
        Exception: Generic exception if something fails in retrieval of the trajectory data from CDF

    Returns:
        pd.DataFrame: output data with trajectory columns added
    """
    depth_column: Optional[str] = kwargs.get("depth_column", None)
    id_column: Optional[str] = kwargs.get("id_column", None)
    trajectory_columns: Optional[List[str]] = kwargs.get("trajectory_columns", None)
    trajectory_df: pd.DataFrame = kwargs.get("trajectory_df", pd.DataFrame())

    if id_column is None:
        raise ValueError("No id_column kwarg provided!")
    if depth_column is None:
        raise ValueError("No depth_column kwarg provided!")
    if trajectory_columns is None or not trajectory_columns:
        raise ValueError("No trajectory_columns kwarg provided!")

    if trajectory_df.empty:
        raise ValueError(
            "No trajectory_df was provided! Please provide a trajectory_df "
            "kwarg to the add_trajectory_data function."
        )
    for c in trajectory_columns + [id_column, depth_column]:
        if c not in trajectory_df:
            raise ValueError(
                f"The provided trajectory_df does not contain the required column {c}! "
                f"Please provide a trajectory_df containing the following columns: {[id_column, depth_column] + trajectory_columns}"
            )

    for c in [id_column, depth_column]:
        if c not in df:
            raise ValueError(
                f"The provided dataframe does not contain the required column {c}! "
                f"Please provide a dataframe containing the following columns: {[id_column, depth_column]}"
            )

    # Initialize trajectory columns with float64 dtype and NaN values
    df.loc[:, trajectory_columns] = pd.NA
    for well, well_df in df.groupby(id_column):
        well_trajectories = trajectory_df.loc[trajectory_df[id_column] == well]
        if well_trajectories.empty:
            logger.warning(
                f"Could not find trajectory data for well {well} in the provided trajectory_df! Skipping "
                "trajectory interpolation for this well.",
                stacklevel=2,
            )
            continue
        x = well_trajectories[depth_column].to_numpy()
        y = well_trajectories[trajectory_columns].to_numpy()
        xp = well_df[depth_column].to_numpy()
        interpolator = interp1d(x, y, axis=0, fill_value="extrapolate")
        df.loc[well_df.index, trajectory_columns] = interpolator(xp)
    return df
