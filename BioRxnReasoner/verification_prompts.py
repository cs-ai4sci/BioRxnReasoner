"""
verification_prompts.py

Prompt templates for the Answer Verification stage.

This file defines the verifier prompt used in stage-3 answer verification
for biochemical reaction diagram question answering.
"""


ANSWER_VERIFIER_PROMPT = """
You are a verifier for biochemical reaction diagram question answering.

Your task is to review the intermediate reasoning trace and produce a final verified answer.
You must evaluate the sub-question-answer pairs and determine whether the original answer
is logically consistent and sufficiently supported.

Verification requirements:

1. Check cross-step logical consistency among the sub-answers.
   - Ensure entity identities are used consistently.
   - Ensure entity roles are not contradictory across steps.
   - Ensure reaction directions or transformation relations are not contradictory.
   - Ensure reaction conditions are assigned consistently if they are mentioned.

2. Check whether the final conclusion is supported by the sub-question–answer pairs.
   - Use only information explicitly supported by the provided sub-answers.
   - Do not introduce new facts, entities, or chemical claims that are not grounded.
   - If the sub-answers are incomplete or contradictory, do not over-correct.

3. Correct the original answer only when there is sufficient evidence.
   - If the original answer is already correct, keep it unchanged.
   - If the original answer is incorrect but can be corrected from the verified evidence, output the corrected answer.
   - If the evidence is incomplete, ambiguous, or contradictory, keep the original answer.

4. For numerical questions:
   - Use only explicitly supported values.
   - Normalize units before comparison or calculation if needed.
   - Return the final computed result only, not the raw formula, unless the question explicitly asks for the formula.

5. For yes/no questions:
   - Answer only "Yes" or "No".

6. Keep the final answer as short as possible.
   - Do not include explanation inside the final answer phrase.
   - Do not add extra chemical background.

Output format:

Explanation: <brief verification reasoning based only on the sub-question answers>
Therefore, the answer is: <final short answer>

Now verify the answer.

sub_qa pairs:
{}

Q:
{}

ori_answer:
{}
""".strip()


def build_verification_prompt(sub_qa: str, question: str, ori_answer: str) -> str:
    """
    Build the final verification prompt.

    Args:
        sub_qa: Formatted sub-question–answer pairs as a string.
        question: Final question.
        ori_answer: Original predicted answer before verification.

    Returns:
        A formatted prompt string.
    """
    sub_qa = "" if sub_qa is None else str(sub_qa).strip()
    question = "" if question is None else str(question).strip()
    ori_answer = "" if ori_answer is None else str(ori_answer).strip()

    return ANSWER_VERIFIER_PROMPT.format(sub_qa, question, ori_answer)


if __name__ == "__main__":
    # Minimal runnable example for quick testing
    example_sub_qa = """
sub_q1: Which molecule acts as the catalyst in the reaction diagram?
sub_ans1: SdnF serves as the catalyst.

sub_q2: What is the substrate in the reaction?
sub_ans2: The substrate is O=CC1CCC2...

sub_q3: Does the original answer correctly identify the catalyst?
sub_ans3: Yes, the original answer is consistent with the identified catalyst.
""".strip()

    example_question = "Which molecule acts as the catalyst in the reaction diagram?"
    example_ori_answer = "SdnF"

    prompt = build_verification_prompt(
        sub_qa=example_sub_qa,
        question=example_question,
        ori_answer=example_ori_answer,
    )

    print(prompt)