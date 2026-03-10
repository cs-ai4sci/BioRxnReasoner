prompt = '''Based on the table_head, break down the following question according to its grammatical structure.
Note that:
1. If the question does not require any computations, simply insert the original question into sub_q1;
2. If the subquestion involves images/cropped regions (e.g., *_pics, *_label_pics, or condition_pics), a question for represent/OCR should be inserted at that sub_q;
3. If there is no entity linked to table_head, the decomposition is directly based on the literal meaning of the question.

Here are some examples.

table_head:{{
    "reactant_pics": "./output/example/reactant.png",
    "reactant_smiles": "CCO",
    "reactant_labels": "['ethanol']",
    "reactant_label_pics": "./output/example/react_label.png",
    "product_pics": "./output/example/product.png",
    "product_smiles": "CC=O",
    "product_labels": "['acetaldehyde']",
    "product_label_pics": "./output/example/prod_label.png",
    "condition": "oxidation",
    "condition_pics": "./output/example/condition.png"
}}

Q: What is the product SMILES?
entities link to table_head:
product SMILES -> product_smiles
sub_questions:
sub_q1: What is the value of product_smiles?

Q: Which compound is labeled ‘indolactam V (1)’?
entities link to table_head:
indolactam V (1) -> one of [reactant_labels, product_labels]
sub_questions:
sub_q1: Does reactant_labels contain "indolactam V (1)"?
sub_q2: Does product_labels contain "indolactam V (1)"?
sub_q3: If sub_q1 is yes, answer "reactant"; if sub_q2 is yes, answer "product".

Q: What does the condition image say?
entities link to table_head:
condition_pics -> key["condition_pics"]
sub_questions:
sub_q1: What text is shown in condition_pics? (OCR)
sub_q2: Return the recognized condition string.

Q: Is the reactant label in the image consistent with the text label?
entities link to table_head:
reactant_label_pics -> key["reactant_label_pics"]
reactant_labels -> key["reactant_labels"]
sub_questions:
sub_q1: What text is shown in reactant_label_pics? (OCR)
sub_q2: What is the text value of reactant_labels?
sub_q3: Are sub_q1 and sub_q2 the same after normalization?

Q: Does the SMILES contain an indole ring?
entities link to table_head:
reactant_smiles, product_smiles (unspecified target)
sub_questions:
sub_q1: Which SMILES does the question refer to: reactant or product?
sub_q2: Does reactant_smiles contain an indole substructure?
sub_q3: Does product_smiles contain an indole substructure?
sub_q4: Report results for each entity.

-----------------------------
Now perform the task:
table_head:
{}
Q: {}
'''
