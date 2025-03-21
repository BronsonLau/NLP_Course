import os
import re
import jieba
import time

# 读取文件
def read_files(directory):
    files = {}
    for i in range(1, 21):
        filename = f"{i}.txt"
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            files[i] = file.read()
    return files

# 分词、去除标点、数字、单字
def preprocess_text(text):
    # 使用jieba进行分词
    words = jieba.lcut(text)
    # 去除标点、数字和单字
    words = [word for word in words if re.match(r'^[\u4e00-\u9fa5]{2,}$', word)]
    return words

# 构建倒排索引
def build_inverted_index(files):
    inverted_index = {}
    for doc_id, text in files.items():
        words = preprocess_text(text)
        for word in words:
            if word not in inverted_index:
                inverted_index[word] = set()
            inverted_index[word].add(doc_id)
    return inverted_index

# 检索功能
def search(query, inverted_index):
    start_time = time.time()
    query_words = preprocess_text(query)
    result = set()
    for word in query_words:
        if word in inverted_index:
            result.update(inverted_index[word])
    end_time = time.time()
    return sorted(result), end_time - start_time

# 主函数
def main():
    directory = 'article'
    files = read_files(directory)
    inverted_index = build_inverted_index(files)
    
    while True:
        query = input("请输入检索词（输入'quit'退出）：")
        if query == 'quit':
            break
        result, search_time = search(query, inverted_index)
        print(f"检索结果：{result}")
        print(f"检索时间：{search_time:.10f}秒")

if __name__ == "__main__":
    main()