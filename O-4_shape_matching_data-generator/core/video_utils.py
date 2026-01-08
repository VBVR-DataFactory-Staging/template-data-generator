"""Video generation utilities - Generic framework code (DO NOT MODIFY)."""

from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

# Check if cv2 is available
import importlib.util

CV2_AVAILABLE = importlib.util.find_spec("cv2") is not None

if CV2_AVAILABLE:
    import cv2
    import numpy as np
else:
    cv2 = None
    np = None
    print("⚠️  Warning: opencv-python not installed. Video generation disabled.")
    print("   Install with: pip install opencv-python==4.8.1.78")


class VideoGenerator:
    """
    Generate videos from image sequences.
    
    This is a generic utility class - use it in your custom generator.
    """
    
    def __init__(self, fps: int = 10, output_format: str = "mp4"):
        """
        Initialize video generator.
        
        Args:
            fps: Frames per second
            output_format: Video format - "mp4" (recommended) or "avi"
        """
        self.fps = fps
        self.output_format = output_format
        
        # Use H.264 for mp4 (better compatibility) or XVID for avi
        if output_format == "mp4":
            self.codec = 'mp4v'  # Most compatible mp4 codec
            self.extension = '.mp4'
        else:
            self.codec = 'XVID'
            self.extension = '.avi'
        
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python is required for video generation")
    
    @staticmethod
    def is_available() -> bool:
        """Check if video generation is available."""
        return CV2_AVAILABLE
    
    def create_video_from_frames(
        self,
        frames: List[Image.Image],
        output_path: Path,
        size: Optional[Tuple[int, int]] = None
    ) -> Path:
        """
        Create video from PIL Image frames.
        
        Args:
            frames: List of PIL Images
            output_path: Path to save video (extension will be corrected)
            size: Optional (width, height) tuple. If None, uses first frame size
            
        Returns:
            Path to created video file
        """
        if not frames:
            raise ValueError("No frames provided")
        
        # Get video size
        if size is None:
            size = frames[0].size
        
        width, height = size
        
        # Ensure correct extension
        output_path = Path(output_path)
        output_path = output_path.with_suffix(self.extension)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        
        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            self.fps,
            (width, height)
        )
        
        # Write frames
        for frame in frames:
            # Ensure RGB and correct size
            if frame.size != size:
                frame = frame.resize(size, Image.Resampling.LANCZOS)
            
            # Convert PIL Image to OpenCV format (BGR)
            frame_rgb = frame.convert('RGB')
            frame_array = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            writer.write(frame_bgr)
        
        writer.release()
        return output_path
    
    def create_crossfade_video(
        self,
        start_image: Image.Image,
        end_image: Image.Image,
        output_path: Path,
        hold_frames: int = 5,
        transition_frames: int = 15
    ) -> Optional[Path]:
        """
        Create video with smooth cross-fade transition between two images.
        
        Args:
            start_image: Initial image
            end_image: Final image
            output_path: Path to save video
            hold_frames: Frames to hold at start and end
            transition_frames: Frames for transition
            
        Returns:
            Path to video file, or None if cv2 not available
        """
        if not CV2_AVAILABLE:
            return None
        
        frames = []
        
        # Hold initial position
        for _ in range(hold_frames):
            frames.append(start_image.copy())
        
        # Smooth cross-fade transition
        start_rgba = start_image.convert('RGBA')
        end_rgba = end_image.convert('RGBA')
        
        # Ensure same size
        if start_rgba.size != end_rgba.size:
            end_rgba = end_rgba.resize(start_rgba.size, Image.Resampling.LANCZOS)
        
        for i in range(transition_frames):
            alpha = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            blended = Image.blend(start_rgba, end_rgba, alpha)
            frames.append(blended.convert('RGB'))
        
        # Hold final position
        for _ in range(hold_frames):
            frames.append(end_image.copy())
        
        return self.create_video_from_frames(frames, output_path)
    
    def create_sliding_fade_video(
        self,
        start_image: Image.Image,
        end_image: Image.Image,
        output_path: Path,
        hold_frames: int = 5,
        transition_frames: int = 15
    ) -> Optional[Path]:
        """
        Create video with sliding transition where pieces fade out then fade in.
        
        The piece slides smoothly from start to end position, but also:
        - Fades out (becomes transparent) in the first half
        - Fades in (becomes opaque) in the second half
        
        Args:
            start_image: Initial image
            end_image: Final image
            output_path: Path to save video
            hold_frames: Frames to hold at start and end
            transition_frames: Frames for transition
            
        Returns:
            Path to video file, or None if cv2 not available
        """
        if not CV2_AVAILABLE:
            return None
        
        frames = []
        
        # Hold initial position
        for _ in range(hold_frames):
            frames.append(start_image.copy())
        
        # Sliding transition with fade out/fade in
        start_rgba = start_image.convert('RGBA')
        end_rgba = end_image.convert('RGBA')
        
        # Ensure same size
        if start_rgba.size != end_rgba.size:
            end_rgba = end_rgba.resize(start_rgba.size, Image.Resampling.LANCZOS)
        
        for i in range(transition_frames):
            # Progress through transition (0 to 1)
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            
            # Fade curve: fade out in first half, fade in in second half
            # Creates a dip in opacity in the middle
            if progress < 0.5:
                # Fading out: opacity goes from 1.0 to 0.2
                opacity = 1.0 - (progress * 2) * 0.8
            else:
                # Fading in: opacity goes from 0.2 to 1.0
                opacity = 0.2 + ((progress - 0.5) * 2) * 0.8
            
            # Blend the positions (sliding motion)
            blended = Image.blend(start_rgba, end_rgba, progress)
            
            # Apply opacity effect by blending with semi-transparent version
            transparent = Image.new('RGBA', blended.size, (0, 0, 0, 0))
            faded = Image.blend(transparent, blended, opacity)
            
            frames.append(faded.convert('RGB'))
        
        # Hold final position
        for _ in range(hold_frames):
            frames.append(end_image.copy())
        
        return self.create_video_from_frames(frames, output_path)
    
    def interpolate_frames(
        self,
        start_frame: Image.Image,
        end_frame: Image.Image,
        num_intermediate: int = 10
    ) -> List[Image.Image]:
        """
        Create smooth transition between two frames using alpha blending.
        
        Args:
            start_frame: Initial frame
            end_frame: Final frame
            num_intermediate: Number of intermediate frames to generate
            
        Returns:
            List of frames including start, intermediates, and end
        """
        frames = [start_frame]
        
        # Ensure same size and mode
        if start_frame.size != end_frame.size:
            end_frame = end_frame.resize(start_frame.size, Image.Resampling.LANCZOS)
        
        start_frame = start_frame.convert('RGBA')
        end_frame = end_frame.convert('RGBA')
        
        # Generate intermediate frames
        for i in range(1, num_intermediate + 1):
            alpha = i / (num_intermediate + 1)
            blended = Image.blend(start_frame, end_frame, alpha)
            frames.append(blended.convert('RGB'))
        
        frames.append(end_frame.convert('RGB'))
        return frames
