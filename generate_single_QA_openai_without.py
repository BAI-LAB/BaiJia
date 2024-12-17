import os
import json
import logging
import re
import time
import warnings
import openai
from openai import OpenAI

# 忽略特定的未来警告（可选）
warnings.filterwarnings("ignore", category=FutureWarning)

# 设置日志记录
logging.basicConfig(
    filename='single_QA_generation.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# 设置CUDA设备
model_name="TA/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
# 定义输入和输出目录
resume_dir = '/home/kjz/CBDB/dataset/test_with_duihua'
questions_dir = '/home/kjz/CBDB/dataset/single_questions'
output_dir = '/home/kjz/CBDB/dataset/QA_jsons/Llama-3.1-70B_basic'
client = OpenAI(
    api_key='sk-VJNRYlFE142b1c4191fAT3BLbKFJ7c244329f6824E10A214',
    base_url='https://cn2us02.opapi.win/v1'
)
# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 读取提示模板
prompt_template_path = '../prompt_QA.txt'  # 请确保该文件存在并包含适当的提示
try:
    with open(prompt_template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
except FileNotFoundError:
    logging.error(f"提示模板文件 {prompt_template_path} 未找到。请确保文件存在。")
    raise

def generate_local_answer(full_prompt, max_length=2000):
    """
    使用本地模型为给定的提示生成答案。
    """
    try:
        logging.info("开始生成答案...")
        start_time = time.time()
        response = client.chat.completions.create(
            model=model_name,  # 建议使用"gpt-4"，如果不可用则回退到"gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "你是一个能够提供角色扮演服务的语言模型。"},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=max_length  # 根据需要调整
        )
        
        # 获取生成的文本
        generated_text = response.choices[0].message.content
       
        answer = generated_text
        
        end_time = time.time()
        logging.info(f"答案生成完成，耗时: {end_time - start_time:.2f} 秒")
        
        return answer
    except Exception as e:
        logging.error(f"生成答案时出错: {e}")
        return "抱歉，我无法生成答案。"

def add_answers_to_questions_file(resume_json_path, questions_json_path, output_json_path):
    try:
        # 读取简历
        with open(resume_json_path, 'r', encoding='utf-8') as f:
            resume_data = json.load(f)
        
        # 提取 agent_name
        agent_info = resume_data.get("基本信息", {})
        agent_name = agent_info.get("姓名", "未知")
        
        if agent_name == "未知":
            logging.warning(f"简历文件 {resume_json_path} 中未找到 '姓名' 字段。")
        
        # 创建 agent_summary（将简历JSON转换为可读的字符串）
        agent_summary = json.dumps(resume_data, ensure_ascii=False, indent=4)
        
        # 读取问题集
        with open(questions_json_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        questions = questions_data.get("问题集", [])
        if not questions:
            logging.warning(f"文件 {questions_json_path} 中没有找到 '问题集'。")
            return
        
        for idx, item in enumerate(questions):
            question = item.get("question")
            if not question:
                logging.warning(f"问题集中的第 {idx+1} 项没有 'question' 字段。")
                continue
            
            # 检查是否已经有答案，避免重复生成
            if "answer" in item:
                logging.info(f"文件 {questions_json_path} 中的第 {idx+1} 个问题已存在答案，跳过。")
                continue
            
            # 构建完整的提示
            filled_prompt = prompt_template.format(agent_name=agent_name, agent_summary=agent_info)
            full_prompt = f"{filled_prompt}\n\n问题：{question}\n回答："
            print(full_prompt)
            # 生成答案
            print(f"正在为文件 {os.path.basename(questions_json_path)} 的第 {idx+1} 个问题生成答案...")
            logging.info(f"为文件 {questions_json_path} 的问题生成答案: {question}")
            
            answer = generate_local_answer(full_prompt)
            item["answer"] = answer
            
            # 打印生成的答案（可选）
            print(f"问题: {question}\n回答: {answer}\n")
    
            time.sleep(2)  # 根据需要调整
    
        # 保存更新后的数据
        with open(output_json_path, 'w', encoding='utf-8') as out_f:
            json.dump(questions_data, out_f, ensure_ascii=False, indent=4)
        
        print(f"答案已添加并保存到 {output_json_path}")
        logging.info(f"答案已添加并保存到 {output_json_path}")
    
    except Exception as e:
        error_message = f"处理文件 {questions_json_path} 时出错: {e}"
        print(error_message)
        logging.error(error_message)

def process_all_files(resume_directory, questions_directory, output_directory):
    # 使用正则表达式匹配文件名格式，如 丁之翰_117533_questions.json
    pattern = re.compile(r'^(.*)_questions\.json$')
    
    for filename in os.listdir(questions_directory):
        if filename.endswith('_questions.json'):
            match = pattern.match(filename)
            if match:
                base_name = match.group(1)  # e.g., 丁之翰_117533
                questions_file_path = os.path.join(questions_directory, filename)
                resume_file_path = os.path.join(resume_directory, f"{base_name}.json")
                
                if not os.path.exists(resume_file_path):
                    logging.warning(f"对应的简历文件 {resume_file_path} 未找到，跳过文件 {filename}。")
                    continue
                
                output_filename = f"{base_name}_QA.json"
                output_file_path = os.path.join(output_directory, output_filename)
    
                add_answers_to_questions_file(resume_file_path, questions_file_path, output_file_path)
            else:
                logging.warning(f"文件名 {filename} 不符合预期格式，跳过。")
        else:
            logging.info(f"文件 {filename} 不是以 '_questions.json' 结尾，跳过。")
    
    print("所有文件的答案生成完毕。")
    logging.info("所有文件的答案生成完毕。")

if __name__ == "__main__":
    process_all_files(resume_dir, questions_dir, output_dir)
