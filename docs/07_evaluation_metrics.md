
## 7. Evaluation Metrics

The performance of the SafeSight AI system is evaluated using a combination of detection accuracy metrics and real-time operational metrics. These metrics ensure that the system is not only accurate but also suitable for continuous real-world deployment in construction environments.

### 7.1 Detection Accuracy Metrics

#### 7.1.1 Precision
Precision measures the proportion of detected safety violations that are actually correct.

High precision ensures that the system does not generate excessive false alarms, which could lead to alert fatigue among site supervisors.

#### 7.1.2 Recall
Recall measures the proportion of actual safety violations that are successfully detected by the system.

Recall is a critical metric for this application, as missed detections (false negatives) may result in serious safety risks. The system prioritizes high recall, especially for missing helmet and harness detection.

#### 7.1.3 Mean Average Precision (mAP)
Mean Average Precision evaluates overall object detection performance across all detected classes, including persons, helmets, and harnesses.

mAP provides a standardized measure of detection quality and is used to compare different model configurations during development.

### 7.2 Violation Detection Metrics

#### 7.2.1 False Negative Rate
The false negative rate represents the frequency at which actual safety violations are not detected.

This metric is closely monitored and minimized, as undetected violations undermine the primary objective of the system.

#### 7.2.2 False Positive Rate
The false positive rate measures how often compliant workers are incorrectly flagged as violating safety rules.

While false positives are less critical than false negatives, excessive false alerts can reduce trust in the system and must be controlled through threshold tuning and temporal filtering.

### 7.3 Real-Time Performance Metrics

#### 7.3.1 Frames Per Second (FPS)
FPS measures how many video frames the system can process per second. Maintaining an adequate FPS is essential to ensure real-time responsiveness.

The target FPS is selected based on practical monitoring needs and available hardware resources.

#### 7.3.2 End-to-End Latency
End-to-end latency measures the time taken from frame capture to violation alert generation.

Low latency ensures that corrective action can be taken immediately after a violation is detected.

### 7.4 System Reliability Metrics

- System uptime during operational hours
- Stability under continuous load
- Graceful handling of dropped frames or temporary stream interruptions

### 7.5 Evaluation Strategy

Evaluation is performed on annotated validation datasets as well as recorded CCTV footage representative of real construction environments. Performance is assessed under varying lighting conditions, camera angles, and worker densities to ensure robustness.

---

These evaluation metrics provide a comprehensive framework for validating both the technical accuracy and real-time suitability of the SafeSight AI system.
