import numpy as np

def create_random(mean, std, size, random_state=None):
    """
    Generate random data with a specified mean and standard deviation.

    Parameters:
        mean (float): Desired mean of the data.
        std (float): Desired standard deviation of the data.
        size (int): Length of the data to generate.
        random_state (int, optional): Seed for reproducibility. Defaults to None.

    Returns:
        dict: A dictionary containing:
            - "data": Random data with the specified mean and standard deviation.
            - "mean": Actual mean of the generated data.
            - "std": Actual standard deviation of the generated data.

    Raises:
        ValueError: If std is negative or size is not a positive integer.
    """
    if std < 0:
        raise ValueError("Standard deviation must be non-negative.")
    if size <= 0:
        raise ValueError("Size must be a positive integer.")

    # Create a random number generator instance
    rng = np.random.default_rng(random_state)
    
    # Generate random normal data
    x = rng.normal(size=size)
    x1 = (x - np.mean(x)) / np.std(x)
    x2 = (x1 * std) + mean

    return {
        "data": x2,
        "mean": np.mean(x2),
        "std": np.std(x2)
    }


import numpy as np
import pandas as pd
from typing import Optional, Dict


class ProbabilisticImputer:
    """
    Probabilistic, group-aware categorical imputer.

    Learns conditional probability distributions during `fit()`
    and samples missing values during `transform()`.

    Default behavior is stateless (fully reproducible).
    If stateful=True, RNG state advances across calls for
    simulation / data augmentation workflows.

    Parameters
    ----------
    group_col : str
        Column name used to group data (e.g. class, category, segment).
    target_col : str
        Column name to impute.
    random_state : int, optional
        Seed for reproducible randomness.
    stateful : bool, default=False
        If True, RNG state advances across multiple transform calls.
    """

    def __init__(
        self,
        group_col: str,
        target_col: str,
        random_state: Optional[int] = None,
        stateful: bool = False
    ):
        self.group_col = group_col
        self.target_col = target_col
        self.random_state = random_state
        self.stateful = stateful

        self._fitted = False
        self._dist_map: Dict = {}

        self._init_rng()

    # ---------------- INTERNAL ---------------- #

    def _init_rng(self):
        """Initialize or reset the random number generator."""
        self.rng = np.random.default_rng(self.random_state)

    # ---------------- PUBLIC API ---------------- #

    def fit(self, df: pd.DataFrame):
        """
        Learn per-group probability distributions from observed data.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame containing group and target columns.

        Returns
        -------
        self
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if self.group_col not in df.columns or self.target_col not in df.columns:
            raise ValueError("group_col and target_col must exist in DataFrame")

        self._dist_map.clear()

        # Build per-group distributions
        grouped = df.dropna(subset=[self.target_col]).groupby(self.group_col)

        for group, gdf in grouped:
            probs = (
                gdf[self.target_col]
                .value_counts(normalize=True)
                .to_dict()
            )
            self._dist_map[group] = probs

        # Global fallback distribution
        self._global_dist = (
            df[self.target_col]
            .dropna()
            .value_counts(normalize=True)
            .to_dict()
        )

        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Impute missing values using learned distributions.

        Parameters
        ----------
        df : pandas.DataFrame
            DataFrame to transform.

        Returns
        -------
        pandas.DataFrame
            New DataFrame with missing values imputed.
        """
        if not self._fitted:
            raise RuntimeError("Must call fit() before transform()")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        out = df.copy()
        missing_mask = out[self.target_col].isna()

        for idx in out[missing_mask].index:
            group = out.at[idx, self.group_col]

            # Get group distribution or fallback to global
            dist = self._dist_map.get(group, self._global_dist)

            if not dist:
                continue  # Nothing to sample from

            choices = list(dist.keys())
            probs = list(dist.values())

            out.at[idx, self.target_col] = self.rng.choice(
                choices,
                p=probs
            )

        # Reset RNG if stateless (default behavior)
        if not self.stateful:
            self._init_rng()

        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit and transform in one step.

        Parameters
        ----------
        df : pandas.DataFrame

        Returns
        -------
        pandas.DataFrame
        """
        return self.fit(df).transform(df)
