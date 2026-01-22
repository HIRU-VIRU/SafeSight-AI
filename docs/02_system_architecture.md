
## 2. System Architecture

The SafeSight AI system is designed as a modular, real-time computer vision pipeline that processes live CCTV video feeds to automatically detect safety gear violations on construction sites. The architecture emphasizes scalability, low latency, and reliability to ensure continuous monitoring across multiple cameras and work zones.

### 2.1 High-Level Overview

At a high level, the system ingests live video streams from existing CCTV cameras, performs frame-by-frame analysis using deep learning models, applies rule-based violation logic, and generates logs and alerts when safety non-compliance is detected.

The architecture follows a linear yet modular flow, allowing individual components to be upgraded or optimized independently without impacting the overall system.

### 2.2 Architectural Components

#### 2.2.1 Video Ingestion Module
This module is responsible for connecting to CCTV feeds using standard video stream protocols and extracting frames at a controlled frame rate suitable for real-time processing. Frame sampling is used to balance detection accuracy and computational efficiency.

**Responsibilities:**
- Connect to live CCTV feeds
- Extract frames at configurable intervals
- Forward frames to the processing pipeline

---

#### 2.2.2 Frame Processing Engine
The frame processing engine prepares raw video frames for inference. This includes resizing, normalization, and basic preprocessing required by the detection models.

**Responsibilities:**
- Frame resizing and normalization
- Handling varying camera resolutions
- Ensuring consistency across inputs

---

#### 2.2.3 Person Detection Module
This module detects human presence in each frame. Identifying workers is a prerequisite for safety gear verification, as safety rules apply only to detected persons and not to the background environment.

**Responsibilities:**
- Detect multiple persons per frame
- Generate bounding boxes for each detected worker
- Filter non-relevant objects

---

#### 2.2.4 Safety Gear Detection Module
Once persons are detected, this module identifies the presence or absence of mandatory safety equipment, specifically safety helmets and harnesses. Detection is performed using object detection techniques capable of handling partial visibility and occlusions.

**Responsibilities:**
- Detect helmets and harnesses
- Associate detected gear with individual workers
- Output confidence scores for each detection

---

#### 2.2.5 Violation Logic Engine
The violation logic engine applies predefined safety rules to determine whether a detected worker is in compliance. If mandatory gear is missing, the engine classifies the event as a safety violation.

**Responsibilities:**
- Evaluate compliance rules
- Minimize false negatives
- Generate violation events with metadata

---

#### 2.2.6 Logging and Alert Module
This module records detected violations and triggers real-time alerts. Logged data serves both immediate safety enforcement and long-term compliance analysis.

**Responsibilities:**
- Store violation records with timestamps
- Save visual evidence (frame snapshots)
- Trigger alerts to supervisors or monitoring systems

---

### 2.3 System Characteristics

- **Real-Time Operation:** Designed to operate continuously with minimal latency.
- **Scalability:** Supports multiple camera feeds through parallel processing.
- **Modularity:** Each component can be improved independently.
- **Fault Tolerance:** Temporary failures in one module do not halt the entire system.

### 2.4 Deployment Perspective

The architecture supports deployment on on-site servers or edge devices close to CCTV infrastructure to reduce network latency and ensure reliable real-time performance. Cloud integration may be added in future phases for centralized monitoring and analytics.

---

This architecture provides a robust foundation for automated, real-time safety compliance monitoring and serves as the basis for subsequent model development and system implementation.
