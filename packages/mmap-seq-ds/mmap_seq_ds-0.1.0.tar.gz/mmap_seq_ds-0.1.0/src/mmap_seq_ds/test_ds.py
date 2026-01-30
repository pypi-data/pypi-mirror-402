import random
import tempfile

import numpy as np

from mmap_seq_ds import MMapDataset, write_sharded_mmap_dataset


def test_general():
    def generate(num_samples, min_len, max_len, aligned_keys):
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
        from torch.utils.data import DataLoader

        # Create a DataLoader with RandomSampler
        dataloader = DataLoader(dataset_with_filter, batch_size=1)

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
