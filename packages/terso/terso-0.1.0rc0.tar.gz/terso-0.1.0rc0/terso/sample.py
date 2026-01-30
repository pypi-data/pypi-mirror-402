"""
Sample class representing a single manipulation video clip with annotations.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch


@dataclass
class Sample:
    """
    A single manipulation video sample with annotations.
    
    Attributes:
        clip_id: Unique identifier for this clip
        frames: Video frames (T, H, W, 3) as uint8 numpy array
        hand_poses: Hand keypoints (T, 2, 21, 3) - [frame, hand, keypoint, xyz]
        actions: Action labels per frame (T,) as int array
        depth_maps: Monocular depth estimates (T, H, W) as float32
        object_masks: Object segmentation masks (T, H, W) as uint8 (class ids)
        metadata: Additional metadata dict
    """
    
    clip_id: str
    frames: np.ndarray
    hand_poses: Optional[np.ndarray] = None
    actions: Optional[np.ndarray] = None
    depth_maps: Optional[np.ndarray] = None
    object_masks: Optional[np.ndarray] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        """Validate sample data."""
        if self.frames.ndim != 4:
            raise ValueError(f"frames must be 4D (T, H, W, C), got {self.frames.ndim}D")
        
        T, H, W, C = self.frames.shape
        
        if self.hand_poses is not None and self.hand_poses.shape[0] != T:
            raise ValueError(f"hand_poses frames ({self.hand_poses.shape[0]}) != video frames ({T})")
        
        if self.actions is not None and self.actions.shape[0] != T:
            raise ValueError(f"actions frames ({self.actions.shape[0]}) != video frames ({T})")
        
        if self.depth_maps is not None and self.depth_maps.shape[0] != T:
            raise ValueError(f"depth_maps frames ({self.depth_maps.shape[0]}) != video frames ({T})")
    
    @property
    def num_frames(self) -> int:
        """Number of frames in the clip."""
        return self.frames.shape[0]
    
    @property
    def resolution(self) -> tuple[int, int]:
        """Video resolution as (height, width)."""
        return self.frames.shape[1], self.frames.shape[2]
    
    @property
    def fps(self) -> Optional[float]:
        """Frames per second if available in metadata."""
        if self.metadata:
            return self.metadata.get("fps")
        return None
    
    @property
    def duration(self) -> Optional[float]:
        """Duration in seconds if fps is available."""
        if self.fps:
            return self.num_frames / self.fps
        return None
    
    def to_tensors(self, device: str = "cpu") -> dict[str, torch.Tensor]:
        """
        Convert sample to PyTorch tensors.
        
        Args:
            device: Device to place tensors on
            
        Returns:
            Dict with tensor versions of all arrays
        """
        result = {
            "frames": torch.from_numpy(self.frames).permute(0, 3, 1, 2).float() / 255.0,
        }
        
        if self.hand_poses is not None:
            result["hand_poses"] = torch.from_numpy(self.hand_poses).float()
        
        if self.actions is not None:
            result["actions"] = torch.from_numpy(self.actions).long()
        
        if self.depth_maps is not None:
            result["depth_maps"] = torch.from_numpy(self.depth_maps).float()
        
        if self.object_masks is not None:
            result["object_masks"] = torch.from_numpy(self.object_masks).long()
        
        return {k: v.to(device) for k, v in result.items()}
    
    def get_frame(self, idx: int) -> np.ndarray:
        """Get a single frame by index."""
        return self.frames[idx]
    
    def get_hand_pose(self, idx: int) -> Optional[np.ndarray]:
        """Get hand pose for a single frame."""
        if self.hand_poses is None:
            return None
        return self.hand_poses[idx]
    
    def get_action(self, idx: int) -> Optional[int]:
        """Get action label for a single frame."""
        if self.actions is None:
            return None
        return int(self.actions[idx])
    
    @classmethod
    def from_directory(cls, path: Path) -> "Sample":
        """
        Load a sample from a directory containing annotation files.
        
        Expected structure:
            clip_dir/
            ├── frames/          # or video.mp4
            │   ├── 000000.jpg
            │   ├── 000001.jpg
            │   └── ...
            ├── hand_poses.npy
            ├── actions.npy
            ├── depth_maps.npy
            ├── object_masks.npy
            └── metadata.json
        """
        import json
        import cv2
        
        path = Path(path)
        
        # Load frames
        frames_dir = path / "frames"
        video_path = path / "video.mp4"
        
        if frames_dir.exists():
            frame_files = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.png"))
            frames = np.stack([cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB) 
                              for f in frame_files])
        elif video_path.exists():
            cap = cv2.VideoCapture(str(video_path))
            frames_list = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames_list.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            cap.release()
            frames = np.stack(frames_list)
        else:
            raise FileNotFoundError(f"No frames or video found in {path}")
        
        # Load annotations
        hand_poses = None
        if (path / "hand_poses.npy").exists():
            hand_poses = np.load(path / "hand_poses.npy")
        
        actions = None
        if (path / "actions.npy").exists():
            actions = np.load(path / "actions.npy")
        
        depth_maps = None
        if (path / "depth_maps.npy").exists():
            depth_maps = np.load(path / "depth_maps.npy")
        
        object_masks = None
        if (path / "object_masks.npy").exists():
            object_masks = np.load(path / "object_masks.npy")
        
        metadata = None
        if (path / "metadata.json").exists():
            with open(path / "metadata.json") as f:
                metadata = json.load(f)
        
        return cls(
            clip_id=path.name,
            frames=frames,
            hand_poses=hand_poses,
            actions=actions,
            depth_maps=depth_maps,
            object_masks=object_masks,
            metadata=metadata,
        )
    
    def save(self, path: Path, save_frames_as: str = "video") -> None:
        """
        Save sample to a directory.
        
        Args:
            path: Directory to save to
            save_frames_as: "video" or "images"
        """
        import json
        import cv2
        
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save frames
        if save_frames_as == "video":
            video_path = path / "video.mp4"
            T, H, W, C = self.frames.shape
            fps = self.fps or 30.0
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(video_path), fourcc, fps, (W, H))
            for frame in self.frames:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            writer.release()
        else:
            frames_dir = path / "frames"
            frames_dir.mkdir(exist_ok=True)
            for i, frame in enumerate(self.frames):
                cv2.imwrite(str(frames_dir / f"{i:06d}.jpg"), 
                           cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        
        # Save annotations
        if self.hand_poses is not None:
            np.save(path / "hand_poses.npy", self.hand_poses)
        
        if self.actions is not None:
            np.save(path / "actions.npy", self.actions)
        
        if self.depth_maps is not None:
            np.save(path / "depth_maps.npy", self.depth_maps)
        
        if self.object_masks is not None:
            np.save(path / "object_masks.npy", self.object_masks)
        
        if self.metadata is not None:
            with open(path / "metadata.json", "w") as f:
                json.dump(self.metadata, f, indent=2)
