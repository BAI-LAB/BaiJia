import os
import json
import openai
import pandas as pd
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import multiprocessing
from openai import OpenAI

# 设置日志记录
logging.basicConfig(
    filename='qa_scoring.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)


client = OpenAI(
    api_key='sk-VJNRYlFE142b1c4191fAT3BLbKFJ7c244329f6824E10A214',
    base_url='https://cn2us02.opapi.win/v1'
)

# 定义输入和输出目录
QA_BASE_DIR ='/home/kjz/CBDB/dataset/QA_jsons_nn'
RESUME_DIR = '/home/kjz/CBDB/dataset/test_without_duihua'
PROMPT_FILE = '../prompt_score.txt'  # 请确保此文件包含最新的评分提示
OUTPUT_SCORE_DIR = '/home/kjz/CBDB/dataset/score'

# 确保输出目录存在
os.makedirs(OUTPUT_SCORE_DIR, exist_ok=True)

# 读取提示模板
try:
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
except FileNotFoundError:
    logging.error(f"提示文件 {PROMPT_FILE} 未找到。请确保该文件存在于脚本目录中。")
    print(f"提示文件 {PROMPT_FILE} 未找到。请确保该文件存在于脚本目录中。")
    exit(1)


def generate_prompt(character_id, resume, question, answer):
    prompt = prompt_template.format(
        character_id=character_id,
        resume=resume,
        question=question,
        answer=answer
    )
    return prompt


def score_qa(character_id, resume, question, answer, max_retries=5):
    prompt = generate_prompt(character_id, resume, question, answer)
    backoff_time = 1  # 初始重试间隔时间
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # 请确保此模型可用，或替换为实际可用的模型名称
                messages=[
                    {"role": "system", "content": "你是一个专业的评分助手，负责根据给定的标准对回答进行评分。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # 设置为 0 以获得更确定的回答
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_message = f"Attempt {attempt + 1} failed for QA: {character_id}. Error: {e}"
            print(error_message)
            logging.error(error_message)

            # 指数退避
            if attempt < max_retries - 1:
                time.sleep(backoff_time)
                backoff_time *= 2  # 指数增长
            else:
                logging.error(f"Max retries reached for QA: {character_id}.")
                return None


def parse_scores(response_text):
    scores = {}
    try:
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                parts = line.split(':')
                if len(parts) >= 2:
                    key = parts[0].strip()
                    score_str = parts[1].strip()
                    # 处理可能存在的分数字符后缀
                    score = ''.join(filter(str.isdigit, score_str))
                    if score.isdigit():
                        scores[key] = int(score)
        return scores
    except Exception as e:
        logging.error(f"Error parsing scores: {e}")
        return None


def process_folder(folder_name, folder_path, resume_data_cache):
    results = []
    qa_files = [f for f in os.listdir(folder_path) if f.endswith('_QA.json')]

    if not qa_files:
        print(f"{folder_name} 中未找到 QA 文件")
        logging.info(f"{folder_name} 中未找到 QA 文件")
        return

    for qa_file in tqdm(qa_files, desc=f"Processing {folder_name} QA files"):
        qa_path = os.path.join(folder_path, qa_file)
        try:
            with open(qa_path, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
        except Exception as e:
            logging.error(f"读取 QA 文件 {qa_file} 时出错: {e}")
            continue

        base_name = qa_file.replace('_QA.json', '')
        character_id = base_name
        resume_file = f"{base_name}.json"

        # 使用缓存的简历数据，避免重复读取文件
        resume_data = resume_data_cache.get(resume_file)
        if resume_data is None:
            resume_path = os.path.join(RESUME_DIR, resume_file)
            if not os.path.exists(resume_path):
                logging.error(f"未找到 {qa_file} 对应的简历文件: {resume_file}")
                continue
            try:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                resume_data_cache[resume_file] = resume_data  # 缓存简历数据
            except Exception as e:
                logging.error(f"读取简历文件 {resume_file} 时出错: {e}")
                continue

        resume = json.dumps(resume_data, ensure_ascii=False, indent=4)
        question_set = qa_data.get('问题集', [])
        if not question_set:
            logging.warning(f"文件 {qa_file} 中未找到 '问题集'")
            print(f"文件 {qa_file} 中未找到 '问题集'")
            continue

        for idx, qa_pair in enumerate(question_set, start=1):
            question = qa_pair.get('question', '').strip()
            answer = qa_pair.get('answer', '').strip()

            if not question or not answer:
                logging.warning(f"文件 {qa_file} 中的 QA 索引 {idx} 存在空的问题或答案")
                print(f"文件 {qa_file} 中的 QA 索引 {idx} 存在空的问题或答案")
                continue

            # 检查答案是否为指定的异常情况
            if answer == "抱歉，我无法生成答案。":
                logging.info(f"跳过文件 {qa_file} 中的 QA 索引 {idx}，答案为空")
                print(f"跳过文件 {qa_file} 中的 QA 索引 {idx}，答案为空")
                continue

            scoring_response = score_qa(character_id, resume, question, answer)
            if scoring_response is None:
                continue

            scores = parse_scores(scoring_response)
            if scores is None:
                logging.error(f"无法解析文件 {qa_file} 中 QA 索引 {idx} 的评分")
                continue

            result = {
                'Character_ID': character_id,
                'QA_Index': idx,
            }

            for key in scores:
                result[key] = scores[key]

            results.append(result)

    if not results:
        print(f"{folder_name} 中没有可保存的结果")
        logging.info(f"{folder_name} 中没有可保存的结果")
        return

    df = pd.DataFrame(results)
    output_excel = os.path.join(OUTPUT_SCORE_DIR, f"{folder_name}.xlsx")

    try:
        df.to_excel(output_excel, index=False)
        print(f"评分结果已保存到 {output_excel}")
        logging.info(f"评分结果已保存到 {output_excel}")
    except Exception as e:
        logging.error(f"保存到 Excel 时出错: {e}")
        print(f"保存到 Excel 时出错: {e}")


def main():
    model_folders = [f for f in os.listdir(QA_BASE_DIR) if os.path.isdir(os.path.join(QA_BASE_DIR, f))]

    # 动态确定 max_workers，避免过多线程导致资源竞争
    max_workers = multiprocessing.cpu_count() * 2
    logging.info(f"使用的最大线程数: {max_workers}")

    # 预先加载所有简历文件到缓存中，减少重复读取
    resume_files = [f for f in os.listdir(RESUME_DIR) if f.endswith('.json')]
    resume_data_cache = {}
    for resume_file in resume_files:
        resume_path = os.path.join(RESUME_DIR, resume_file)
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)
                resume_data_cache[resume_file] = resume_data
        except Exception as e:
            logging.error(f"预加载简历文件 {resume_file} 时出错: {e}")

    # 使用 ThreadPoolExecutor 进行多线程处理文件夹
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_folder = {
            executor.submit(process_folder, folder, os.path.join(QA_BASE_DIR, folder), resume_data_cache): folder
            for folder in model_folders
        }

        for future in as_completed(future_to_folder):
            folder = future_to_folder[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"处理文件夹 {folder} 时出错: {e}")
                print(f"处理文件夹 {folder} 时出错: {e}")


if __name__ == "__main__":
    main()
