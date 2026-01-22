
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
```
SafeSight-AI/
├── docs/
│   ├── 01_problem_statement.md        # Industrial problem definition
│   ├── 02_system_architecture.md      # End-to-end system architecture
│   ├── 03_data_strategy.md            # Dataset sources and preparation strategy
│   ├── 04_model_strategy.md           # Object detection and model design rationale
│   ├── 05_real_time_pipeline.md       # Real-time processing workflow
│   ├── 06_violation_logic.md           # Rule-based safety violation logic
│   ├── 07_evaluation_metrics.md       # Performance and validation metrics
│   └── 08_future_scope.md              # Planned enhancements and extensions
│
├── diagrams/
│   ├── system_architecture.png        # System-level architecture diagram
│   └── real_time_pipeline.png         # Real-time processing pipeline diagram
│
├── reports/
│   └── TN-IMPACT_2026_REPORT_FORMAT.docx   # Official TN-IMPACT report template
│
├── presentations/
│   └── TN-IMPACT_2026_PPT_TEMPLATE.pptx    # Official TN-IMPACT presentation template
│
├── datasets/
│   └── README.md                       # Dataset documentation (future use)
│
├── experiments/
│   └── README.md                       # Experiment tracking (future use)
│
├── logs/
│   └── README.md                       # Violation and system logs (future use)
│
├── README.md                           # Project overview and status
└── LICENSE                             # Project license
```
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

