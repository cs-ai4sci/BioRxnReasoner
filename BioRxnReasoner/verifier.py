import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from openai import OpenAI

# ===== project path =====
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

# ===== prompt import =====
from .verification_prompts import ANSWER_VERIFIER_PROMPT



# ===== logging =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)



def llama3_8b(prompt: str,
              api_key: str = "",
              base_url: str = "",
              model_name: str = "llama3-8B-instruct",
              max_retries: int = 5,
              retry_interval: int = 5) -> Dict[str, Any]:
    client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                temperature=0.0,
                top_p=1.0,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )

            response = completion.choices[0].message.content if completion.choices else ""
            usage = getattr(completion, "usage", None)

            return {
                "success": True,
                "text": response or "",
                "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "raw_response": completion.model_dump() if hasattr(completion, "model_dump") else None,
                "error": None,
            }

        except Exception as e:
            last_error = str(e)
            logger.warning("llama3_8b failed (%d/%d): %s", attempt, max_retries, last_error)
            if attempt < max_retries:
                time.sleep(retry_interval)

    return {
        "success": False,
        "text": "",
        "input_tokens": None,
        "output_tokens": None,
        "raw_response": None,
        "error": last_error,
    }


def gpt4o_http(prompt: str,
               api_key: str = "",
               url: str = "https://chatapi.onechats.ai/v1/chat/completions",
               model_name: str = "gpt-4o",
               timeout: int = 60,
               max_retries: int = 5,
               retry_interval: int = 5) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model_name,
        "temperature": 0.0,
        "top_p": 1.0,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()

            text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            return {
                "success": True,
                "text": text,
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "raw_response": result,
                "error": None,
            }

        except Exception as e:
            last_error = str(e)
            logger.warning("gpt4o_http failed (%d/%d): %s", attempt, max_retries, last_error)
            if attempt < max_retries:
                time.sleep(retry_interval)

    return {
        "success": False,
        "text": "",
        "input_tokens": None,
        "output_tokens": None,
        "raw_response": None,
        "error": last_error,
    }


def gpt4o_openai(prompt: str,
                 api_key: str = "",
                 base_url: str = "",
                 model_name: str = "gpt-4o",
                 max_retries: int = 5,
                 retry_interval: int = 5) -> Dict[str, Any]:
    client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                temperature=0.0,
                top_p=1.0,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )

            response = completion.choices[0].message.content if completion.choices else ""
            usage = getattr(completion, "usage", None)

            return {
                "success": True,
                "text": response or "",
                "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "raw_response": completion.model_dump() if hasattr(completion, "model_dump") else None,
                "error": None,
            }

        except Exception as e:
            last_error = str(e)
            logger.warning("gpt4o_openai failed (%d/%d): %s", attempt, max_retries, last_error)
            if attempt < max_retries:
                time.sleep(retry_interval)

    return {
        "success": False,
        "text": "",
        "input_tokens": None,
        "output_tokens": None,
        "raw_response": None,
        "error": last_error,
    }



def sanitize_filename(text: str, max_length: int = 120) -> str:
    if text is None:
        return "unknown"
    cleaned = "".join(c for c in str(text) if c.isalnum() or c in (" ", "_", "-", ".", "[", "]"))
    cleaned = cleaned.strip().replace(" ", "_")
    return cleaned[:max_length] if cleaned else "unknown"


def build_subqa_text(sub_q_list: List[str], sub_ans_list: List[str]) -> str:
    lines = []
    for i, ans in enumerate(sub_ans_list):
        q = sub_q_list[i] if i < len(sub_q_list) else f"sub_q{i+1}:"
        cleaned_ans = str(ans).replace("\n", " ").strip()
        lines.append(f"{q}\nsub_ans{i+1}:{cleaned_ans}")
    return "\n".join(lines)


def extract_final_question(sub_q_list: List[str], fallback_query: str) -> str:
    if not sub_q_list:
        return fallback_query
    last_q = sub_q_list[-1]
    return last_q.split(":", 1)[-1].strip() if ":" in last_q else last_q.strip()


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    tmp_path.replace(path)


def build_verification_prompt(sub_qa: str, final_q: str, final_res: str) -> str:
    return ANSWER_VERIFIER_PROMPT.format(sub_qa, final_q, final_res)


def call_llm(prompt: str, llm_name: str) -> Dict[str, Any]:
    llm_name = llm_name.lower().strip()

    if llm_name == "gpt-4o":
        return gpt4o_openai(
            prompt=prompt,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", ""),
            model_name="gpt-4o",
        )

    if llm_name == "gpt-4o-http":
        return gpt4o_http(
            prompt=prompt,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            url=os.getenv("OPENAI_HTTP_URL", "https://chatapi.onechats.ai/v1/chat/completions"),
            model_name="gpt-4o",
        )

    if llm_name == "llama3-8b":
        return llama3_8b(
            prompt=prompt,
            api_key=os.getenv("LLAMA_API_KEY", ""),
            base_url=os.getenv("LLAMA_BASE_URL", ""),
            model_name="llama3-8B-instruct",
        )

    raise ValueError(f"Unsupported llm_name: {llm_name}")


# =========================
# Core process
# =========================
def process_item(item: Dict[str, Any], llm_name: str) -> Dict[str, Any]:
    imgname = str(item.get("imgname", ""))
    label = str(item.get("label", ""))
    query = str(item.get("query", ""))
    response = str(item.get("response", "")).replace("\n", " ")

    sub_q_list = item.get("sub_q", [])
    sub_res_list = item.get("sub_res", [])

    if not isinstance(sub_q_list, list):
        sub_q_list = []
    if not isinstance(sub_res_list, list):
        sub_res_list = []

    if len(sub_res_list) == 0:
        return {
            "imgname": imgname,
            "q": query,
            "sub_q": "None",
            "sub_ans": "None",
            "ori_res": response,
            "res": response,
            "label": label,
            "status": "skipped_no_subqa",
        }

    subqs = sub_q_list[:-1] if len(sub_q_list) >= 1 else []
    final_q = extract_final_question(sub_q_list, query)
    sub_qa = build_subqa_text(subqs, sub_res_list)
    final_res = response

    prompt = build_verification_prompt(sub_qa, final_q, final_res)
    llm_result = call_llm(prompt, llm_name)

    save = {
        "imgname": imgname,
        "q": final_q,
        "sub_q": subqs,
        "sub_ans": sub_res_list,
        "ori_res": final_res,
        "res": llm_result["text"] if llm_result["success"] else final_res,
        "label": label,
        "status": "success" if llm_result["success"] else "failed_fallback_to_ori_res",
        "input_tokens": llm_result["input_tokens"],
        "output_tokens": llm_result["output_tokens"],
        "error": llm_result["error"],
        "statistic": llm_result["raw_response"],
    }
    return save


def run(read_path: str, write_path: str, llm_name: str) -> None:
    read_path = Path(read_path)
    write_path = Path(write_path)
    write_path.mkdir(parents=True, exist_ok=True)

    if not read_path.exists():
        raise FileNotFoundError(f"Input file not found: {read_path}")

    with open(read_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of items.")

    logger.info("Start processing %d items with model=%s", len(data), llm_name)

    for idx, item in enumerate(data, start=1):
        try:
            imgname = str(item.get("imgname", f"item_{idx}"))
            label = str(item.get("label", "unknown"))

            tmp_imgid = Path(imgname).name if imgname else f"item_{idx}"
            cleaned_label = sanitize_filename(label)
            output_file = Path(write_path) / f"[{tmp_imgid}]_{cleaned_label}.json"

            if output_file.exists():
                logger.info("Skip existing file: %s", output_file.name)
                continue

            result = process_item(item, llm_name)
            atomic_write_json(output_file, result)

            logger.info("Processed %d/%d -> %s", idx, len(data), output_file.name)

        except Exception as e:
            logger.exception("Failed to process item %d: %s", idx, str(e))


if __name__ == "__main__":
    MLLMs = "gpt-4o"
    LLMs1 = "gpt-4o"
    LLMs2 = "gpt-4o"   # 可选: "gpt-4o", "gpt-4o-http", "llama3-8b"

    read_path = r"xxx"
    write_path = f"./res/3refine/{LLMs1}_{MLLMs}_{LLMs2}/human_val"

    run(read_path, write_path, LLMs2)