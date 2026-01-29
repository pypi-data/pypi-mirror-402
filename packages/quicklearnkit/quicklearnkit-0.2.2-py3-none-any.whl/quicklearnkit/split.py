import numpy as np
import pandas as pd
from typing import Optional, Tuple, Union


ArrayLike = Union[np.ndarray, pd.DataFrame]


def train_test_split(
    X: ArrayLike,
    y: Optional[np.ndarray] = None,
    test_size: float = 0.25,
    shuffle: bool = True,
    stratify: Optional[np.ndarray] = None,
    random_state: Optional[int] = None
) -> Tuple:
    """
    Split data into train and test subsets.

    Parameters
    ----------
    X : numpy.ndarray or pandas.DataFrame
        Feature data to split.
    y : numpy.ndarray, optional
        Target labels corresponding to X.
    test_size : float, default=0.25
        Proportion of the dataset to include in the test split.
    shuffle : bool, default=True
        Whether to shuffle data before splitting.
    stratify : numpy.ndarray, optional
        Class labels for stratified split (classification only).
    random_state : int, optional
        Seed for reproducibility.

    Returns
    -------
    X_train, X_test : same type as X
        Split feature data.
    y_train, y_test : numpy.ndarray, optional
        Split target labels (only if y is provided).
    """

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    if random_state is not None:
        np.random.seed(random_state)

    n_samples = len(X)
    indices = np.arange(n_samples)

    # ---------- STRATIFIED SPLIT ----------
    if stratify is not None:
        if y is None:
            raise ValueError("y must be provided when using stratify")

        if not shuffle:
            raise ValueError("Stratified split requires shuffle=True")

        stratify = np.asarray(stratify)

        train_idx = []
        test_idx = []

        for cls in np.unique(stratify):
            cls_indices = indices[stratify == cls]
            np.random.shuffle(cls_indices)

            split = int(len(cls_indices) * (1 - test_size))
            train_idx.extend(cls_indices[:split])
            test_idx.extend(cls_indices[split:])

        train_idx = np.array(train_idx)
        test_idx = np.array(test_idx)

    # ---------- STANDARD SPLIT ----------
    else:
        if shuffle:
            np.random.shuffle(indices)

        split = int(n_samples * (1 - test_size))
        train_idx, test_idx = indices[:split], indices[split:]

    # ---------- APPLY INDICES ----------
    if isinstance(X, pd.DataFrame):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]
    else:
        X_train = X[train_idx]
        X_test = X[test_idx]

    if y is None:
        return X_train, X_test

    y = np.asarray(y)
    y_train = y[train_idx]
    y_test = y[test_idx]

    return X_train, X_test, y_train, y_test
