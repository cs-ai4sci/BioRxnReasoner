# ReactionQA Dataset

## Overview

ReactionQA is a benchmark dataset for **biochemical reaction diagram question answering**.  
The dataset is designed to evaluate multimodal reasoning capabilities over biochemical reaction diagrams, requiring models to understand reaction components, semantic relations, and logical consistency across complex reaction schemes.

ReactionQA accompanies the **BioRxnReasoner** framework and provides structured question–answer annotations for biochemical reaction diagrams.

The dataset is publicly available on Hugging Face:

https://huggingface.co/datasets/ryan-aiforge/reactionqa

---

## Dataset Structure
data 

├── reaction_diagram_qa.json 

├── images

└── Dataset Traceability and Provenance Table.csv



### Files

**reaction_diagram_qa.json**

Contains question–answer annotations associated with biochemical reaction diagrams.  
Each record typically contains:

- `image` — path to the reaction diagram image
- `question` — natural language question about the diagram
- `answer` — ground truth answer
- `category` — reasoning category

**images/**

Directory containing biochemical reaction diagram images used for the questions.

**Dataset Traceability and Provenance Table.csv**

Metadata describing the origin, traceability, and provenance information of the reaction diagrams collected for the dataset.

---

## Task Definition

The dataset supports the task of **biochemical reaction diagram question answering**.

Given a reaction diagram **I** and a natural language question **Q**, the goal is to predict the answer **A**:


The questions cover multiple reasoning levels including:

- Reaction Element Identification  
- Reaction Entity Alignment  
- Role Identification  
- Relationship Reasoning  
- Consistency Verification  

These categories reflect increasing levels of reasoning complexity required for biochemical diagram understanding.

---

## Lisences
This dataset is released under the Apache 2.0 License.

---
## Usage

Example for loading the dataset locally:

```python
import json

with open("reaction_diagram_qa.json", "r") as f:
    data = json.load(f)

print(data[0])

```




