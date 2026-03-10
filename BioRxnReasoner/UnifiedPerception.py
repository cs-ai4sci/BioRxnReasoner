import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
import base64
import json
import os
import time
import requests
import PIL
from PIL import Image
from io import BytesIO
import BioRxnReasoner.table_qa_prompt as table_qa_prompt  # prompts for perception stage


def getColTable(tablefrom, table_str, delimiter=' | '):

    rows = [row.strip() for row in str(table_str).replace('<0x0A>', '\n').split('\n') if row]
    if not rows:
        return json.dumps({"columns": [], "data": []}, ensure_ascii=False)

    if 'PlotQA' in str(tablefrom):

        if len(rows) < 2:
            return json.dumps({"columns": [], "data": []}, ensure_ascii=False)
        title = rows[0].split(delimiter)[1] if delimiter in rows[0] and len(rows[0].split(delimiter)) > 1 else rows[0]
        columns = rows[1].split(delimiter)
        data = []
        for row in rows[2:]:
            vals = row.split(delimiter)
            data.append({col: vals[i] if i < len(vals) else "" for i, col in enumerate(columns)})
        return json.dumps({"title": title, "columns": columns, "data": data}, ensure_ascii=False)
    else:
        columns = rows[0].split(delimiter)
        data = []
        for row in rows[1:]:
            vals = row.split(delimiter)
            data.append({col: vals[i] if i < len(vals) else "" for i, col in enumerate(columns)})
        return json.dumps({"columns": columns, "data": data}, ensure_ascii=False)

def resolve_image_path(img_root_path: str, img_id: str):

    if not img_id:
        raise FileNotFoundError("Empty img_id.")

    pid = str(img_id).strip().rstrip('/')
    # 绝对路径直接命中
    if os.path.isabs(pid) and os.path.isfile(pid):
        return os.path.normpath(pid)

    fname = os.path.basename(pid)
    base = os.path.join(img_root_path, fname)
    if os.path.isfile(base):
        return os.path.normpath(base)

    name, ext = os.path.splitext(base)
    if not ext:
        for e in ('.png', '.jpg', '.jpeg', '.webp'):
            cand = name + e
            if os.path.isfile(cand):
                return os.path.normpath(cand)

    base2 = os.path.normpath(base)
    if os.path.isfile(base2):
        return base2

    raise FileNotFoundError(f"Image not found. Tried: {base} (and common extensions) under {img_root_path}")

# ========== 数据整合 ==========
def getinput(table_path, tablefrom, root_path):

    dict_table = {}

    # --- ① 处理表格文件（table_path） ---
    try:
        with open(table_path, 'r', encoding='utf-8') as f1:
            tables = json.load(f1)

        if isinstance(tables, dict):
            tables = [tables]

        for i, item in enumerate(tables):
            if not isinstance(item, dict):
                continue


            key = None
            if item.get('imgname'):
                key = os.path.basename(str(item['imgname']).strip().rstrip('/'))
            elif item.get('reactant_pics'):
                key = os.path.basename(str(item['reactant_pics']).strip().rstrip('/'))
            else:
                key = f"reaction_{i}.png"

            if item.get('table'):
                dict_table[key] = str(item['table'])
            else:
                reactant = item.get('reactant_smiles', '-')
                product = item.get('product_smiles', '-')
                condition = item.get('condition', '-')
                table_str = "reactant_smiles | product_smiles | condition\n" \
                            f"{reactant} | {product} | {condition}"
                dict_table[key] = table_str

    except Exception as e:
        print(f"[Warning] Failed to load/parse table file '{table_path}': {e}")
        dict_table = {"default.png": "reactant_smiles | product_smiles | condition\n- | - | -"}

 
    aa = []
    try:
        with open(root_path, 'r', encoding='utf-8') as f2:
            data = json.load(f2)


        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                pass

        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            fixed = []
            for x in data:
                try:
                    fixed.append(json.loads(x))
                except Exception:
                    print(f"[Warning] Skipped malformed string item in subQsfile: {x[:120]}...")
            data = fixed

        if isinstance(data, dict):
            data = [data]

        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                print(f"[Warning] Skipped malformed item (not dict): {item}")
                continue

            tmp_imgname = item.get('imgname', None)
            if tmp_imgname:
                tmp_imgname = os.path.basename(str(tmp_imgname).strip().rstrip('/'))

            tmp_question = item.get('question', 'Unknown question')
            tmp_label = item.get('label', '')

            subq_raw = item.get('subq', '')
            if isinstance(subq_raw, str):
                subq_clean = subq_raw.replace('\n\n', '\n').split('\n') if subq_raw else []
            elif isinstance(subq_raw, list):
                subq_clean = subq_raw
            else:
                subq_clean = []


            tmp_table = dict_table.get(tmp_imgname) if tmp_imgname else None
            if tmp_table is None:
                tmp_table = next(iter(dict_table.values())) if dict_table else \
                    "reactant_smiles | product_smiles | condition\n- | - | -"
                if tmp_imgname is None:
                    tmp_imgname = next(iter(dict_table.keys())) if dict_table else "default.png"

            aa.append({
                'imgid': tmp_imgname,
                'question': tmp_question,
                'subq': subq_clean,
                'label': tmp_label,
                'table': tmp_table
            })

    except Exception as e:
        print(f"[Error] Failed to load/parse sub-question file '{root_path}': {e}")
        aa = []

    return aa


def gpt4o(inputs):

    import os
    image = os.path.normpath(str(inputs['image']).strip().rstrip('/'))
    text = inputs['text']

    if not os.path.isfile(image):
        return f"wrong!! image file not found: {image}"

    with open(image, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode("utf-8")


    api_key = os.getenv("ONECHATS_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        return "wrong!! missing API key (set ONECHATS_API_KEY or OPENAI_API_KEY)."


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
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
    }

    for attempt in range(5):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[gpt4o] attempt {attempt+1} failed: {e}")
            time.sleep(5)

    return "wrong!! failed to get response from GPT-4o after retries."

# ========== 路由器 ==========
def multimodal_conversation_call(tokenizer, model, image_processor, model_name, inputs, MLLMs_type):
    if MLLMs_type == "geminiV":
        return "geminiV not enabled in this build."
    elif MLLMs_type == "qwenVPlus":
        return "qwenVPlus not enabled in this build."
    elif MLLMs_type == "llava":
        return "llava not enabled in this build."
    elif MLLMs_type == "gpt4o":
        return gpt4o(inputs)
    else:
        return "unknown MLLM"


def run(table_path, tablefrom, subQsfile, res_split, img_root_path, LLMs_type, MLLMs_type):
    inputs = getinput(table_path, tablefrom, subQsfile)


    out_dir = os.path.join(res_split, f"2perceptual_{LLMs_type}subQ_{MLLMs_type}")
    os.makedirs(out_dir, exist_ok=True)

    for item in inputs:
        tmp_imgname = os.path.basename(str(item['imgid']).strip().rstrip('/'))
        try:
            img_path = resolve_image_path(img_root_path, tmp_imgname)
        except Exception as e:
            print(f"[Error] resolve_image_path failed for '{tmp_imgname}': {e}")
            continue

        tmp_table = item['table']
        tmp_question = item['question']
        tmp_subq = item['subq']
        tmp_label = item['label']


        cleaned_question = "".join(c for c in tmp_question if c.isalnum() or c in (' ', '_', '-')).strip()
        cleaned_question = cleaned_question.replace(os.sep, '_')
        save_name = f"[{tmp_imgname}]_{cleaned_question}.json"
        filename = os.path.join(out_dir, save_name)

        usingT = table_qa_prompt  # prompts for perception stage


        subqID = 0
        if len(tmp_subq) > 1:

            first = tmp_subq[subqID]
            first_q = first.split(':', 1)[1] if ':' in first else first
            txt_input = usingT.template.format(tmp_table, first_q)
        else:
            # txt_input = usingT.final_0sub.format(tmp_table, tmp_question)
            txt_input = usingT.final_0sub.format(table=tmp_table, q=tmp_question)

        test_input = {"image": img_path, "text": txt_input}

        if not os.path.exists(filename):
            sub_response = []
            if len(tmp_subq) > 1:
                history_subQApairs = ""
                response = None
                for subq_id in range(len(tmp_subq) - 1):
                    if subq_id == 0:
                        response = multimodal_conversation_call(None, None, None, "", test_input, MLLMs_type)
                    else:
                        subqID += 1
                        cur = tmp_subq[subqID]
                        cur_q = cur.split(':', 1)[1] if ':' in cur else cur
                        txt_input = usingT.template.format(tmp_table, cur_q)
                        test_input = {"image": img_path, "text": txt_input}
                        response = multimodal_conversation_call(None, None, None, "", test_input, MLLMs_type)

                    sub_response.append(response)
                    history_subQApairs += f"\nsub_q{subqID + 1}:{tmp_subq[subqID].split(':', 1)[1] if ':' in tmp_subq[subqID] else tmp_subq[subqID]}" \
                                          f"\nsub_ans{subqID + 1}:{response}\n"

                final_txt_input = usingT.final_nsub.format(tmp_table, history_subQApairs, tmp_question)
                final_input = {"image": img_path, "text": final_txt_input}
                response_final = multimodal_conversation_call(None, None, None, "", final_input, MLLMs_type)
            else:
                response_final = multimodal_conversation_call(None, None, None, "", test_input, MLLMs_type)
                sub_response = []

            tmp_save = {
                "imgname": img_path,
                "table": tmp_table,
                "query": tmp_question,
                "sub_q": tmp_subq,
                "sub_res": sub_response,
                "response": response_final,
                "label": tmp_label
            }
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(tmp_save, json_file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    tablefrom = 'PlotQA'  # ChartQA, PlotQA
    img_root_path = r'/xxx'
    table_path = r'/xxx'
    subQsfile = r'/xxx'  # decomposer generates
    res_split = r"/xxx"
    MLLMs_type = "gpt4o"  # geminiV qwenVPlus llava gpt4o
    LLMs_type = "gpt4o"   # which decomposer generates the subquestions

    run(table_path=table_path, tablefrom=tablefrom, subQsfile=subQsfile,
        res_split=res_split, img_root_path=img_root_path,
        LLMs_type=LLMs_type, MLLMs_type=MLLMs_type)
