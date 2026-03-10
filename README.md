# BioRxnReasoner

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Status](https://img.shields.io/badge/Status-Research-orange)
![Task](https://img.shields.io/badge/Task-Reaction%20Diagram%20Reasoning-purple)
![Framework](https://img.shields.io/badge/Framework-LLM%20%2B%20MLLM-red)

BioRxnReasoner is a multi-agent framework for biochemical reaction diagram understanding, enabling structured parsing and multi-step reasoning over reaction elements, relations, and conditions.

---

# 🔍 Overview

Biochemical reaction diagrams encode molecular entities, transformation pathways, and experimental conditions within tightly coupled visual–symbolic structures.  
Understanding such diagrams requires models to perform structured reasoning beyond local visual perception.

BioRxnReasoner addresses this challenge through a **multi-stage, multi-agent architecture** that separates structured grounding, multimodal perception, and global reasoning validation.


<p align="center">
  <img src="https://github.com/user-attachments/assets/a0466352-09cf-414c-a658-275f3c844dd0" width="800">
</p>

<p align="center">
  <em>Overview of the BioRxnReasoner framework.</em>
</p>


---

# 🏗️ Architecture

The framework integrates symbolic reasoning from LLMs with multimodal perception.

- **Reaction2Struct**  
  Converts biochemical reaction diagrams into structured reaction schemas.

- **Decomposer Agent**  
  Decomposes complex questions into smaller reasoning units.

- **Visual Comprehender Agent**  
  Performs multimodal perception and localized reasoning.

- **Verifier Agent**  
  Validates reasoning consistency and chemical plausibility.

This design improves the stability and reliability of reasoning over biochemical reaction diagrams.

---

# 📊 ReactionQA Benchmark

We introduce **ReactionQA**, a benchmark for biochemical reaction diagram question answering.

The benchmark evaluates models across five reasoning categories:

1. Reaction Element Identification  
2. Reaction Entity Alignment  
3. Role Identification  
4. Relationship Reasoning  
5. Consistency Verification  

These categories represent increasing levels of reasoning complexity, from perception-level recognition to multi-step reasoning and validation.




<p align="center">
  <img src="https://github.com/user-attachments/assets/e3e6ce5d-20a9-4f8d-8226-eca7d5815c62" width="800">
</p>

<p align="center">
  <em> Five-Level Data Taxonomy by Reasoning Complexity </em>
</p>


The dataset is publicly available on Hugging Face:

https://huggingface.co/datasets/ryan-aiforge/reactionqa

---

# 🙏 Acknowledgements

The **Reaction2Struct** module in this project is adapted from the open-source project **OpenChemIE**.

OpenChemIE provides a toolkit for chemical information extraction from scientific literature, including molecular structure recognition and reaction information extraction.

We thank the authors of OpenChemIE for making their code publicly available.

Repository:  
https://github.com/CrystalEye42/OpenChemIE

Portions of the code are used under the **MIT License**.
