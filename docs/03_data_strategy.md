

## 3. Data Strategy

A robust data strategy is essential to ensure accurate and reliable detection of safety compliance in real-world construction environments. The SafeSight AI system is designed to be trained and evaluated on diverse, representative visual data that reflects the variability present in live CCTV feeds.

### 3.1 Data Sources

The system leverages multiple data sources to achieve comprehensive coverage of construction site scenarios:

- Publicly available personal protective equipment (PPE) detection datasets
- Annotated images and video frames from construction environments
- Extracted frames from recorded CCTV footage where available

These sources collectively provide diversity in worker appearance, safety gear types, camera angles, and environmental conditions.

### 3.2 Data Classes

The dataset is annotated with the following object classes:

- **Person**
- **Helmet**
- **Harness**

These classes directly align with the detection and compliance requirements of the system.

### 3.3 Data Annotation

Annotations are performed using bounding boxes around each object of interest. Object detection annotation formats compatible with common detection frameworks are used to facilitate training and evaluation.

Annotation guidelines ensure:
- Accurate localization of objects
- Consistent labeling across datasets
- Correct handling of partially visible objects

### 3.4 Data Diversity and Coverage

To ensure robustness, the dataset captures variations in:

- Lighting conditions (daylight, low-light, shadows)
- Camera viewpoints (top-down, side angles, oblique views)
- Worker posture and movement
- Occlusions caused by equipment or other workers
- Different helmet and harness designs

### 3.5 Data Augmentation

Data augmentation techniques are applied to improve model generalization and reduce overfitting. Augmentation strategies include:

- Image scaling and rotation
- Motion blur simulation
- Brightness and contrast adjustments
- Noise injection
- Random occlusion

These techniques help simulate real-world CCTV conditions and enhance detection reliability.

### 3.6 Dataset Splitting

The dataset is split into training, validation, and testing subsets to ensure unbiased performance evaluation. Care is taken to avoid overlap between frames from the same video sequence across different splits.

### 3.7 Ethical and Privacy Considerations

All data used for training and evaluation is handled responsibly. The system focuses on detecting safety compliance without performing worker identification or biometric recognition, thereby minimizing privacy concerns.

---

This data strategy ensures that the SafeSight AI system is trained on representative and diverse data, enabling reliable performance across a wide range of construction site scenarios.
