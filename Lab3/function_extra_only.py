import os
import re
import jieba
import time
from collections import defaultdict

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
    words = jieba.lcut(text)
    words = [word for word in words if re.match(r'^[\u4e00-\u9fa5]{2,}$', word)]
    return words

# 构建倒排索引
def build_inverted_index(files):
    inverted_index = defaultdict(set)
    for doc_id, text in files.items():
        words = preprocess_text(text)
        for word in words:
            inverted_index[word].add(doc_id)
    return inverted_index

# 布尔检索
def boolean_search(query, inverted_index):
    query = query.lower()
    if ' and ' in query:
        terms = query.split(' and ')
        return set.intersection(*[inverted_index.get(term.strip(), set()) for term in terms])
    elif ' or ' in query:
        terms = query.split(' or ')
        return set.union(*[inverted_index.get(term.strip(), set()) for term in terms])
    elif ' not ' in query:
        term, exclude = query.split(' not ')
        return inverted_index.get(term.strip(), set()) - inverted_index.get(exclude.strip(), set())
    else:
        return inverted_index.get(query.strip(), set())

# 短语检索 
def phrase_search(query, files):
    query_words = preprocess_text(query)
    result = set()
    for doc_id, text in files.items():
        words = preprocess_text(text)
        for i in range(len(words) - len(query_words) + 1):
            if words[i:i + len(query_words)] == query_words:
                result.add(doc_id)
                break
    return result

# 模糊检索（基于编辑距离） 
# 例如中国与中图的编辑距离为1
def fuzzy_search(query, inverted_index, max_distance=1):
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    result = set()
    for word in inverted_index:
        if levenshtein_distance(query, word) <= max_distance:
            result.update(inverted_index[word])
    return result

# 主函数
def main():
    directory = 'article'
    files = read_files(directory)
    inverted_index = build_inverted_index(files)

    while True:
        query = input("请输入检索词（支持布尔检索、短语检索、模糊检索，输入'quit'退出）：")
        if query == 'quit':
            break

        start_time = time.time()
        if '"' in query:  # 短语检索
            query = query.strip('"')
            result = phrase_search(query, files)
        elif '~' in query:  # 模糊检索
            query = query.strip('~')
            result = fuzzy_search(query, inverted_index)
        else:  # 布尔检索
            result = boolean_search(query, inverted_index)

        end_time = time.time()
        print(f"检索结果：{sorted(result)}")
        print(f"检索时间：{end_time - start_time:.10f}秒")

if __name__ == "__main__":
    main()