
# ========== template ==========


template = """
STRICT MODE: This is a TABLE-first QA task. 
Use the TABLE as the single source of truth unless the question explicitly asks about visual attributes 
(e.g., bar color, shape) OR the table cell is missing/NaN/untrusted.

Instructions:
1. If the question requests a specific column value (such as "reactant_smiles", "product_smiles", or "condition"), 
   return the cell string EXACTLY as it appears (preserve case, symbols, and punctuation).
2. Do NOT convert SMILES, IDs, or structured chemical strings into common chemical names.
3. If the table and chart conflict, TRUST THE TABLE.
4. If you must use the chart because the table is missing/untrusted, 
   clearly state "using chart due to missing/untrusted table cell" and then extract the value.
5. Output only JSON, no explanations or multi-step reasoning.

Return format example:
{{"answer":"<exact string>","source":"table" | "chart"}}

Here is the table in JSON format:
{table}

Q: {q}
"""



final_nsub = """
STRICT MODE: Produce the final answer by prioritizing the TABLE. 
Use the chart ONLY if the table cell is missing/NaN/untrusted or if the question explicitly refers to visual attributes.

Rules:
1. If the question asks for a column value (like "reactant_smiles"), return the exact string — no abbreviation or paraphrase.
2. Do NOT provide analysis, steps, or explanations.
3. If you used the chart due to missing/untrusted table cell, set "source":"chart"; otherwise use "source":"table".
4. Never convert SMILES to names.
5. Output must strictly be valid JSON.

Inputs:
- Table (JSON):
{table}
- Sub-QA pairs (may contain noise):
{subqa}

Q: {q}

Output JSON only:
{{"answer":"<exact string>","source":"table" | "chart"}}
"""



final_0sub = """
STRICT MODE (TABLE-first):
- Answer strictly from the table unless the question explicitly refers to visual attributes 
  or the table cell is missing/NaN/untrusted.
- Return the exact cell string if the question asks for a specific column 
  (e.g., "reactant_smiles", "product_smiles", "condition").
- Do NOT invent names or interpret the SMILES chemically.
- Output only JSON — no explanation, no prefixes like "The answer is".

Table (JSON):
{table}

Q: {q}

Output:
{{"answer":"<exact string>","source":"table"}}
"""