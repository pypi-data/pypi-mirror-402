"""
Train test validation split function
"""

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals

from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def train_test_validation_split(
    data: pd.DataFrame,
    col_target: str,
    # Parametry dla podziału procentowego
    train_percent: float | None = None,
    test_percent: float | None = None,
    validate_percent: float | None = None,
    random_state: int = 2024,
    col_order: str | None = None,
    task: str = "reg",
    # Parametry dla podziału według miesięcy
    train_months: list[int] | None = None,
    test_months: list[int] | None = None,
    val_months: list[int] | None = None,
    col_date: str | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Splits a Pandas dataframe into three subsets (train, val, and test).

    Supports two modes:
    1. PERCENTAGE MODE: Uses sklearn's train_test_split with percentage splits
    2. MONTHLY MODE: Splits data based on month numbers from a date column

    Mode is automatically selected based on provided parameters:
    - If train_months is provided -> MONTHLY MODE
    - Otherwise -> PERCENTAGE MODE

    Parameters
    ----------
    data: pd.DataFrame
        Data to split
    col_target: str
        Name of column target

    PERCENTAGE MODE parameters:
    ---------------------------
    train_percent: float (0,1) | None
        Percent of train data. Defaults to 0.7 if None in percentage mode.
    test_percent: float (0,1) | None
        Percent of test data. Defaults to 0.15 if None in percentage mode.
    validate_percent: float (0,1) | None
        Percent of validate data. Defaults to 0.15 if None in percentage mode.
    random_state: int
        Random state for reproducibility. Defaults to 2024.
    col_order: str | None
        Column to sort values for train/test/validation split by date.
        If provided, standard split is done without shuffling.
    task: str
        Type of task - 'reg' for regression, 'bin' for binary classification,
        or 'multi' for multiclass classification. Defaults to "reg".

    MONTHLY MODE parameters:
    ------------------------
    train_months: list[int] | None
        List of month numbers (1-12) to include in training set
    test_months: list[int] | None
        List of month numbers (1-12) to include in test set
    val_months: list[int] | None
        List of month numbers (1-12) to include in validation set.
        If None in monthly mode, validation set will be empty.
    col_date: str | None
        Name of date column (e.g., 'ftd_date') from which to extract month numbers.
        Required for monthly mode.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]
        X_train : Training data features
        X_test : Test data features
        X_val : Validation data features
        y_train : Training data target
        y_test : Test data target
        y_val : Validation data target

    Raises
    ------
    ValueError
        Various validation errors depending on mode

    Examples
    --------
    # PERCENTAGE MODE
    >>> X_train, X_test, X_val, y_train, y_test, y_val = train_test_validation_split(
    ...     data=df,
    ...     col_target='remaining_ngr',
    ...     train_percent=0.7,
    ...     test_percent=0.15,
    ...     validate_percent=0.15,
    ...     task='reg'
    ... )

    # MONTHLY MODE
    >>> X_train, X_test, X_val, y_train, y_test, y_val = train_test_validation_split(
    ...     data=df,
    ...     col_target='remaining_ngr',
    ...     col_date='ftd_date',
    ...     train_months=[1, 2, 3, 4, 5, 6],
    ...     test_months=[7, 8],
    ...     val_months=[9, 10]
    ... )
    """

    # Determine mode
    monthly_mode = train_months is not None

    if monthly_mode:
        return _split_by_months(
            data=data,
            col_target=col_target,
            col_date=col_date,
            train_months=train_months,
            test_months=test_months,
            val_months=val_months,
        )
    else:
        return _split_by_percentage(
            data=data,
            col_target=col_target,
            train_percent=train_percent if train_percent is not None else 0.7,
            test_percent=test_percent if test_percent is not None else 0.15,
            validate_percent=validate_percent if validate_percent is not None else 0.15,
            random_state=random_state,
            col_order=col_order,
            task=task,
        )


def _split_by_percentage(
    data: pd.DataFrame,
    col_target: str,
    train_percent: float,
    test_percent: float,
    validate_percent: float,
    random_state: int,
    col_order: str | None,
    task: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Internal function for percentage-based split."""

    if train_percent + validate_percent + test_percent != 1.0:
        raise ValueError("Sum of train, validate and test is not 1.0")
    if col_target not in data.columns:
        raise ValueError(f"{col_target} is not a column in the dataframe")

    if col_order is not None:
        data = data.sort_values(by=col_order, ignore_index=True)
        data = data.drop(col_order, axis=1)

    y = data[[col_target]]
    data = data.drop(col_target, axis=1)

    train_temp_params = {} if task == "reg" or col_order is not None else {"stratify": y}
    X_train, X_temp, y_train, y_temp = train_test_split(
        data, y, test_size=(1.0 - train_percent), random_state=random_state, **train_temp_params
    )

    test_val_params = {} if task == "reg" or col_order is not None else {"stratify": y_temp}
    validate_to_split = validate_percent / (validate_percent + test_percent)
    X_test, X_val, y_test, y_val = train_test_split(
        X_temp, y_temp, test_size=validate_to_split, random_state=random_state, **test_val_params
    )

    assert len(data) == len(X_train) + len(X_test) + len(
        X_val
    ), "Length of X is different than sum of x_train + x_test + x_val"
    assert len(y) == len(y_train) + len(y_test) + len(
        y_val
    ), "Length of y is different than sum of y_train + y_test + y_val"
    assert len(X_train) == len(y_train), "Length of X_train is different than y_train"
    assert len(X_test) == len(y_test), "Length of X_test is different than y_test"
    assert len(X_val) == len(y_val), "Length of X_val is different than y_val"

    return X_train, X_test, X_val, y_train, y_test, y_val


def _split_by_months(
    data: pd.DataFrame,
    col_target: str,
    col_date: str | None,
    train_months: list[int] | None,
    test_months: list[int] | None,
    val_months: list[int] | None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Internal function for month-based split."""

    # Validation checks
    if col_target not in data.columns:
        raise ValueError(f"{col_target} is not a column in the dataframe")
    if col_date is None:
        raise ValueError("col_date is required for monthly split mode")
    if col_date not in data.columns:
        raise ValueError(f"{col_date} is not a column in the dataframe")
    if train_months is None:
        raise ValueError("train_months is required for monthly split mode")
    if test_months is None:
        raise ValueError("test_months is required for monthly split mode")

    # Check for overlapping months
    all_months = set(train_months) | set(test_months)
    if val_months is not None:
        all_months |= set(val_months)
        overlap_train_test = set(train_months) & set(test_months)
        overlap_train_val = set(train_months) & set(val_months)
        overlap_test_val = set(test_months) & set(val_months)

        if overlap_train_test or overlap_train_val or overlap_test_val:
            raise ValueError(
                f"Months cannot overlap between datasets. "
                f"Train∩Test: {overlap_train_test}, "
                f"Train∩Val: {overlap_train_val}, "
                f"Test∩Val: {overlap_test_val}"
            )
    else:
        overlap = set(train_months) & set(test_months)
        if overlap:
            raise ValueError(f"Months cannot overlap between train and test: {overlap}")

    # Create a copy to avoid modifying original data
    df = data.copy()

    # Extract month from date column
    df["_month"] = pd.to_datetime(df[col_date]).dt.month

    # Split data by months
    train_mask = df["_month"].isin(train_months)
    test_mask = df["_month"].isin(test_months)

    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()

    if val_months is not None and len(val_months) > 0:
        val_mask = df["_month"].isin(val_months)
        df_val = df[val_mask].copy()
    else:
        df_val = pd.DataFrame(columns=df.columns)

    # Check that datasets are not empty
    if len(df_train) == 0:
        raise ValueError(f"Training set is empty. No data found for months: {train_months}")
    if len(df_test) == 0:
        raise ValueError(f"Test set is empty. No data found for months: {test_months}")
    if val_months is not None and len(val_months) > 0 and len(df_val) == 0:
        raise ValueError(f"Validation set is empty. No data found for months: {val_months}")

    # Remove temporary month column and split X/y
    df_train = df_train.drop("_month", axis=1)
    df_test = df_test.drop("_month", axis=1)
    df_val = df_val.drop("_month", axis=1) if len(df_val) > 0 else df_val

    # Split features and target
    X_train = df_train.drop(col_target, axis=1)
    y_train = df_train[[col_target]]

    X_test = df_test.drop(col_target, axis=1)
    y_test = df_test[[col_target]]

    if len(df_val) > 0:
        X_val = df_val.drop(col_target, axis=1)
        y_val = df_val[[col_target]]
    else:
        X_val = pd.DataFrame(columns=X_train.columns)
        y_val = pd.DataFrame(columns=y_train.columns)

    # Assertions
    assert len(X_train) == len(y_train), "Length of X_train is different than y_train"
    assert len(X_test) == len(y_test), "Length of X_test is different than y_test"
    assert len(X_val) == len(y_val), "Length of X_val is different than y_val"

    # Print split summary
    print("Data split summary:")
    print(f"  Train: {len(X_train)} samples (months: {sorted(train_months)})")
    print(f"  Test:  {len(X_test)} samples (months: {sorted(test_months)})")
    if val_months:
        print(f"  Val:   {len(X_val)} samples (months: {sorted(val_months)})")
    else:
        print(f"  Val:   {len(X_val)} samples (no validation set)")

    return X_train, X_test, X_val, y_train, y_test, y_val


def resample_X_y(
    X_train: pd.DataFrame, y_train: pd.Series, sampler_object: Any, params: Dict[str, Any] | None = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """Function for resampling train data and target column.

    Parameters
    ----------
    X_train : pd.DataFrame
        Data with all columns to train model
    y_train : pd.Series
        Target column
    sampler_object : Any
        Object of selected sampler to execute
    params : Dict[str, Any], optional
        Dictionary of params for selected sampler, by default None

    Returns
    -------
    Tuple[pd.DataFrame, pd.Series]
        - X_resampled : Resampled training data
        - y_resampled : Resampled target column
    """
    if params is None:
        params = {}

    if "id_client" in X_train.columns:
        X_train = X_train.drop("id_client", axis=1)
    sampler = sampler_object(**params)
    X_resampled, y_resampled = sampler.fit_resample(X_train, y_train)
    return X_resampled, y_resampled


def get_train_test_val_months(
    df: pd.DataFrame,
    date_column: str,
    n_val_months: int = 1,
    n_test_months: int = 2,
    exclude_periods: list[str] | None = None,
) -> tuple[list[int], list[int], list[int]]:
    """
    Automatically extracts months for train/test/val in chronological order.
    Handles data from different years and allows excluding specific periods.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with data
    date_column : str
        Name of the date column
    n_val_months : int, default=1
        Number of last months for validation
    n_test_months : int, default=2
        Number of months before validation for testing
    exclude_periods : list[str] | None, default=None
        List of specific periods to exclude in 'YYYY-MM' format.
        E.g. ['2024-06'] excludes June 2024, ['2024-11', '2024-12'] excludes November and December 2024.

    Returns
    -------
    tuple[list[int], list[int], list[int]]
        train_months, test_months, val_months (month number 1-12)

    Examples
    --------
    >>> # Exclude June 2024 (e.g. incomplete data)
    >>> train_m, test_m, val_m = get_train_test_val_months(
    ...     df, 'ftd_date', exclude_periods=['2024-06']
    ... )

    >>> # Exclude multiple specific periods
    >>> train_m, test_m, val_m = get_train_test_val_months(
    ...     df, 'ftd_date', exclude_periods=['2024-11', '2024-12', '2025-01']
    ... )
    """
    df_copy = df.copy()
    df_copy["_date"] = pd.to_datetime(df_copy[date_column])

    # Find unique year-month and sort chronologically
    df_copy["_year_month"] = df_copy["_date"].dt.to_period("M")
    unique_periods = sorted(df_copy["_year_month"].unique())

    # Exclude selected periods
    if exclude_periods is not None and len(exclude_periods) > 0:
        original_count = len(unique_periods)

        # Convert string periods to Period objects
        exclude_periods_set = {pd.Period(p, freq="M") for p in exclude_periods}
        unique_periods = [p for p in unique_periods if p not in exclude_periods_set]

        excluded_count = original_count - len(unique_periods)

        if excluded_count > 0:
            print(f"Excluded {excluded_count} period(s): {exclude_periods}")

    total_periods = len(unique_periods)

    if total_periods < (n_val_months + n_test_months + 1):
        raise ValueError(
            f"Insufficient number of periods in data after exclusion. "
            f"Need minimum {n_val_months + n_test_months + 1}, "
            f"available {total_periods}"
        )

    # Split periods
    val_periods = unique_periods[-n_val_months:]
    test_periods = unique_periods[-(n_val_months + n_test_months) : -n_val_months]
    train_periods = unique_periods[: -(n_val_months + n_test_months)]

    # Extract month number (1-12) from each period
    train_months = [p.month for p in train_periods]
    test_months = [p.month for p in test_periods]
    val_months = [p.month for p in val_periods]

    print(f"Periods in data: {unique_periods[0]} to {unique_periods[-1]}")
    print(f"Train: {train_months} ")
    print(f"Test:  {test_months} ")
    print(f"Val:   {val_months}")

    return train_months, test_months, val_months
