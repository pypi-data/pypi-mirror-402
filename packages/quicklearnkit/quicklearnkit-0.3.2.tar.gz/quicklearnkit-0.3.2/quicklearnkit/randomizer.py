import random
import numpy as np
import pandas as pd
from typing import Union, Optional


DataType = Union[list, tuple, np.ndarray, pd.DataFrame]


class Sampler:
    """
    Unified random sampler supporting:

    - Stateful and stateless sampling
    - Sampling with or without replacement
    - list, numpy.ndarray, pandas.DataFrame
    - Row or column sampling for DataFrames

    Parameters
    ----------
    data : list, tuple, numpy.ndarray, or pandas.DataFrame
        Data to sample from.
    replace : bool, default=False
        Whether sampling is done with replacement.
    stateful : bool, default=False
        If True, sampled elements are removed from future draws.
    seed : int, optional
        Random seed for reproducibility.
    """

    def __init__(
        self,
        data: DataType,
        replace: bool = False,
        stateful: bool = False,
        seed: Optional[int] = None
    ):
        self.replace = replace
        self.stateful = stateful

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Detect data type
        if isinstance(data, (list, tuple)):
            self._type = "list"
            self.data = list(data)

        elif isinstance(data, np.ndarray):
            self._type = "array"
            self.data = data

        elif isinstance(data, pd.DataFrame):
            self._type = "df"
            self.data = data

        else:
            raise TypeError(
                "Unsupported data type. Use list, numpy array, or pandas DataFrame."
            )

        if self.stateful:
            self._reset_pool()

    # ---------------- INTERNAL ---------------- #

    def _reset_pool(self):
        """Initialize or reset internal sampling pool."""
        if self._type == "list":
            self.pool = self.data.copy()
            random.shuffle(self.pool)

        elif self._type == "array":
            self.pool = self.data.copy()
            np.random.shuffle(self.pool)

        elif self._type == "df":
            self.pool = self.data.copy()

    # ---------------- PUBLIC API ---------------- #

    def sample(self, n: int = 1, axis: int = 0):
        """
        Sample data.

        Parameters
        ----------
        n : int, default=1
            Number of items to sample.
        axis : int, default=0
            Axis to sample from when data is a DataFrame.
            0 = rows, 1 = columns.

        Returns
        -------
        Sampled data (same type as input).
        """

        if n <= 0:
            raise ValueError("n must be a positive integer")

        source = self.pool if self.stateful else self.data

        # -------- LIST --------
        if self._type == "list":
            if self.stateful:
                if n > len(self.pool):
                    raise StopIteration("No items left to sample")
                out = self.pool[:n]
                self.pool = self.pool[n:]
                return out

            if not self.replace and n > len(source):
                raise ValueError("Cannot sample more elements than population")

            return (
                random.sample(source, n)
                if not self.replace
                else random.choices(source, k=n)
            )

        # -------- NUMPY ARRAY --------
        if self._type == "array":
            if self.stateful:
                if n > len(self.pool):
                    raise StopIteration("No items left to sample")
                out = self.pool[:n]
                self.pool = self.pool[n:]
                return out

            return np.random.choice(source, size=n, replace=self.replace)

        # -------- DATAFRAME --------
        if self._type == "df":
            if axis not in (0, 1):
                raise ValueError("axis must be 0 (rows) or 1 (columns)")

            # Row sampling
            if axis == 0:
                if self.stateful:
                    if n > len(self.pool):
                        raise StopIteration("No rows left to sample")
                    out = self.pool.iloc[:n]
                    self.pool = self.pool.iloc[n:]
                    return out

                return self.data.sample(n=n, replace=self.replace)

            # Column sampling
            cols = list(source.columns)

            if n > len(cols):
                raise StopIteration("No columns left to sample")

            chosen = (
                cols[:n]
                if self.stateful
                else random.sample(cols, n)
                if not self.replace
                else random.choices(cols, k=n)
            )

            if self.stateful:
                self.pool = self.pool.drop(columns=chosen)

            return self.data[chosen]

    def reset(self):
        """
        Reset internal state (only for stateful sampler).
        """
        if not self.stateful:
            raise RuntimeError("reset() is only available when stateful=True")
        self._reset_pool()
