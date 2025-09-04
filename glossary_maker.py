import csv
import json
import os
import re
import time
from pathlib import Path
from typing import List

import ollama
import ujson
from tqdm import tqdm



def tsv_reader(path: str,start:int = 0) -> List[dict[str, str]]:
    path_object = Path(path)
    if not path_object.exists():
        print("请先生成TSV")
        exit(-1)

    result = []
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        tsv_reader = csv.DictReader(f, delimiter='\t')
        for row in tsv_reader:
            # if count >= 1000:
            #     return result
            if count < start:
                count += 1
                continue
            result.append(row)
            count += 1

    return result


def extract_json_from_response(response_text: str):
    """
    从响应文本中提取JSON字符串
    """
    # 尝试直接解析整个响应
    try:
        json.loads(response_text)
        return response_text
    except json.JSONDecodeError:
        pass

    if response_text.startswith("``json"):
        json_str = response_text[6:-3]
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass

    if response_text.startswith("```json"):
        json_str = response_text[7:-3]
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass

    # 尝试使用正则表达式提取JSON部分
    json_match = re.search(r'\{.*\}|\[.*\]', response_text, re.DOTALL)
    if json_match:
        try:
            json_str = json_match.group()
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass

    # 如果没有找到有效的JSON，返回原始响应
    return response_text


if __name__ == '__main__':
    tsv = tsv_reader("./output/mod_tsv.tsv",start=0)

    # base_url = "https://api.ppinfra.com/openai"
    # api_key = "sk_EF0-iDBzfIEuP141Xl1lXT2f6plm9n1Z1STH81KT-JM"
    # model = "baidu/ernie-4.5-0.3b"

    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['ALL_PROXY'] = ''
    os.environ['no_proxy'] = "localhost,127.0.0.1"



    client = ollama.Client(host='http://127.0.0.1:25566/')
    result: dict[str, set[str]] = {}
    errors: dict[str, str] = {}

    # client = OpenAI(
    #     base_url=base_url,
    #     api_key=api_key,
    # )

    stream = False
    response_format = {"type": "json"}

    # 优化后的提示词，强调需要先进行分词
    prompt = "You are a professional translator specializing in Minecraft mod localization. I will provide you with English and Chinese text pairs from a Minecraft mod. Before performing word alignment, please first tokenize both the English and Chinese texts. For English, split into words and phrases as appropriate. For Chinese, segment the text into meaningful terms. Then perform word alignment between the tokenized English and Chinese texts. For each English word or phrase, find its corresponding Chinese translation. Return only a JSON object where each key-value pair represents an English term and its matched Chinese translation. Format: {\"english_term\": \"chinese_term\", ...}. Only return the JSON object, no additional text, no markdown, no explanations."

    try:
        for item in tqdm(tsv):
            eng_text = item['英文']
            # en_tokens = nltk.word_tokenize(eng_text)  # 英文分词可使用NLTK
            ch_text = item['中文']
            # ch_tokens = list(jieba.cut(ch_text))      # 中文分词可使用jieba
            try:
                response = client.generate(
                    model='qwen3:8b',
                    prompt=f"{prompt} {eng_text}\t{ch_text}",
                    stream=False,
                    format='json',
                    # options={
                    #     "num_ctx": 1024
                    # }
                )
            except Exception as e:
                tqdm.write(str(e))
                continue
            # print(f"{prompt} {eng_text}\t{ch_text}")
            # chat_completion_res = client.chat.completions.create(
            #     model=model,
            #     messages=[
            #
            #         {
            #             "role": "user",
            #             "content": f"{prompt} {eng_text}\t{ch_text}",
            #         }
            #     ],
            #     stream=stream,
            #     extra_body={
            #     }
            # )
            #
            # print(chat_completion_res.choices[0].message.content)

            try:
                json_result: dict[str, str] = ujson.loads(response.response)
                for english in json_result.keys():
                    if english not in result.keys():
                        result[english] = set()
                        result[english].add(json_result[english])
                    else:
                        result[english].add(json_result[english])
            except Exception:
                errors[eng_text] = ch_text
                tqdm.write(response.response)
                pass

            #tqdm.write(str(result))
    except Exception as e:
        serializable_result = {k: list(v) for k, v in result.items()}
        with open("./output/glossary.json", "w", encoding="utf-8") as f:
            ujson.dump(serializable_result, f, ensure_ascii=False, indent=4)

        with open("./output/failed_lines.json", "w", encoding="utf-8") as f:
            ujson.dump(errors, f, ensure_ascii=False, indent=4)

        print(e)
        exit(-1)

    serializable_result = {k: list(v) for k, v in result.items()}

    with open("./output/glossary.json", "w", encoding="utf-8") as f:
        ujson.dump(result, f, ensure_ascii=False, indent=4)

    with open("./output/failed_lines.json", "w", encoding="utf-8") as f:
        ujson.dump(errors, f, ensure_ascii=False, indent=4)