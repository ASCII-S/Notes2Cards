import os
import re
import shutil
from config import data_folder, global_prompt_folder_path, processed_folder, des_folder_path, finished_folder, unfinished_folder, output_folder_path, log_folder_path, WORKSPACE_CACHE_FILE
from pathlib import Path
import json
import csv

# 清理非法字符
def clean_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 清理无效字符，保留标题的回车符
def clean_content(content, ignore_title=False):
    cleaned_content = []
    for line in content:
        line = line.rstrip()  # 去掉行尾的空格
        # 如果这一行是空行或仅包含`---`，则跳过
        if line and line != '---':  
            cleaned_content.append(line + '\n')  # 保留回车符
    # 如果清理后的内容只有标题和空行，返回空列表
    if len(cleaned_content) <= 1 and ignore_title:
        return None
    return cleaned_content

def split_md_by_title(md_file_path, output_dir, ignore_title=False):
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        content = md_file.readlines()

    file_content = []
    file_counter = 1  # 文件编号

    for line in content:
        # 跳过以 #include 开头的行
        if line.strip().startswith("#include"):
            continue
        if "https://" in line or "http://" in line:  # 跳过链接
            continue
        if not line.strip():  # 跳过空行
            continue

        # 处理一级标题
        if line.startswith('#') and line.count('#') == 1:
            # 如果当前内容有实际内容且不为空，保存
            if file_content:
                cleaned_content = clean_content(file_content, ignore_title)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"# {line.strip('#').strip()}\n"]  # 保留标题及其换行符

        # 处理二级标题
        elif line.startswith('#') and line.count('#') == 2:
            # 保存之前的内容（如果有的话）
            if file_content:
                cleaned_content = clean_content(file_content, ignore_title)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"## {line.strip('#').strip()}\n"]  # 保留标题及其换行符
        
        # 处理三级标题
        elif line.startswith('#') and line.count('#') == 3:
            # 保存之前的内容（如果有的话）
            if file_content:
                cleaned_content = clean_content(file_content, ignore_title)
                if cleaned_content:  # 如果清理后的内容不为空
                    file_name = f"{file_counter:03d}.md"
                    file_path = os.path.join(output_dir, file_name)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
                    with open(file_path, 'w', encoding='utf-8') as section_file:
                        section_file.writelines(cleaned_content)
                    file_counter += 1
            # 清空当前内容，准备开始新的一段
            file_content = [f"### {line.strip('#').strip()}\n"]  # 保留标题及其换行符
        
        else:
            # 添加当前内容
            file_content.append(line)

    # 最后一部分的内容保存
    if file_content:
        cleaned_content = clean_content(file_content, ignore_title)
        if cleaned_content:  # 如果清理后的内容不为空
            file_name = f"{file_counter:03d}.md"
            file_path = os.path.join(output_dir, file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
            with open(file_path, 'w', encoding='utf-8') as section_file:
                section_file.writelines(cleaned_content)

def get_files_in_order(folder_path):
    # 获取文件夹内的所有文件，并按数字顺序排序
    files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
    # 按文件名的数字顺序排序
    files.sort(key=lambda x: int(x.split('.')[0]))  # 通过文件名前的数字进行排序
    
    # 返回排序后的文件路径
    for file in files:
        yield os.path.join(folder_path, file)

# 在file_utils.py中使用生成器替代列表
def get_files_in_order_fail(folder_path):
    for f in sorted(os.listdir(folder_path), 
                   key=lambda x: int(x.split('.')[0])):
        if f.endswith('.md'):
            yield os.path.join(folder_path, f)

def text_file_to_string(file_path):
    # 打开文件并读取内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def move_to_folder(src, dst):
    """ 移动文件到目标文件夹 """
    os.makedirs(dst, exist_ok=True)
    shutil.move(src, os.path.join(dst, os.path.basename(src)))

def init_folder():
    # 创建文件夹
    folders_to_create = [
        data_folder, global_prompt_folder_path, processed_folder, des_folder_path, finished_folder,
        unfinished_folder, output_folder_path, log_folder_path
    ]
    
    for folder in folders_to_create:
        if not os.path.exists(folder):
            os.makedirs(folder)

def load_workspace_cache():
    """从 `workspace_cache.json` 读取 `workspace_name`、`chatmodel`、`thread_name`"""
    if not Path(WORKSPACE_CACHE_FILE).exists():
        return {"workspaces": []}  # **文件不存在，返回空数据**

    with open(WORKSPACE_CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
    
def get_unique_chatmodels():
    """从 `workspace_cache.json` 获取所有出现过的 `chatmodel` 并去重"""
    data = load_workspace_cache()
    chatmodels = set()

    for ws in data.get("workspaces", []):
        chat_model = ws.get("chatModel")
        if chat_model:
            chatmodels.add(chat_model)

    return sorted(chatmodels)  # **返回排序后的唯一 chatmodel 列表**

def extract_json(data_str):
    print("Raw data to extract JSON from:\n", data_str)

    # 1. 尝试从 ```json 中提取并确保有配对的 `````
    try:
        if "```json" in data_str:
            start_index = data_str.find("```json") + len("```json")
            end_index = data_str.find("```", start_index)
            
            # 如果找到了配对的结尾 ```
            if start_index != -1 and end_index != -1:
                csv_content = data_str[start_index:end_index].strip()
                print("Extracted content from ```json:", csv_content)  # 输出提取的内容
                json_data = json.loads(csv_content)  # 使用 json.loads 代替 ast.literal_eval
                return json_data
            else:
                raise ValueError("没有找到有效的 JSON 结束标记```")
    except Exception as e:
        print(f"Error extracting from ```json block: {e}")

    # 2. 如果没有 ```json，尝试通过括号匹配的方式提取 JSON
    try:
        # 使用正则表达式匹配第一个有效的 JSON 对象
        json_str_match = re.search(r"\{.*\}", data_str, re.DOTALL)
        if json_str_match:
            csv_content = json_str_match.group(0)
            print("Extracted content by matching braces:", csv_content)  # 输出提取的内容
            json_data = json.loads(csv_content)
            return json_data
        else:
            raise ValueError("无法从数据中提取有效的 JSON")
    except Exception as e:
        print(f"Error extracting JSON from braces: {e}")
        return None


def process_json_to_csv(json_data, output_file_path):
    # 1. 查找包含问题和答案数据的字段（我们假设它是一个列表）
    for key, value in json_data.items():
        if isinstance(value, list):  # 假设包含问题和答案的字段是一个列表
            answer_data = value
            break
    else:
        print("没有找到包含问题和答案的列表字段。")
        return
    
    # 2. 写入 CSV 数据，不写入列头
    with open(output_file_path, "a+", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=answer_data[0].keys(), quoting=csv.QUOTE_MINIMAL)
        for entry in answer_data:
            writer.writerow(entry)


if __name__ == '__main__':
    input_md = './C9_docker.md'  # 输入Markdown文件路径
    # 获取input_md的文件名（不包含路径和扩展名）
    file_name = os.path.splitext(os.path.basename(input_md))[0]
    
    # 设置output_dir为文件名
    output_dir = file_name  # 输出文件夹路径为文件名
    print(f"将 {input_md} 按标题分割，保存到 {output_dir} 文件夹中")
    split_md_by_title(input_md, output_dir)
