# -*- coding: utf-8 -*-
"""
Single-agent version: uses only MLLM for image question answering.
Input: image file path + question text.
Output: MLLM answer.
"""

import os
import base64
import requests
import json
import time


def gpt4o_image_qa(image_path: str, question: str):

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")


    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    api_key = os.getenv("ONECHATS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("Please set the environment variable ONECHATS_API_KEY or OPENAI_API_KEY")

    if os.getenv("ONECHATS_API_KEY"):
        url = "https://chatapi.onechats.ai/v1/chat/completions"
    else:
        url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-4o",
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "You are a vision-language assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
            ]}
        ]
    }

    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[gpt4o attempt {attempt+1}] error: {e}")
            time.sleep(5)
    return "Error: Failed to get response from GPT-4o after retries."


if __name__ == "__main__":
    img_path = "xxx"
    question = "What is the first reactant_smiles in the figure?"

    print(f"Running GPT-4o on image: {img_path}")
    print(f"Question: {question}\n")

    answer = gpt4o_image_qa(img_path, question)
    print("Answer:\n", answer)


