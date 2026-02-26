"""
Detection Parser for SafeSight AI.
Converts YOLO model output into structured detection objects.
"""

from typing import List, Dict, Any
import numpy as np
from config.settings import CLASS_NAMES, CONF_THRESHOLD


class DetectionParser:
    """Parses YOLO model output into structured detection dictionaries."""
    
    def __init__(self, conf_threshold: float = CONF_THRESHOLD):
        """
        Initialize detection parser.
        
        Args:
            conf_threshold: Minimum confidence score for detections
        """
        self.conf_threshold = conf_threshold
        self.class_names = CLASS_NAMES
    
    def parse(self, results: Any) -> List[Dict[str, Any]]:
        """
        Parse YOLO results into structured detection objects.
        
        Args:
            results: YOLO model output (ultralytics Results object)
            
        Returns:
            List of detection dictionaries with format:
            [
                {
                    "class": "Person",
                    "confidence": 0.92,
                    "bbox": [x1, y1, x2, y2]
                }
            ]
        """
        detections = []
        
        # Extract boxes from YOLO results
        if len(results) == 0:
            return detections
        
        result = results[0]  # First result (single image/frame)
        
        if result.boxes is None or len(result.boxes) == 0:
            return detections
        
        boxes = result.boxes
        
        # Process each detection
        for box in boxes:
            confidence = float(box.conf[0])
            
            # Filter by confidence threshold
            if confidence < self.conf_threshold:
                continue
            
            class_id = int(box.cls[0])
            class_name = self.class_names.get(class_id, f"Unknown_{class_id}")
            
            # Get bounding box coordinates (xyxy format)
            bbox = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(float, bbox)
            
            detection = {
                "class": class_name,
                "class_id": class_id,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            }
            
            detections.append(detection)
        
        return detections
    
    def filter_by_class(self, detections: List[Dict[str, Any]], 
                       class_name: str) -> List[Dict[str, Any]]:
        """
        Filter detections by class name.
        
        Args:
            detections: List of detection dictionaries
            class_name: Class name to filter for
            
        Returns:
            Filtered list of detections
        """
        return [d for d in detections if d["class"] == class_name]
    
    def get_persons(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all Person detections."""
        return self.filter_by_class(detections, "Person")
    
    def get_ppe(self, detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize PPE detections by type.
        
        Args:
            detections: List of all detections
            
        Returns:
            Dictionary mapping PPE type to list of detections:
            {
                "helmet": [...],
                "vest": [...],
                "boots": [...],
                "gloves": [...],
                "goggles": [...]
            }
        """
        ppe_types = ["helmet", "vest", "boots", "gloves", "goggles"]
        ppe_detections = {}
        
        for ppe_type in ppe_types:
            ppe_detections[ppe_type] = self.filter_by_class(detections, ppe_type)
        
        return ppe_detections
