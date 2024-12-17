import os
import json
import openai
import logging
import re  # 新增导入正则表达式模块
from openai import OpenAI
# 设置日志记录
logging.basicConfig(
    filename='question_generation.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

client = OpenAI(
    api_key='',
    base_url=''
)
# 定义输入和输出目录
input_dir=''
output_dir = ''

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 读取提示模板
prompt_template_path = 'prompt_agent_questions.txt'  # 请确保该文件存在并包含适当的提示
try:
    with open(prompt_template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
except FileNotFoundError:
    logging.error(f"提示模板文件 {prompt_template_path} 未找到。请确保文件存在。")
    raise

def generate_questions(agent_json, agent_name, aspects, num_questions_per_aspect):
    """
    从简历中生成问题集。

    :param agent_json: 角色的简历JSON数据
    :param agent_name: 角色姓名
    :param aspects: 需要关注的方面列表，每个方面是一个字典，包含 'topic'、'description' 和 'topic_id'
    :param num_questions_per_aspect: 每个方面需要生成的问题数量
    :return: 问题列表，包含字典形式的每个问题及其相关信息
    """
    # 将整个JSON内容作为上下文
    agent_summary = json.dumps(agent_json, ensure_ascii=False, indent=4)

    # 构建提示内容
    prompt = prompt_template.replace("{agent_summary}", agent_summary).replace("{agent_name}", agent_name)
    prompt = prompt.replace("{aspects}", '\n'.join([f"{aspect['topic_id']}. {aspect['topic']}: {aspect['description']}" for aspect in aspects]))
    prompt = prompt.replace("{num_questions_per_aspect}", str(num_questions_per_aspect))

    try:
        # 调用OpenAI API生成问题
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "你是一个专家，擅长根据提供的简历信息生成相关问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048  # 根据需要调整
        )

        # 获取生成的文本
        generated_text = response.choices[0].message.content
        print(f"Generated questions for {agent_name}:\n{generated_text}\n{'-'*50}")  # 打印生成的文本以便调试
        logging.info(f"Generated questions for {agent_name}:\n{generated_text}\n{'-'*50}")

        # 解析生成的问题
        questions = []
        # 使用正则表达式匹配类似 '1.1. 问题内容' 的行
        pattern = re.compile(r'^(\d+)\.\d+\.\s*(.*)')

        for line in generated_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                topic_id = int(match.group(1))
                question_part = match.group(2)
                # 根据 topic_id 从 aspects 中获取 topic 名称
                topic = next((aspect['topic'] for aspect in aspects if aspect['topic_id'] == topic_id), "未知")
                questions.append({
                    "question": question_part,
                    "topic": topic,
                    "topic_id": topic_id
                })

        return questions

    except Exception as e:
        error_message = f"Error generating questions for {agent_name}: {e}"
        print(error_message)
        logging.error(error_message)
        return []

def create_agent_context(agent_data):
    """
    创建角色的上下文信息。

    :param agent_data: 角色的简历JSON数据
    :return: 上下文数据
    """
    return agent_data

# 定义需要关注的方面，每个方面包含 topic, description 和 topic_id
aspects_to_extract = [
    {
        "topic_id": 1,
        "topic": "个人历史与背景",
        "description": "询问模型有关简历里的事实性问题，看模型能否回答正确，保证知识的一致性，可以重点从朝代，官职，地点等方面提问，可以提问类似“你的家乡是哪里，对你产生了什么影响”，"
    },
    {
        "topic_id": 2,
        "topic": "时代背景与社会环境",
        "description": "询问模型关于其生活时期的社会状况、文化习俗和历史事件的问题。探讨其对当时政治、经济和文化环境的看法和适应情况。可以提问类似“你所处的时代是什么样的时代？”"
    },
    {
        "topic_id": 3,
        "topic": "成就与贡献",
        "description": "询问模型关于其主要成就、作品或对历史的贡献的问题。探讨其对自己成就的评价以及对后世可能产生的影响。可以提问类似“你的著述是什么？你认为你的作品对当代产生了什么影响”，而不是提问你的著述xx集对当代产生了什么影响，不要产生知识暴露的问题"
    },
    {
        "topic_id": 4,
        "topic": "人际交往与社会，亲属关系",
        "description": "询问模型关于其与家人、朋友、同僚和敌人的关系的问题。探讨其在社会中的地位、角色以及与其他重要人物的交往。可以提问类似“你的家人有谁，他对你产生了什么影响之类的”，尽量不要提问那种类似把关系信息直接暴露出来的问题"
    },
    {
        "topic_id": 5,
        "topic": "思想，性格与价值观",
        "description": "询问模型关于其个人性格，个人信仰，哲学观点和道德观念的问题，可以主要关注性格和价值观方面。"
    }
]

# 遍历输入目录下的所有JSON文件
for filename in os.listdir(input_dir):
    if filename.endswith('.json'):
        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            agent_summary = json.dumps(agent_data, ensure_ascii=False, indent=4)
            agent_name = agent_data.get("基本信息", {}).get("姓名", "未知")
            agent_context = create_agent_context(agent_data)

            print(f"Generating questions for {agent_name}...")
            logging.info(f"Generating questions for {agent_name}...")

            questions = generate_questions(
                agent_context,
                agent_name,
                aspects=aspects_to_extract,
                num_questions_per_aspect=3  # 根据需要调整每个方面生成的问题数量
            )

            # 打印 questions 列表以确认其内容
            print(f"Questions list for {agent_name}: {questions}\n{'-'*50}")
            logging.info(f"Questions list for {agent_name}: {questions}\n{'-'*50}")

            # 准备输出数据
            output_data = {
                "问题集": questions
            }

            # 保存为JSON文件
            output_filename = f"{os.path.splitext(filename)[0]}_questions.json"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump(output_data, out_f, ensure_ascii=False, indent=4)

            print(f"Questions saved to {output_path}")
            logging.info(f"Questions saved to {output_path}")

        except Exception as e:
            error_message = f"Error processing file {filename}: {e}"
            print(error_message)
            logging.error(error_message)

print("所有角色的问题集生成完毕。")
