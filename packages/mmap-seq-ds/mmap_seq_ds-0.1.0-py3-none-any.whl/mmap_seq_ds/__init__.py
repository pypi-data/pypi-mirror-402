import json
import tempfile
from pathlib import Path

import msgpack
import numpy as np
from torch.utils.data import Dataset

__all__ = ["MMapDataset", "write_sharded_mmap_dataset"]


def write_sharded_mmap_dataset(source_iter, out_dir, shard_size=10000, fmt="msgpack"):
    """
    Stream from source_iter and write shards + global root index.
    All aligned keys share the same segment offsets per sample.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    global_index = {"format": fmt, "shards": []}
    shard_id = 0
    shard_samples = []
    aligned_keys = None

    def flush_shard():
        nonlocal shard_id, shard_samples, aligned_keys
        if not shard_samples:
            return

        shard_dir = out_dir / f"shard{shard_id:05d}"
        shard_dir.mkdir(exist_ok=True)

        # Determine total length for each key
        total_lens = {}
        for k in aligned_keys:
            total_lens[k] = sum(len(s["aligned"][k]) for s in shard_samples)

        # create memmaps per key
        memmaps = {}
        for k in aligned_keys:
            dtype = shard_samples[0]["aligned"][k].dtype
            memmaps[k] = np.memmap(
                shard_dir / f"{k}.bin", dtype=dtype, mode="w+", shape=(total_lens[k],)
            )

        # write samples sequentially, shared segments
        segments = []
        offset = 0
        for s in shard_samples:
            length = len(s["aligned"][aligned_keys[0]])
            for k in aligned_keys:
                memmaps[k][offset : offset + length] = s["aligned"][k]
            segments.append((offset, length))
            offset += length

        # flush memmaps
        for k in memmaps:
            memmaps[k].flush()

        # store dtypes for each key
        key_dtypes = {}
        for k in aligned_keys:
            key_dtypes[k] = str(shard_samples[0]["aligned"][k].dtype)

        # shard index
        shard_index = {
            "sequences": [
                {"sequence_id": s.get("id", None), "meta": s.get("meta", {})}
                for s in shard_samples
            ],
            "aligned_keys": aligned_keys,
            "key_dtypes": key_dtypes,
            "segments": segments,
        }

        # write shard index
        idx_path = shard_dir / f"index.{fmt}"
        if fmt == "json":
            with open(idx_path, "w") as f:
                json.dump(shard_index, f)
        else:
            with open(idx_path, "wb") as f:
                f.write(msgpack.packb(shard_index, use_bin_type=True))

        # update global index
        global_index["shards"].append(
            {
                "id": shard_id,
                "path": str(shard_dir.relative_to(out_dir)),
                "num_sequences": len(shard_samples),
            }
        )

        shard_id += 1
        shard_samples.clear()

    # Stream samples
    for sample in source_iter:
        if aligned_keys is None:
            aligned_keys = list(sample["aligned"].keys())
        shard_samples.append(sample)
        if len(shard_samples) >= shard_size:
            flush_shard()

    if shard_samples:
        flush_shard()

    # write global root index
    global_idx_path = out_dir / f"index.{fmt}"
    if fmt == "json":
        with open(global_idx_path, "w") as f:
            json.dump(global_index, f)
    else:
        with open(global_idx_path, "wb") as f:
            f.write(msgpack.packb(global_index, use_bin_type=True))


class MMapDataset(Dataset):
    def __init__(
        self,
        root_dir,
        window_size=None,
        mmap_mode="r",
        filter_fn=None,
        filter_return_none=False,
        map_fn=None,
    ):
        self.root_dir = Path(root_dir)
        self.window_size = window_size
        self.mmap_mode = mmap_mode
        self.filter_fn = filter_fn
        self.map_fn = map_fn
        self._memmaps = {}

        # load global index
        if (self.root_dir / "index.msgpack").exists():
            idx_path = self.root_dir / "index.msgpack"
            with open(idx_path, "rb") as f:
                self.global_index = msgpack.unpackb(f.read(), raw=False)
        elif (self.root_dir / "index.json").exists():
            idx_path = self.root_dir / "index.json"
            with open(idx_path, "r") as f:
                self.global_index = json.load(f)
        else:
            raise FileNotFoundError("No global index found in dataset root")

        # build flat sample list: (shard_id, local_idx)
        self.samples = {}
        sample_idx = 0
        for shard in self.global_index["shards"]:
            shard_id = shard["id"]
            for local_idx in range(shard["num_sequences"]):
                self.samples[sample_idx] = (shard_id, local_idx)
                sample_idx += 1

        # Keep track of original sample count for debugging
        self.original_sample_count = len(self.samples)

        self.filter_return_none = filter_return_none

        # Track the maximum number of filter retries to prevent infinite loops
        self.max_filter_retries = 100

    def __len__(self):
        # Always return the original sample count to maintain consistency with samplers
        return self.original_sample_count

    def _load_shard(self, shard_id):
        if shard_id in self._memmaps:
            return self._memmaps[shard_id]

        shard_meta = next(s for s in self.global_index["shards"] if s["id"] == shard_id)
        shard_dir = self.root_dir / shard_meta["path"]

        # detect shard index
        if (shard_dir / "index.msgpack").exists():
            idx_path = shard_dir / "index.msgpack"
            with open(idx_path, "rb") as f:
                shard_index = msgpack.unpackb(f.read(), raw=False)
        else:
            idx_path = shard_dir / "index.json"
            with open(idx_path, "r") as f:
                shard_index = json.load(f)

        # load memmaps with correct dtypes
        memmaps = {}
        for k in shard_index["aligned_keys"]:
            # Use stored dtype or fallback to float32 for backward compatibility
            dtype = shard_index.get("key_dtypes", {}).get(k, "float32")
            memmaps[k] = np.memmap(
                shard_dir / f"{k}.bin", dtype=dtype, mode=self.mmap_mode
            )

        self._memmaps[shard_id] = (memmaps, shard_index)
        return self._memmaps[shard_id]

    def __getitem__(self, idx):
        # Check bounds against original sample count
        if idx >= self.original_sample_count:
            raise IndexError(
                f"Index {idx} out of range for dataset of length {self.original_sample_count}"
            )

        return self._get_item_with_filter(idx)

    def _get_item_with_filter(self, idx, _retry_count=0):
        """Get item with optional filtering, with limited retries."""

        # Prevent infinite retries
        if _retry_count >= self.max_filter_retries:
            raise RuntimeError(
                f"Exceeded maximum filter retries ({self.max_filter_retries}) for index {idx}"
            )

        # Check if this sample index still exists (might have been filtered out previously)
        if idx not in self.samples:
            # Sample was filtered out, try a random valid index
            valid_indices = list(self.samples.keys())
            if not valid_indices:
                raise RuntimeError("No valid samples remaining in dataset")

            # Choose a random valid index
            random_idx = np.random.choice(valid_indices)
            return self._get_item_with_filter(random_idx, _retry_count + 1)

        # Get the sample data
        shard_id, local_idx = self.samples[idx]

        try:
            memmaps, shard_index = self._load_shard(shard_id)
        except Exception as e:
            # If we can't load the shard, try another sample
            if _retry_count < self.max_filter_retries:
                valid_indices = list(self.samples.keys())
                if valid_indices:
                    random_idx = np.random.choice(
                        [i for i in valid_indices if i != idx]
                    )
                    return self._get_item_with_filter(random_idx, _retry_count + 1)
            raise RuntimeError(f"Failed to load shard {shard_id}: {e}")

        # Check if local_idx is valid
        if local_idx >= len(shard_index["segments"]):
            # Invalid local index, remove this sample and try another
            del self.samples[idx]
            if _retry_count < self.max_filter_retries:
                valid_indices = list(self.samples.keys())
                if valid_indices:
                    random_idx = np.random.choice(valid_indices)
                    return self._get_item_with_filter(random_idx, _retry_count + 1)
            raise RuntimeError(f"Invalid local index {local_idx} for shard {shard_id}")

        seg_start, seg_len = shard_index["segments"][local_idx]

        # choose window start once
        if self.window_size is not None and seg_len > self.window_size:
            w_start = np.random.randint(0, seg_len - self.window_size + 1)
            w_end = w_start + self.window_size
        else:
            w_start, w_end = 0, seg_len

        aligned = {}
        for k in shard_index["aligned_keys"]:
            try:
                arr = memmaps[k][seg_start + w_start : seg_start + w_end]
                aligned[k] = arr.copy()
            except Exception as e:
                # Data corruption or other issue, remove this sample and try another
                del self.samples[idx]
                if _retry_count < self.max_filter_retries:
                    valid_indices = list(self.samples.keys())
                    if valid_indices:
                        random_idx = np.random.choice(valid_indices)
                        return self._get_item_with_filter(random_idx, _retry_count + 1)
                raise RuntimeError(f"Failed to read data for sample {idx}: {e}")

        seq_meta = shard_index["sequences"][local_idx].get("meta", {})
        seq_id = shard_index["sequences"][local_idx].get("sequence_id", None)
        item = {"id": seq_id, "aligned": aligned, "meta": seq_meta}

        # Apply map_fn transformation if provided
        if self.map_fn is not None:
            try:
                item = self.map_fn(item)
            except Exception as e:
                # Map function failed, remove this sample and try another
                del self.samples[idx]
                if _retry_count < self.max_filter_retries:
                    valid_indices = list(self.samples.keys())
                    if valid_indices:
                        random_idx = np.random.choice(valid_indices)
                        return self._get_item_with_filter(random_idx, _retry_count + 1)
                raise RuntimeError(f"Map function failed for sample {idx}: {e}")

        # Apply filter if provided
        if self.filter_fn is not None:
            try:
                passes_filter = self.filter_fn(item)
            except Exception as e:
                # Filter function failed, remove this sample and try another
                del self.samples[idx]
                if _retry_count < self.max_filter_retries:
                    valid_indices = list(self.samples.keys())
                    if valid_indices:
                        random_idx = np.random.choice(valid_indices)
                        return self._get_item_with_filter(random_idx, _retry_count + 1)
                raise RuntimeError(f"Filter function failed for sample {idx}: {e}")

            if not passes_filter:
                if self.filter_return_none:
                    return None

                # Remove this sample since it doesn't pass the filter
                del self.samples[idx]

                # Try a different random sample
                if _retry_count < self.max_filter_retries:
                    valid_indices = list(self.samples.keys())
                    if valid_indices:
                        random_idx = np.random.choice(valid_indices)
                        return self._get_item_with_filter(random_idx, _retry_count + 1)

                raise RuntimeError("No more valid samples available after filtering")

        return item


def test_general():
    import numpy as np

    def generate(num_samples, min_len, max_len, aligned_keys):
        import random

        for i in range(num_samples):
            length = random.randint(min_len, max_len)
            sample = {
                "id": f"sample_{i}",
                "meta": {"length": length},
                "aligned": {k: np.arange(length) for k in aligned_keys},
            }
            yield sample

    stream = generate(
        num_samples=1_000,
        min_len=500,
        max_len=2000,
        aligned_keys=["wavelength", "flux"],
    )

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        write_sharded_mmap_dataset(stream, temp_dir, shard_size=200)

        window_size = 20

        ds = MMapDataset(temp_dir, window_size=None)
        dsw = MMapDataset(temp_dir, window_size=window_size)

        for idx in range(len(ds)):
            sample = ds[idx]
            samplew = dsw[idx]

            offset = np.where(
                sample["aligned"]["wavelength"] == samplew["aligned"]["wavelength"][0]
            )[0][0]

            assert np.allclose(
                sample["aligned"]["wavelength"][offset : offset + window_size],
                samplew["aligned"]["wavelength"],
            ), f"Mismatch at index {idx}"
            assert np.allclose(
                sample["aligned"]["flux"][offset : offset + window_size],
                samplew["aligned"]["flux"],
                atol=1e-5,
                rtol=1e-5,
            ), f"Mismatch at index {idx}"


def test_filtering():
    """Test the filtering functionality"""
    import random

    def generate_test_data():
        for i in range(10):
            # Create data where some samples will be "bad" (even IDs)
            length = random.randint(50, 100)
            sample = {
                "id": f"sample_{i}",
                "meta": {
                    "sample_id": i,
                    "is_bad": i % 2 == 0,
                },  # Even samples are "bad"
                "aligned": {
                    "wavelength": np.arange(length, dtype=np.float32),
                    "flux": np.random.normal(0, 1, size=length).astype(np.float32),
                },
            }
            yield sample

    # Filter function that rejects "bad" samples
    def filter_fn(item):
        return not item["meta"].get("is_bad", False)

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # Write the dataset
        write_sharded_mmap_dataset(generate_test_data(), temp_dir, shard_size=5)

        # Test without filtering
        print("\n=== Dataset without filtering ===")
        dataset_no_filter = MMapDataset(temp_dir)
        print(f"Total samples: {len(dataset_no_filter)}")

        # Test with filtering
        print("\n=== Dataset with filtering ===")
        dataset_with_filter = MMapDataset(temp_dir, filter_fn=filter_fn)
        print(f"Initial samples: {len(dataset_with_filter)}")

        # Test with PyTorch DataLoader and RandomSampler
        print("\n=== Testing with PyTorch DataLoader and RandomSampler ===")
        from dfs.data import DynamicDistributedSampler
        from torch.utils.data import DataLoader

        # Create a DataLoader with RandomSampler
        sampler = DynamicDistributedSampler(dataset_with_filter)
        dataloader = DataLoader(dataset_with_filter, batch_size=1, sampler=sampler)

        print("DataLoader created with batch_size=1")
        print(f"Dataset length for sampler: {len(dataset_with_filter)}")

        # Iterate through a few batches
        for batch_idx, batch in enumerate(dataloader):
            if batch_idx >= 5:  # Only test first few batches
                break

            print(f"\nBatch {batch_idx}:", batch)

        print(
            f"\nFinal dataset length after DataLoader usage: {len(dataset_with_filter)}"
        )
        print(f"Remaining good indices: {sorted(dataset_with_filter.samples.keys())}")


def test_dtype_mismatch():
    """Test to reproduce the dtype mismatch issue"""

    # Create test data with known values
    def generate_test_data():
        for i in range(3):
            # Use float64 data (this is what np.random.normal returns by default)
            wavelength = np.random.normal(0, 1, size=100).astype(
                np.float64
            )  # Explicit float64
            flux = np.random.normal(0, 1, size=100).astype(
                np.float64
            )  # Explicit float64

            print(
                f"Sample {i}: wavelength dtype={wavelength.dtype}, range=[{wavelength.min():.6f}, {wavelength.max():.6f}]"
            )
            print(
                f"Sample {i}: flux dtype={flux.dtype}, range=[{flux.min():.6f}, {flux.max():.6f}]"
            )

            yield {
                "id": f"sample_{i}",
                "aligned": {"wavelength": wavelength, "flux": flux},
                "meta": {"sample_id": i},
            }

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # Write the dataset
        print("\n=== Writing dataset ===")
        data_gen = generate_test_data()
        write_sharded_mmap_dataset(data_gen, temp_dir, shard_size=2)

        # Read back the dataset
        print("\n=== Reading dataset ===")
        dataset = MMapDataset(temp_dir)

        # Check first sample
        sample = dataset[0]
        wavelength = sample["aligned"]["wavelength"]
        flux = sample["aligned"]["flux"]

        print(
            f"Read back: wavelength dtype={wavelength.dtype}, range=[{wavelength.min():.6f}, {wavelength.max():.6f}]"
        )
        print(
            f"Read back: flux dtype={flux.dtype}, range=[{flux.min():.6f}, {flux.max():.6f}]"
        )

        # Check if values are corrupted (large numbers indicate dtype mismatch)
        if np.any(np.abs(wavelength) > 1e10) or np.any(np.abs(flux) > 1e10):
            print("\n❌ DTYPE MISMATCH DETECTED: Values are corrupted!")
            print("This happens when float64 data is written but read back as float32")
        else:
            print("\n✅ Data looks correct")
