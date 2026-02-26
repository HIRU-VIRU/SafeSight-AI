"""
Evidence storage service for SafeSight AI.
Manages saving violation images with organized folder structure.
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional
from config.settings import STORAGE_PATH


class EvidenceStorage:
    """
    Manages storage of violation evidence images.
    Creates date-based folder structure and saves cropped violation images.
    """
    
    def __init__(self, base_path: str = STORAGE_PATH):
        """
        Initialize evidence storage service.
        
        Args:
            base_path: Base directory for violation storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_date_folder(self) -> Path:
        """
        Get today's date-based folder path.
        Creates folder if it doesn't exist.
        
        Returns:
            Path to today's folder (YYYY-MM-DD format)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        date_folder = self.base_path / today
        date_folder.mkdir(parents=True, exist_ok=True)
        return date_folder
    
    def _generate_filename(self, camera_id: str, person_id: int) -> str:
        """
        Generate filename for violation image.
        
        Format: camera1_2026-02-25_15-34-22_person3.jpg
        
        Args:
            camera_id: Camera identifier
            person_id: Tracked person ID
            
        Returns:
            Filename string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{camera_id}_{timestamp}_person{person_id}.jpg"
        return filename
    
    def save_violation_image(self, frame: np.ndarray, 
                            bbox: list,
                            camera_id: str, 
                            person_id: int,
                            crop: bool = True) -> str:
        """
        Save violation image to storage.
        
        Args:
            frame: Full video frame as numpy array
            bbox: Bounding box [x1, y1, x2, y2] of the violation
            camera_id: Camera identifier
            person_id: Tracked person ID
            crop: Whether to crop to bbox (default True)
            
        Returns:
            Relative path to saved image file
        """
        try:
            date_folder = self._get_date_folder()
            filename = self._generate_filename(camera_id, person_id)
            file_path = date_folder / filename
            
            if crop and bbox:
                # Crop image to bounding box
                x1, y1, x2, y2 = map(int, bbox)
                
                # Ensure coordinates are within frame bounds
                h, w = frame.shape[:2]
                x1 = max(0, min(x1, w))
                y1 = max(0, min(y1, h))
                x2 = max(0, min(x2, w))
                y2 = max(0, min(y2, h))
                
                # Add small margin around person
                margin = 10
                x1 = max(0, x1 - margin)
                y1 = max(0, y1 - margin)
                x2 = min(w, x2 + margin)
                y2 = min(h, y2 + margin)
                
                cropped_frame = frame[y1:y2, x1:x2]
                
                if cropped_frame.size == 0:
                    # Fallback to full frame if crop failed
                    image_to_save = frame
                else:
                    image_to_save = cropped_frame
            else:
                image_to_save = frame
            
            # Save image
            cv2.imwrite(str(file_path), image_to_save)
            
            # Return relative path from base storage path
            relative_path = str(file_path.relative_to(self.base_path.parent))
            return relative_path
            
        except Exception as e:
            print(f"❌ Error saving violation image: {e}")
            return ""
    
    def save_full_frame(self, frame: np.ndarray,
                       camera_id: str,
                       person_id: int) -> str:
        """
        Save full frame without cropping.
        
        Args:
            frame: Full video frame
            camera_id: Camera identifier
            person_id: Person ID
            
        Returns:
            Path to saved image
        """
        return self.save_violation_image(frame, None, camera_id, person_id, crop=False)
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage information
        """
        total_images = sum(1 for _ in self.base_path.rglob("*.jpg"))
        total_size_bytes = sum(f.stat().st_size for f in self.base_path.rglob("*.jpg"))
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        return {
            "base_path": str(self.base_path),
            "total_images": total_images,
            "total_size_mb": round(total_size_mb, 2)
        }
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> int:
        """
        Remove violation images older than specified days.
        
        Args:
            days_to_keep: Number of days to keep files
            
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for image_file in self.base_path.rglob("*.jpg"):
            file_time = datetime.fromtimestamp(image_file.stat().st_mtime)
            if file_time < cutoff_date:
                image_file.unlink()
                deleted_count += 1
        
        print(f"🗑️  Cleaned up {deleted_count} old files")
        return deleted_count
