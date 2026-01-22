
## 5. Real-Time Processing Pipeline

The SafeSight AI system operates as a continuous real-time pipeline designed to analyze live CCTV feeds and detect safety gear violations with minimal latency. The pipeline is optimized to balance detection accuracy, computational efficiency, and system reliability.

### 5.1 Pipeline Overview

The real-time pipeline follows a sequential flow where each stage performs a specific function and passes its output to the next stage. This design ensures clarity, modularity, and ease of optimization.

The pipeline processes video streams continuously during site operation hours and is capable of handling multiple camera feeds in parallel.

### 5.2 Frame Acquisition

Live video streams are captured from CCTV cameras using standard streaming protocols. Frames are extracted at a configurable frame rate to ensure real-time responsiveness while avoiding unnecessary computational load.

Key considerations:
- Frame rate is adjustable based on hardware capability
- Video resolution is normalized for consistent processing
- Frame drops are handled gracefully without system failure

### 5.3 Frame Preprocessing

Each extracted frame undergoes preprocessing to prepare it for inference by the detection models. Preprocessing ensures uniformity across inputs from different cameras.

Preprocessing steps include:
- Frame resizing to model input dimensions
- Pixel normalization
- Noise and lighting normalization where applicable

### 5.4 Person Detection Stage

The preprocessed frame is first passed through the person detection stage. This stage identifies all workers present in the scene and generates bounding boxes for each detected individual.

This step reduces unnecessary computation by restricting safety gear analysis to regions containing detected persons.

### 5.5 Safety Gear Detection Stage

For each frame, safety gear detection is performed to identify helmets and harnesses. The detection model outputs bounding boxes and confidence scores for each detected safety item.

This stage is designed to handle:
- Partial visibility of equipment
- Occlusions caused by body posture or other workers
- Variations in camera angle and distance

### 5.6 Association and Compliance Evaluation

Detected safety gear is spatially associated with detected persons using bounding box overlap and proximity analysis. Each worker is evaluated independently to determine safety compliance.

A worker is marked as non-compliant if mandatory safety gear is not detected within the associated region.

### 5.7 Violation Event Generation

When a safety violation is identified, a violation event is generated. This event contains all necessary metadata for logging and alerting.

Violation event data includes:
- Timestamp
- Camera identifier
- Detected violation type
- Detection confidence
- Frame reference for evidence

### 5.8 Continuous Operation and Optimization

The pipeline is designed for uninterrupted operation during working hours. Performance metrics such as processing latency and frame throughput are monitored to ensure real-time performance is maintained.

The modular design allows individual stages to be optimized or replaced without disrupting the entire pipeline.

---

This real-time pipeline forms the operational backbone of the SafeSight AI system and ensures timely detection and response to safety compliance violations.
