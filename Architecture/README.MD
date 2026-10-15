# Architecture Specifications

This folder contains the authoritative architecture diagrams and code-driven specifications for **Yukti**.

## Available Diagrams

- 📋 [**System Overview**](./SystemOverview.md) — High-level end-to-end data processing and reasoning flow
- 🧩 [**Component Diagram**](./ComponentDiagram.md) — Modular classes, DTOs, and component boundaries
- 🔄 [**Execution Flow Diagram**](./FlowDiagram.md) — Execution step lifecycle from ingestion to SMT verdict
- ⏱️ [**Sequence Diagram**](./SequenceDiagram.md) — Chronological runtime interactions between components

## Synchronizing Architecture

To regenerate or verify the architecture documentation from code, run:

```bash
python3 Architecture/architectureSync.py
```
