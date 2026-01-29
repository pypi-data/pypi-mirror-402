from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator

import pandas as pd
import numpy as np

try:
    import torch
    from torch.utils.data import Dataset, IterableDataset
except ImportError:
    class Dataset:  # type: ignore
        pass
    class IterableDataset:  # type: ignore
        pass
    torch = None  # type: ignore

try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None

from datashift import load
from datashift.versioning import resolve_version
from datashift.storage import load_dataset_file


class TorchDataset(Dataset):
    """
    PyTorch Dataset adapter for DataShift datasets.
    Loads the entire dataset into memory (suitable for small to medium datasets).
    
    Args:
        dataset_spec: The dataset specification (e.g. 'my_data@v1')
        base_path: Optional path to the DataShift repository
        columns: Optional list of columns to load.
        target_column: Optional name of the target/label column.
        transform: Optional callable to transform the features.
        target_transform: Optional callable to transform the target.
        to_tensor: If True (default), converts outputs to PyTorch tensors automatically.
    """
    def __init__(
        self,
        dataset_spec: str,
        base_path: Path | None = None,
        columns: list[str] | None = None,
        target_column: str | None = None,
        transform: Callable | None = None,
        target_transform: Callable | None = None,
        to_tensor: bool = True,
    ):
        if torch is None:
            raise ImportError("PyTorch is not installed. Please install 'torch' to use TorchDataset.")
            
        self.df = load(dataset_spec, columns=columns, base_path=base_path)
        self.target_column = target_column
        self.transform = transform
        self.target_transform = target_transform
        self.to_tensor = to_tensor
        
        if self.target_column and self.target_column not in self.df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in dataset")

    def __len__(self) -> int:
        return len(self.df)

    def _convert_to_tensor(self, data: Any) -> Any:
        if not self.to_tensor:
            return data
        
        if isinstance(data, (np.ndarray, list)):
            # Handle numeric types specifically to avoid errors with object arrays (strings)
            try:
                return torch.tensor(data)
            except (ValueError, TypeError):
                # Fallback for mixed/string types: return as is or let user handle it
                return data
        if np.isscalar(data):
            if isinstance(data, (int, float, bool, np.number)):
                return torch.tensor(data)
        return data

    def __getitem__(self, idx: int) -> Any:
        if torch.is_tensor(idx):
            idx = idx.tolist()  # type: ignore

        row = self.df.iloc[idx]
        
        if self.target_column:
            target = row[self.target_column]
            features = row.drop(self.target_column)
            
            features_data = features.values
            
            if self.transform:
                features_data = self.transform(features_data)
            elif self.to_tensor:
                # Apply default tensor conversion only if no transform provided
                # (If transform is provided, we assume it handles conversion)
                features_data = self._convert_to_tensor(features_data)
            
            if self.target_transform:
                target = self.target_transform(target)
            elif self.to_tensor:
                target = self._convert_to_tensor(target)
                
            return features_data, target
        else:
            data = row.values
            if self.transform:
                data = self.transform(data)
            elif self.to_tensor:
                data = self._convert_to_tensor(data)
            return data


class TorchIterableDataset(IterableDataset):
    """
    PyTorch IterableDataset adapter for DataShift datasets.
    Streams data from disk without loading the entire dataset into memory.
    Requires 'pyarrow' to be installed.
    
    Args:
        dataset_spec: The dataset specification (e.g. 'my_data@v1')
        base_path: Optional path to the DataShift repository
        columns: Optional list of columns to load.
        target_column: Optional name of the target/label column.
        transform: Optional callable to transform the features.
        target_transform: Optional callable to transform the target.
        to_tensor: If True (default), converts outputs to PyTorch tensors automatically.
        batch_size: Number of rows to read from disk at a time (buffer size).
    """
    def __init__(
        self,
        dataset_spec: str,
        base_path: Path | None = None,
        columns: list[str] | None = None,
        target_column: str | None = None,
        transform: Callable | None = None,
        target_transform: Callable | None = None,
        to_tensor: bool = True,
        batch_size: int = 1024,
    ):
        if torch is None:
            raise ImportError("PyTorch is not installed. Please install 'torch'.")
        if pq is None:
            raise ImportError("PyArrow is not installed. Please install 'pyarrow' to use TorchIterableDataset.")

        self.dataset_spec = dataset_spec
        self.base_path = base_path
        self.columns = columns
        self.target_column = target_column
        self.transform = transform
        self.target_transform = target_transform
        self.to_tensor = to_tensor
        self.batch_size = batch_size
        
        # Resolve path immediately to fail fast if dataset doesn't exist
        record = resolve_version(self.dataset_spec, self.base_path)
        self.file_path = load_dataset_file(record.object_path, self.base_path)

    def _convert_to_tensor(self, data: Any) -> Any:
        # Same logic as TorchDataset
        if not self.to_tensor:
            return data
        if isinstance(data, (np.ndarray, list)):
            try:
                return torch.tensor(data)
            except (ValueError, TypeError):
                return data
        if np.isscalar(data):
            if isinstance(data, (int, float, bool, np.number)):
                return torch.tensor(data)
        return data

    def __iter__(self) -> Iterator[Any]:
        worker_info = torch.utils.data.get_worker_info()
        
        # Open parquet file
        parquet_file = pq.ParquetFile(self.file_path)
        
        # Simple sharding for multi-worker loading
        # Note: Parquet row groups might not align perfectly with equal splitting,
        # but iterating batches is safer. For true sharding, we'd assign row groups.
        if worker_info is None:
            # Single process
            batch_iter = parquet_file.iter_batches(batch_size=self.batch_size, columns=self.columns)
        else:
            # Split by row groups if possible, otherwise simple skip
            # Ideally we split row groups among workers
            num_row_groups = parquet_file.num_row_groups
            per_worker = int(np.ceil(num_row_groups / worker_info.num_workers))
            worker_id = worker_info.id
            start = worker_id * per_worker
            end = min(start + per_worker, num_row_groups)
            
            # If dataset is small (fewer row groups than workers), some workers get nothing
            # If dataset is large, this works well.
            row_groups = list(range(start, end))
            if not row_groups:
                return
                
            batch_iter = parquet_file.iter_batches(
                batch_size=self.batch_size, 
                columns=self.columns, 
                row_groups=row_groups
            )

        for batch in batch_iter:
            df = batch.to_pandas()
            # Filter columns if needed (iter_batches usually handles it but to be safe)
            if self.target_column and self.target_column not in df.columns:
                 # This might happen if user didn't request target column in 'columns'
                 # but we can't recover here easily without re-reading.
                 # Assuming user provided correct columns list including target.
                 pass

            for _, row in df.iterrows():
                if self.target_column:
                    target = row[self.target_column]
                    features = row.drop(self.target_column)
                    features_data = features.values
                    
                    if self.transform:
                        features_data = self.transform(features_data)
                    elif self.to_tensor:
                        features_data = self._convert_to_tensor(features_data)
                    
                    if self.target_transform:
                        target = self.target_transform(target)
                    elif self.to_tensor:
                        target = self._convert_to_tensor(target)
                        
                    yield features_data, target
                else:
                    data = row.values
                    if self.transform:
                        data = self.transform(data)
                    elif self.to_tensor:
                        data = self._convert_to_tensor(data)
                    yield data
