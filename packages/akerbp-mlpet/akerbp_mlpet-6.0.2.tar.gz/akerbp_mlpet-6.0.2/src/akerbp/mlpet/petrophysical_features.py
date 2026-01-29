# ruff: noqa: N802
# ruff: noqa: N803
import logging
from typing import List, Optional

import numpy as np
import pandas as pd

from akerbp.mlpet import utilities

logger = logging.getLogger(__name__)


def guess_BS_from_CALI(
    df: pd.DataFrame,
    standard_bitsizes: Optional[List[float]] = None,
) -> pd.DataFrame:
    """
    Guess bitsize from CALI, given the standard bitsizes

    Args:
        df (pd.DataFrame): dataframe to preprocess

    Keyword Args:
        standard_bitsizes (ndarray): Numpy array of standardized bitsizes to
            consider. Defaults to::

                np.array([6, 8.5, 9.875, 12.25, 17.5, 26])

    Returns:
        pd.DataFrame: preprocessed dataframe

    """
    if standard_bitsizes is None:
        standard_bitsizes = [6, 8.5, 9.875, 12.25, 17.5, 26]
    bitsize_array = np.array(standard_bitsizes)
    edges = (bitsize_array[1:] + bitsize_array[:-1]) / 2
    edges = np.concatenate([[-np.inf], edges, [np.inf]])
    df.loc[:, "BS"] = pd.cut(df["CALI"], edges, labels=bitsize_array)
    df = df.astype({"BS": np.float64})
    return df


def calculate_CALI_BS(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates CALI-BS assuming at least CALI is provided in the dataframe
    argument. If BS is not provided, it is estimated using the
    :py:meth:`guess_BS_from_CALI <akerbp.mlpet.feature_engineering.guess_BS_from_CALI>`
    method from this module.

    Args:
        df (pd.DataFrame): The dataframe to which CALI-BS should be added.

    Raises:
        ValueError: Raises an error if neither CALI nor BS are provided

    Returns:
        pd.DataFrame: Returns the dataframe with CALI-BS as a new column
    """
    drop_BS = False  # noqa: N806
    if "CALI" in df.columns:
        if "BS" not in df.columns:
            drop_BS = True  # noqa: N806
            df = guess_BS_from_CALI(df)
        df["CALI-BS"] = df["CALI"] - df["BS"]
    else:
        raise ValueError(
            "Not possible to generate CALI-BS. At least CALI needs to be present in the dataset."
        )

    if drop_BS:
        df = df.drop(columns=["BS"])

    return df


def calculate_AI(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates AI from DEN and AC according to the following formula::

        AI = DEN * ((304.8 / AC) ** 2)

    Args:
        df (pd.DataFrame): The dataframe to which AI should be added.

    Raises:
        ValueError: Raises an error if neither DEN nor AC are provided

    Returns:
        pd.DataFrame: Returns the dataframe with AI as a new column
    """
    if {"DEN", "AC"}.issubset(set(df.columns)):
        df["AI"] = df["DEN"] * (304.8 / df["AC"])
    else:
        raise ValueError(
            "Not possible to generate AI as DEN and AC are not present in the dataset."
        )
    return df


def calculate_LI(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates LI from LFI according to the following formula::

        LI = ABS(ABS(LFI) - LFI) / 2

    If LFI is not in the provided dataframe, it is calculated using the
    calculate_LFI method of this module.

    Args:
        df (pd.DataFrame): The dataframe to which LI should be added.

    Raises:
        ValueError: Raises an error if neither NEU nor DEN or LFI are provided

    Returns:
        pd.DataFrame: Returns the dataframe with LI as a new column
    """
    if "LFI" in df.columns:
        pass
    elif {"NEU", "DEN"}.issubset(set(df.columns)):
        df = calculate_LFI(df)
    else:
        raise ValueError(
            "Not possible to generate LI as NEU and DEN or LFI are not present in dataset."
        )
    df["LI"] = abs(abs(df["LFI"]) - df["LFI"]) / 2
    df = df.drop(columns=["LFI"])
    return df


def calculate_FI(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates FI from LFI according to the following formula::

        FI = (ABS(LFI) + LFI) / 2

    If LFI is not in the provided dataframe, it is calculated using the
    calculate_LFI method of this module.

    Args:
        df (pd.DataFrame): The dataframe to which FI should be added.

    Raises:
        ValueError: Raises an error if neither NEU nor DEN or LFI are provided

    Returns:
        pd.DataFrame: Returns the dataframe with FI as a new column
    """
    if "LFI" in df.columns:
        pass
    elif {"NEU", "DEN"}.issubset(set(df.columns)):
        df = calculate_LFI(df)
    else:
        raise ValueError(
            "Not possible to generate FI as NEU and DEN or LFI are not present in dataset."
        )
    df["FI"] = (df["LFI"].abs() + df["LFI"]) / 2
    df = df.drop(columns=["LFI"])
    return df


def calculate_LFI(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Calculates LFI from NEU and DEN according to the following formula::

        LFI = 2.95 - ((NEU + 0.15) / 0.6) - DEN

    where:

        * LFI < -0.9 = 0
        * NaNs are filled with 0. unless fill_na is set to False

    Args:
        df (pd.DataFrame): The dataframe to which LFI should be added.

    Raises:
        ValueError: Raises an error if neither NEU nor DEN are provided

    Returns:
        pd.DataFrame: Returns the dataframe with LFI as a new column
    """
    fill_na: bool = kwargs.get("fill_na", True)
    if {"NEU", "DEN"}.issubset(set(df.columns)):
        df["LFI"] = 2.95 - ((df["NEU"] + 0.15) / 0.6) - df["DEN"]
        df.loc[df["LFI"] < -0.9, "LFI"] = 0
        if fill_na:
            df["LFI"] = df["LFI"].fillna(0)
    else:
        raise ValueError(
            "Not possible to generate LFI as NEU and/or DEN are not present in dataset."
        )
    return df


def calculate_RAVG(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates RAVG from RDEP, RMED, RSHA according to the following formula::

        RAVG = AVG(RDEP, RMED, RSHA), if at least two of those are present

    Args:
        df (pd.DataFrame): The dataframe to which RAVG should be added.

    Raises:
        ValueError: Raises an error if one or less resistivity curves are found
            in the provided dataframe

    Returns:
        pd.DataFrame: Returns the dataframe with RAVG as a new column
    """
    r_curves = [c for c in ["RDEP", "RMED", "RSHA"] if c in df.columns]
    if len(r_curves) > 1:
        df["RAVG"] = df[r_curves].mean(axis=1)
    else:
        raise ValueError(
            "Not possible to generate RAVG as there is only one or none resistivities curves in dataset."
        )
    return df


def calculate_VPVS(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates VPVS from ACS and AC according to the following formula::

        VPVS = ACS / AC

    Args:
        df (pd.DataFrame): The dataframe to which VPVS should be added.


    Raises:
        ValueError: Raises an error if neither ACS nor AC are found
            in the provided dataframe

    Returns:
        pd.DataFrame: Returns the dataframe with VPVS as a new column
    """
    if {"AC", "ACS"}.issubset(set(df.columns)):
        df["VPVS"] = df["ACS"] / df["AC"]
    else:
        raise ValueError(
            "Not possible to generate VPVS as both necessary curves (AC and"
            " ACS) are not present in dataset."
        )
    return df


def calculate_PR(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates PR from VP and VS or ACS and AC (if VP and VS are not found)
    according to the following formula::

        PR = (VP ** 2 - 2 * VS ** 2) / (2 * (VP ** 2 - VS ** 2))

    where:

        * VP = 304.8 / AC
        * VS = 304.8 / ACS

    Args:
        df (pd.DataFrame): The dataframe to which PR should be added.

    Raises:
        ValueError: Raises an error if none of AC, ACS, VP or VS are found
            in the provided dataframe

    Returns:
        pd.DataFrame: Returns the dataframe with PR as a new column
    """
    drop = False
    if not {"VP", "VS"}.issubset(set(df.columns)):
        if {"AC", "ACS"}.issubset(set(df.columns)):
            df = calculate_VP(df)
            df = calculate_VS(df)
            drop = True  # Don't want to add unwanted columns
        else:
            raise ValueError(
                "Not possible to generate PR as none of the neccessary curves "
                "(AC, ACS or VP, VS) are present in the dataset."
            )
    df["PR"] = (df["VP"] ** 2 - 2.0 * df["VS"] ** 2) / (
        2.0 * (df["VP"] ** 2 - df["VS"] ** 2)
    )
    if drop:
        df = df.drop(columns=["VP", "VS"])
    return df


def calculate_VP(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Calculates VP (if AC is found) according to the following formula::

        VP = 304.8 / AC

    Args:
        df (pd.DataFrame): The dataframe to which PR should be added.

    Raises:
        ValueError: Raises an error if AC is not found in the provided dataframe

    Returns:
        pd.DataFrame: Returns the dataframe with VP as a new column
    """
    if "AC" in df.columns:
        df["VP"] = 304.8 / df["AC"]
    else:
        raise ValueError("Not possible to generate VP as AC is not present in dataset.")
    return df


def calculate_VS(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Calculates VS (if ACS is found) according to the following formula::

        VS = 304.8 / ACS

    Args:
        df (pd.DataFrame): The dataframe to which PR should be added.

    Raises:
        ValueError: Raises an error if ACS is not found in the provided dataframe

    Returns:
        pd.DataFrame: Returns the dataframe with VS as a new column
    """
    if "ACS" in df.columns:
        df["VS"] = 304.8 / df["ACS"]
    else:
        raise ValueError(
            "Not possible to generate VS as ACS is not present in dataset."
        )
    return df


def calculate_diffRes(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Calculates the difference between two resistivity logs according to the following formula::

        diffRes = RDEP - RMED

    Args:
        df (pd.DataFrame): The dataframe to which diffRes should be added.
        left (str): The name of the left resistivity log. Defaults to None
        right (str): The name of the right resistivity log. Defaults to None
        fill_na (float): An option to fill the NaN values with the provided value. Defaults to None

    Note:
        The returned column is named according to the following convention::

            <left>-<right>

    Returns:
        pd.DataFrame: Returns the dataframe with the calculated column
    """
    left = kwargs.get("left", None)
    right = kwargs.get("right", None)
    fill_na = kwargs.get("fill_na", None)
    if left is None or right is None:
        logger.warning(
            "Not possible to calculate_diffRes because the kwargs left and/or "
            "right are not provided. Returning the dataframe without any changes.",
            stacklevel=2,
        )
        return df

    if left not in df.columns or right not in df.columns:
        raise ValueError(
            f"Not possible to generate diffRes as {left} and/or {right} are not present in dataframe."
        )

    df[f"{left}-{right}"] = df[left] - df[right]
    if fill_na is not None:
        df[f"{left}-{right}"] = df[f"{left}-{right}"].fillna(fill_na)

    return df


def calculate_empirical_salinity_or_water_resistivity(
    df: pd.DataFrame, **kwargs
) -> pd.DataFrame:
    """
    Calculate NaCl concentration from water resistivity or water resistivity from NaCl concentration
    using the Bateman and Konen method (1977).

    This function uses an empirical relationship to estimate either:
    1. NaCl concentration (salinity) from formation water resistivity (Rw) and well temperature, or
    2. Formation water resistivity (Rw) from NaCl concentration and well temperature

    The Bateman and Konen method:
        Rw @ 75 deg F = 0.0123 + (3647.5 / (salinity ^ 0.955))

    It calculates water resistivity (Rw) at 75 deg F (approx 23.889 °C) based on salinity.

    To convert that water resisitivity to a different temperature T (in °C), the following adjustment is made:

        Rw @ T = Rw @ 75 deg F * ((23.889 + 21.5) / (T + 21.5))

    Where T is temperature in °C, Rw is water resistivity in ohm-m, and NaCl is in g/L.

    Parameters:
        rw_column_name (str, optional): The name of the column containing water resistivity values (ohm-m).
            Provide this to calculate NaCl concentration.
        salinity_column_name (str, optional): The name of the column containing NaCl concentration values (g/L).
            Provide this to calculate water resistivity.
        welltemp_column_name (str): The name of the column containing well temperature values (°C).

    Returns:
        pd.DataFrame: DataFrame with either:
            - 'NaCl' column (salinity in g/L) if calculating from resistivity
            - 'RW' column (water resistivity in ohm-m) if calculating from salinity

    Raises:
        ValueError: If neither or both rw_column_name and salinity_column_name are provided,
                   or if required columns are missing from the dataframe, or if welltemp_column_name
                   is not provided.
    """
    rw_column_name = kwargs.get("rw_column_name", None)
    salinity_column_name = kwargs.get("salinity_column_name", None)
    welltemp_column_name = kwargs.get("welltemp_column_name", None)

    # Input checks
    if rw_column_name is not None and salinity_column_name is None:
        calculate_salinity = True
    elif rw_column_name is None and salinity_column_name is not None:
        calculate_salinity = False
    elif rw_column_name is None and salinity_column_name is None:
        raise ValueError(
            "Not possible to generate NaCl or Rw as neither rw_column_name nor "
            "salinity_column_name are provided."
        )
    elif rw_column_name is not None and salinity_column_name is not None:
        raise ValueError(
            "Don't know whether to calculate NaCl or Rw as both rw_column_name and "
            "salinity_column_name are provided. Please provide only one of them."
        )
    if calculate_salinity:
        if rw_column_name not in df.columns:
            raise ValueError(
                f"Not possible to generate NaCl as {rw_column_name} is not present in dataframe."
            )
    else:
        if salinity_column_name not in df.columns:
            raise ValueError(
                f"Not possible to generate Rw as {salinity_column_name} is not present in dataframe."
            )
    if welltemp_column_name is None:
        raise ValueError(
            "Not possible to generate NaCl or Rw as welltemp_column_name is not provided."
        )
    if welltemp_column_name not in df.columns:
        raise ValueError(
            f"Not possible to generate NaCl or Rw as {welltemp_column_name} is not present in dataframe."
        )

    # Constants
    bateman_konen_intercept = 0.0123
    bateman_konen_gradient = 3647.5
    lab_temperature = 45.39  # 23.889 + 21.5 rounded up
    bateman_konen_power = 0.955

    # Shift temperature
    formation_temperature = df[welltemp_column_name] + 21.5

    if calculate_salinity:
        # Calculate denominator
        denominator = (
            df[rw_column_name] * formation_temperature / lab_temperature
        ) - bateman_konen_intercept

        # Remove values where denominator is less than or equal to 0
        denominator = denominator.mask(denominator <= 0, np.nan)

        # Calculate NaCl
        # Convert from mg/L to g/L
        df.loc[:, "NaCl"] = (bateman_konen_gradient / denominator) ** (
            1 / bateman_konen_power
        ) / 1000
    else:
        # Invert the formula to calculate Rw from NaCl
        df.loc[:, "RW"] = (
            bateman_konen_intercept
            + (
                bateman_konen_gradient
                / (df[salinity_column_name] * 1000.0) ** bateman_konen_power
            )
        ) * (lab_temperature / formation_temperature)

    return df


def calculate_weighted_water_resistivity(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Calculate the formation water resistivity (Rw) for a given NaCl concentration
    and well temperature.

    Parameters:
        nacl_column_name (str): The name of the column containing NaCl concentration values (g/L).
        welltemp_column_name (str): The name of the column containing well temperature values (°C).

    Returns:
        pd.DataFrame: DataFrame with Rw column (formation water resistivity - ohm-m).
    """
    # Required columns
    id_column = kwargs.get("id_column", None)
    rw_column_name = kwargs.get("rw_column_name", None)
    tvd_column_name = kwargs.get("tvd_column_name", "TVDBML")  # m
    zone_column_names = kwargs.get("zone_column_names", None)
    # Required df with calibration points
    rw_table = kwargs.get("rw_table", None)
    # Pseudo temp kwargs
    seabed_temperature = kwargs.get("seabed_temperature", 4)  # °C
    pseudo_temperature_gradient = kwargs.get(
        "pseudo_temperature_gradient", 3 / 100
    )  # °C/m

    # Input checks
    if id_column is None:
        raise ValueError("Not possible to generate Rw as id_column is not provided.")
    if rw_table is None:
        raise ValueError("Not possible to generate Rw as rw_table is not provided.")
    if tvd_column_name not in df.columns:
        raise ValueError(
            f"Not possible to generate Rw as {tvd_column_name} is not present in dataframe."
        )
    if tvd_column_name not in rw_table.columns:
        raise ValueError(
            f"Not possible to generate Rw as {tvd_column_name} is not present in rw_table."
        )
    if zone_column_names is None:
        raise ValueError(
            "Not possible to generate Rw as zone_column_names are not provided."
        )
    if zone_column_names is not None:
        for col in zone_column_names:
            if col not in df.columns:
                raise ValueError(
                    f"Not possible to generate Rw as {col} is not present in dataframe."
                )
            if col not in rw_table.columns:
                raise ValueError(
                    f"Not possible to generate Rw as {col} is not present in rw_table."
                )

    if rw_column_name is None:
        raise ValueError(
            "Not possible to generate Rw as rw_column_name is not provided."
        )

    # Start by calculating pseudo temperature
    df = df.assign(
        PSEUDO_TEMPERATURE=seabed_temperature
        + (df[tvd_column_name] * pseudo_temperature_gradient)
    )
    rw_table = rw_table.assign(
        PSEUDO_TEMPERATURE=seabed_temperature
        + (rw_table[tvd_column_name] * pseudo_temperature_gradient)
    )

    # Then calculate pseudo_salinity
    rw_table = calculate_empirical_salinity_or_water_resistivity(
        rw_table,
        **{
            "rw_column_name": rw_column_name,
            "welltemp_column_name": "PSEUDO_TEMPERATURE",
        },
    )

    # Now calculate pseudo salinity based on weighted nearest neighbours
    for _, well_df in df.groupby(id_column):
        well_df = well_df.assign(PSEUDO_SALINITY=np.nan)
        for zone_column_name in zone_column_names:
            well_df = utilities.estimate_parameter(
                well_df,
                rw_table,
                id_column=id_column,
                parameter_column_name="NaCl",
                zone_column_name=zone_column_name,
                coordinate_columns=kwargs.get(
                    "coordinate_columns", ["X_TRAJECTORY", "Y_TRAJECTORY"]
                ),
                distance_metric=kwargs.get("distance_metric", "nan_euclidean"),
                # Use squared euclidean distance
                metric_params=kwargs.get("distance_metric_params", {"squared": True}),
                weights=kwargs.get("weights", "distance"),
                aggregation_method=kwargs.get("aggregation_method", "weighted_mean"),
                scale_coordinate_columns=kwargs.get("scale_coordinate_columns", True),
                remove_current_well=kwargs.get("remove_current_well", True),
                nearest_neighbours=kwargs.get("nearest_neighbours", None),
            )
            well_df["PSEUDO_SALINITY"] = well_df["PSEUDO_SALINITY"].combine_first(
                well_df["NaCl"]
            )
            well_df = well_df.drop(columns=["NaCl"])
        df.loc[well_df.index, "PSEUDO_SALINITY"] = well_df["PSEUDO_SALINITY"]

    # Finally calculate Rw based on pseudo salinity and pseudo temperature
    df = calculate_empirical_salinity_or_water_resistivity(
        df,
        **{
            "salinity_column_name": "PSEUDO_SALINITY",
            "welltemp_column_name": "PSEUDO_TEMPERATURE",
        },
    )
    df = df.drop(columns=["PSEUDO_TEMPERATURE", "PSEUDO_SALINITY"])

    return df
