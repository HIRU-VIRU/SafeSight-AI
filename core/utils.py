"""
Utility functions for SafeSight AI.
"""

import cv2
import numpy as np
from typing import Tuple, List


def resize_maintain_aspect(image: np.ndarray, target_size: int) -> np.ndarray:
    """
    Resize image maintaining aspect ratio.
    
    Args:
        image: Input image
        target_size: Target size for longest dimension
        
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    scale = target_size / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h))


def draw_bbox(image: np.ndarray, bbox: List[float], 
              color: Tuple[int, int, int], 
              label: str = None, 
              thickness: int = 2) -> np.ndarray:
    """
    Draw bounding box on image.
    
    Args:
        image: Input image
        bbox: [x1, y1, x2, y2]
        color: BGR color tuple
        label: Optional label text
        thickness: Line thickness
        
    Returns:
        Image with drawn bbox
    """
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    if label:
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        cv2.rectangle(image, (x1, y1 - label_h - 10), 
                     (x1 + label_w, y1), color, -1)
        cv2.putText(image, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return image


def calculate_overlap_percentage(bbox1: List[float], bbox2: List[float]) -> float:
    """
    Calculate what percentage of bbox1 is covered by bbox2.
    
    Args:
        bbox1: [x1, y1, x2, y2]
        bbox2: [x1, y1, x2, y2]
        
    Returns:
        Percentage overlap (0.0 to 1.0)
    """
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2
    
    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection_area = (x2_i - x1_i) * (y2_i - y1_i)
    bbox1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    
    if bbox1_area == 0:
        return 0.0
    
    return intersection_area / bbox1_area


def format_timestamp(timestamp: float = None) -> str:
    """
    Format timestamp as readable string.
    
    Args:
        timestamp: Unix timestamp (default: now)
        
    Returns:
        Formatted string
    """
    from datetime import datetime
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_video_source(source) -> bool:
    """
    Validate video source can be opened.
    
    Args:
        source: Video source (int, path, or URL)
        
    Returns:
        True if valid, False otherwise
    """
    cap = cv2.VideoCapture(source)
    is_opened = cap.isOpened()
    cap.release()
    return is_opened


def create_summary_image(violations: List[dict], 
                        storage_path: str,
                        max_images: int = 4) -> np.ndarray:
    """
    Create summary image grid from violation images.
    
    Args:
        violations: List of violation dictionaries with image_path
        storage_path: Base storage path
        max_images: Maximum images in grid
        
    Returns:
        Combined grid image
    """
    from pathlib import Path
    
    images = []
    for violation in violations[:max_images]:
        img_path = Path(storage_path).parent / violation.get('image_path', '')
        if img_path.exists():
            img = cv2.imread(str(img_path))
            if img is not None:
                # Resize to standard size
                img = cv2.resize(img, (300, 300))
                
                # Add violation info
                person_id = violation.get('person_id', '?')
                cv2.putText(img, f"Person {person_id}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                images.append(img)
    
    if not images:
        return None
    
    # Create grid
    rows = (len(images) + 1) // 2
    grid = []
    for i in range(0, len(images), 2):
        if i + 1 < len(images):
            row = np.hstack([images[i], images[i+1]])
        else:
            row = images[i]
        grid.append(row)
    
    if grid:
        return np.vstack(grid)
    
    return None
