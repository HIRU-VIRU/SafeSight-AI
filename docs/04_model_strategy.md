
## 4. Model Strategy

The SafeSight AI system adopts an object detection–based approach for identifying safety gear compliance in construction sites. This strategy is chosen to meet real-time performance requirements while accurately handling complex visual scenes involving multiple workers, partial occlusions, and varying camera angles.

### 4.1 Choice of Detection over Classification

Image classification approaches are insufficient for construction site monitoring because:
- Multiple workers may appear in a single frame
- Safety gear may be partially visible or occluded
- The system must associate safety equipment with specific individuals

To address these challenges, object detection is used instead of classification. Object detection enables the system to localize and identify multiple objects within a single frame, making it suitable for real-world surveillance scenarios.

### 4.2 Detection Targets

The model is trained to detect the following object classes:
- **Person**: Represents workers present in the scene
- **Helmet**: Mandatory head protection equipment
- **Harness**: Mandatory fall-protection equipment for height-related work

Detecting these objects allows the system to infer safety compliance by analyzing spatial relationships between detected persons and their corresponding safety gear.

### 4.3 Model Architecture Selection

A YOLO-based (You Only Look Once) object detection architecture is selected due to its balance between detection accuracy and real-time inference speed. YOLO models perform detection in a single forward pass, making them well-suited for live CCTV video analysis.

Key reasons for selecting a YOLO-based approach include:
- High inference speed suitable for real-time systems
- Strong performance on small and medium-sized objects
- Ability to detect multiple objects simultaneously
- Proven effectiveness in surveillance and industrial monitoring tasks

### 4.4 Real-Time Performance Considerations

The model strategy prioritizes minimizing false negatives, especially for missing safety gear, as undetected violations pose significant safety risks. Detection confidence thresholds are tuned conservatively to favor recall over precision when necessary.

To maintain real-time performance:
- Frames may be sampled at a controlled rate
- Model input resolution is optimized
- Inference is performed on each frame independently to avoid temporal dependencies

### 4.5 Association of Safety Gear with Workers

Detected safety gear must be correctly associated with individual workers. This is achieved by analyzing spatial proximity and bounding box overlap between detected persons and detected safety equipment.

A worker is considered compliant only if the required safety gear is detected within the spatial region corresponding to that person. This association logic forms the basis for downstream violation detection.

### 4.6 Model Extensibility

The selected model strategy allows for future extension to additional safety equipment such as safety vests, gloves, or boots without requiring architectural changes. New object classes can be added through dataset expansion and retraining.

---

This model strategy ensures that the SafeSight AI system achieves a practical balance between accuracy, speed, and scalability, making it suitable for real-time deployment in active construction environments.
