
# SafeSight AI  
### Real-Time Safety Gear Compliance Monitoring System

SafeSight AI is a proposed computer vision–based system designed to automatically monitor safety compliance on construction sites using existing CCTV infrastructure. The system focuses on detecting workers who are not wearing mandatory safety gear such as helmets and harnesses and generating real-time violation alerts.

This repository currently contains **complete system documentation and design artifacts** prepared as part of the **TN-IMPACT 2026 – Identifying Industrial Challenges** program. Implementation and model development are planned for a later phase.

---

## Problem Overview

Construction sites are high-risk environments where non-compliance with safety regulations can lead to severe injuries and fatalities. Manual monitoring of safety gear usage is inconsistent, error-prone, and difficult to sustain across large sites and multiple work zones.

Although CCTV systems are commonly deployed on construction sites, they are rarely used for proactive safety enforcement. SafeSight AI aims to bridge this gap by leveraging computer vision to automate safety compliance monitoring in real time.

---

## Project Objectives

- Detect workers in live CCTV video feeds
- Identify missing safety gear (helmet and harness)
- Automatically log safety violations with evidence
- Trigger immediate alerts for timely corrective action
- Improve reliability and consistency of safety enforcement

---

## Project Status

**Current Phase:**  
📌 Documentation and system design completed  

**Upcoming Phase:**  
🔧 Dataset preparation, model training, real-time pipeline implementation, and system validation

No implementation code has been added yet by design.

---

## Repository Structure
SafeSight-AI/
├── docs/ # Complete system documentation (finalized)
├── diagrams/ # Architecture and pipeline diagrams
├── reports/ # TN-IMPACT report template and final report
├── presentations/ # TN-IMPACT presentation template and slides
├── datasets/ # Dataset documentation (future use)
├── experiments/ # Experimental tracking (future use)
├── logs/ # Logging structure (future use)
├── README.md
└── LICENSE


---

## Documentation

The `docs/` directory contains finalized markdown documents covering:

- Problem statement
- System architecture
- Model strategy
- Real-time processing pipeline
- Violation logic
- Evaluation metrics
- Data strategy
- Future scope

These documents serve as the authoritative design reference for the project and are used as the basis for the TN-IMPACT report and presentation.

---

## Technology Stack (Planned)

- Python
- OpenCV
- PyTorch
- YOLO-based object detection
- Flask / FastAPI (for integration and alerts)

---

## Intended Impact

SafeSight AI aims to reduce preventable workplace accidents by transforming passive CCTV surveillance into an active, intelligent safety monitoring system. By automating safety compliance checks, the system supports safer construction environments and more effective safety management.

---

## License

This project is released under the MIT License.

---

## Note

This repository intentionally contains **no implementation code at this stage**.  
All design decisions have been finalized and frozen prior to development to ensure a clean and well-justified build phase.

