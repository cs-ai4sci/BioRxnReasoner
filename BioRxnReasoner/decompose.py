import json 
import os
import time
from openai import OpenAI
import requests
from pathlib import Path
from   decomposition_prompt import prompt
import google.generativeai as genai
def llama3_8b(prompt):
    client = OpenAI(
        api_key="",
        base_url=""
    )
    processed_flag = False
    while not processed_flag:
        try:
            completion = client.chat.completions.create(
                model="llama3-8B-instruct",
                temperature=0.0001,
                top_p=0.0001,
                messages=[
                    {"role": "system", "content": "you are an assistant"},
                    {"role": "user", "content": prompt},
                ],
            )
            input_tokens = completion.usage.prompt_tokens
            output_tokens = completion.usage.completion_tokens
            response = completion.choices[0].message.content
            return  response,input_tokens,output_tokens
        except Exception as e:
            processed_flag = False
            print(e)
            print('Error! Sleep for 5s.')
            time.sleep(5)

def gpt4(prompt):
    api_key = "sk-xxx"
    url = "https://api.openai.com/v1/chat/completions" 
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4-1106-preview",
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "you are an assistant"},
            {"role": "user", "content": prompt}
        ]
    }
    processed_flag = False
    while not processed_flag:
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            result = response.json()
            generated_result = result["choices"][0]["message"]["content"]
            statistic = result
            return generated_result, statistic
        except Exception as e:
            processed_flag = False
            print(result)
            print(e)
            print('Error! Sleep for 5s.')
            time.sleep(5)

def gemini(prompt):
    generation_config = {"temperature": 0.0, "top_p": 0.0, "top_k": None}
    genai.configure(api_key='', transport='rest')
    model = genai.GenerativeModel('models/gemini-pro', generation_config = generation_config)
    processed_flag = False
    ii = 0
    while not processed_flag:
        try:
            response = model.generate_content(prompt)
            input_tokens = model.count_tokens(prompt).total_tokens
            output_tokens = model.count_tokens(response.text).total_tokens
            return response.text, input_tokens, output_tokens
        except Exception as e:
            if ii >= 5:
                res = f'wrong!!, {str(e)}'
                return res, "wrong!!", "wrong!!"
            ii += 1
            processed_flag = False
            print(e)
            print('Error! Sleep for 5s.')
            time.sleep(5)

def process_item(item, write_path, LLMs):
    imgid = item['imgname'].split('/')[-1]
    question = item['question']
    col_table = item['table_head']
    ans = item['label']
    cleaned_question = "".join(c for c in question if c.isalnum() or c in (' ', '_', '-'))
    filename = f"/res/1decomposer_{LLMs}/{write_path}/[{imgid}]_{cleaned_question}.json"
    
    if not os.path.exists(filename):
        res = ''
        inputs = prompt.format(col_table, question)
        if LLMs == "gpt4":
            res, my_statistic = gpt4(inputs)
        elif LLMs == "gemini":
            res, input_tokens, output_tokens = gemini(inputs)
        elif LLMs == "llama3_8b":
            res, input_tokens, output_tokens = llama3_8b(inputs)
        else:
            print("unknown llm")
            return
        # data = {"imgname": imgid, "question": question, "col_table": col_table, "response": res, "label": ans, "input_tokens": input_tokens, "output_tokens": output_tokens}
        save_usage = {"imgname": imgid, "question": question, "col_table": col_table, "response": res, "label": ans, 'statistic': my_statistic}
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(save_usage, json_file, ensure_ascii=False, indent=4)
    else:
        print(f'{filename} \n exit')
_tablehead="""
table_head:{{
   {}
}}
"""
def get_inputs(qa_path, table_path):
    dict_table = {}
    with open(table_path, 'r') as f1:
       tables = json.load(f1)
       for item in tables:
          dict_table[item['imgname'].split('/')[-1]] = item['table']
    aa = []
    try:
        with open(qa_path, 'r', encoding='utf-8') as f2:
            data = json.load(f2)
            for item in data:
                if 'PlotQA' in qa_path:
                    imgname = str(item['image_index']) + '.png'
                    query = item['question_string']
                    label = item['answer']
                    mytable = dict_table[imgname]
                    table_row = [rows.split(' | ') for rows in mytable.split('<0x0A>')]
                    col_head = table_row[1]
                    row_head = []
                    for rows in table_row[1:]:
                        col_1 = rows[0]
                        row_head.append(col_1)
                    title = table_row[0][1]
                    aa.append({'imgname': imgname, 'table_tittle': title, 'table_head': _tablehead.format({"col_head": col_head, "row_head": row_head}), 'question': query, 'label': label})
                else:
                    imgname = item['imgname']
                    query = item['query']
                    label = item['label']
                    mytable = dict_table[imgname]
                    table_row = [rows.split(' | ') for rows in mytable.split(' <0x0A> ')]
                    col_head = table_row[0]
                    row_head = []
                    for rows in table_row:
                        col_1 = rows[0]
                        row_head.append(col_1)
                    aa.append({'imgname': imgname, 'table_head': _tablehead.format({"col_head": col_head, "row_head": row_head}), 'question': query, 'label': label})
                
    except Exception as e:
        print(e)
    return aa

def run(qa_path, table_path, write_path, LLMs):
    all_QApairs = get_inputs(qa_path, table_path)
    for item in all_QApairs:
        process_item(item, write_path, LLMs)

# if __name__ == '__main__':
#     LLMs = "" # gemini, gpt4, llama3_8b

#     write_path = ''
#     qa_path = r''
#     table_path = r''
#     run(qa_path, table_path, write_path, LLMs)

if __name__ == '__main__':
    # gemini / gpt4 / llama3_8b
    LLMs = "gpt4"  


    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    INPUT_DIR = PROJECT_ROOT / "input"


    qa_path = INPUT_DIR / "QA.json"
    table_path = INPUT_DIR / "table.json"


    write_path = 'test_run'

    run(str(qa_path), str(table_path), write_path, LLMs)
