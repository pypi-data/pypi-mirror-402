"""
Dataset classes for loading manipulation data.
"""

from pathlib import Path
from typing import Iterator, Optional, Callable, Literal

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

from terso.sample import Sample


class ManipulationDataset(Dataset):
    """
    Base dataset class for manipulation video data.
    
    Args:
        root: Root directory containing the dataset
        split: Which split to load ("train", "val", "test")
        task: Optional task filter (e.g., "pour_latte", "crack_egg")
        transform: Optional transform to apply to samples
        load_annotations: Which annotations to load
    """
    
    ANNOTATION_TYPES = ["hand_poses", "actions", "depth_maps", "object_masks"]
    
    def __init__(
        self,
        root: str | Path,
        split: Literal["train", "val", "test"] = "train",
        task: Optional[str] = None,
        transform: Optional[Callable] = None,
        load_annotations: list[str] = None,
    ):
        self.root = Path(root)
        self.split = split
        self.task = task
        self.transform = transform
        self.load_annotations = load_annotations or self.ANNOTATION_TYPES
        
        # Find all clip directories
        self.clips = self._find_clips()
        
        if len(self.clips) == 0:
            raise ValueError(f"No clips found in {self.root} for split={split}, task={task}")
    
    def _find_clips(self) -> list[Path]:
        """Find all clip directories matching the criteria."""
        split_dir = self.root / self.split
        
        if not split_dir.exists():
            # Maybe flat structure
            split_dir = self.root
        
        clips = []
        
        for clip_dir in sorted(split_dir.iterdir()):
            if not clip_dir.is_dir():
                continue
            
            # Check if it has video/frames
            has_video = (clip_dir / "video.mp4").exists()
            has_frames = (clip_dir / "frames").exists()
            
            if not (has_video or has_frames):
                continue
            
            # Filter by task if specified
            if self.task:
                metadata_file = clip_dir / "metadata.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    if metadata.get("task") != self.task:
                        continue
                else:
                    # Use directory name as task hint
                    if self.task not in clip_dir.name:
                        continue
            
            clips.append(clip_dir)
        
        return clips
    
    def __len__(self) -> int:
        return len(self.clips)
    
    def __getitem__(self, idx: int) -> Sample:
        clip_path = self.clips[idx]
        sample = Sample.from_directory(clip_path)
        
        if self.transform:
            sample = self.transform(sample)
        
        return sample
    
    def __iter__(self) -> Iterator[Sample]:
        for idx in range(len(self)):
            yield self[idx]
    
    def get_dataloader(
        self,
        batch_size: int = 1,
        shuffle: bool = True,
        num_workers: int = 4,
        collate_fn: Optional[Callable] = None,
    ) -> DataLoader:
        """
        Get a PyTorch DataLoader for this dataset.
        
        Args:
            batch_size: Batch size
            shuffle: Whether to shuffle
            num_workers: Number of worker processes
            collate_fn: Custom collate function
            
        Returns:
            DataLoader instance
        """
        if collate_fn is None:
            collate_fn = self._default_collate
        
        return DataLoader(
            self,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=collate_fn,
            pin_memory=True,
        )
    
    @staticmethod
    def _default_collate(samples: list[Sample]) -> dict[str, torch.Tensor]:
        """
        Default collate function that stacks samples into batches.
        
        Note: This requires all samples to have the same number of frames.
        For variable-length sequences, use a custom collate_fn.
        """
        batch = {
            "clip_ids": [s.clip_id for s in samples],
            "frames": torch.stack([
                torch.from_numpy(s.frames).permute(0, 3, 1, 2).float() / 255.0
                for s in samples
            ]),
        }
        
        if samples[0].hand_poses is not None:
            batch["hand_poses"] = torch.stack([
                torch.from_numpy(s.hand_poses).float() for s in samples
            ])
        
        if samples[0].actions is not None:
            batch["actions"] = torch.stack([
                torch.from_numpy(s.actions).long() for s in samples
            ])
        
        if samples[0].depth_maps is not None:
            batch["depth_maps"] = torch.stack([
                torch.from_numpy(s.depth_maps).float() for s in samples
            ])
        
        if samples[0].object_masks is not None:
            batch["object_masks"] = torch.stack([
                torch.from_numpy(s.object_masks).long() for s in samples
            ])
        
        return batch
    
    @property
    def tasks(self) -> list[str]:
        """Get list of unique tasks in this dataset."""
        tasks = set()
        for clip_path in self.clips:
            metadata_file = clip_path / "metadata.json"
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)
                if "task" in metadata:
                    tasks.add(metadata["task"])
        return sorted(tasks)
    
    @property  
    def stats(self) -> dict:
        """Get dataset statistics."""
        total_frames = 0
        total_duration = 0.0
        
        for clip_path in self.clips:
            metadata_file = clip_path / "metadata.json"
            if metadata_file.exists():
                import json
                with open(metadata_file) as f:
                    metadata = json.load(f)
                total_frames += metadata.get("num_frames", 0)
                total_duration += metadata.get("duration", 0.0)
        
        return {
            "num_clips": len(self.clips),
            "total_frames": total_frames,
            "total_duration_seconds": total_duration,
            "total_duration_hours": total_duration / 3600,
        }


class KitchenDataset(ManipulationDataset):
    """
    Dataset for kitchen manipulation tasks.
    
    Available tasks:
        - crack_egg
        - pour_liquid
        - chop_vegetable
        - stir_pot
        - plate_food
        - use_utensil
    """
    
    DATASET_NAME = "kitchen-v1"
    
    def __init__(
        self,
        root: Optional[str | Path] = None,
        split: Literal["train", "val", "test"] = "train",
        task: Optional[str] = None,
        transform: Optional[Callable] = None,
        download: bool = False,
    ):
        if root is None:
            root = Path.home() / ".manipulationdata" / "datasets" / self.DATASET_NAME
        
        if download and not Path(root).exists():
            from terso.download import download_dataset
            download_dataset(self.DATASET_NAME, root)
        
        super().__init__(root, split, task, transform)


class BaristaDataset(ManipulationDataset):
    """
    Dataset for barista/coffee manipulation tasks.
    
    Available tasks:
        - pull_espresso
        - steam_milk
        - pour_latte_art
        - pour_over
        - clean_portafilter
        - tamp_grounds
    """
    
    DATASET_NAME = "barista-v1"
    
    def __init__(
        self,
        root: Optional[str | Path] = None,
        split: Literal["train", "val", "test"] = "train",
        task: Optional[str] = None,
        transform: Optional[Callable] = None,
        download: bool = False,
    ):
        if root is None:
            root = Path.home() / ".manipulationdata" / "datasets" / self.DATASET_NAME
        
        if download and not Path(root).exists():
            from terso.download import download_dataset
            download_dataset(self.DATASET_NAME, root)
        
        super().__init__(root, split, task, transform)
