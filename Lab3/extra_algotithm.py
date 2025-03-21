import os
import re
import jieba
import time
from collections import defaultdict
from functools import lru_cache

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

# 构建倒排索引（使用差值编码压缩）
def build_inverted_index(files):
    inverted_index = defaultdict(list)
    for doc_id, text in files.items():
        words = preprocess_text(text)
        word_positions = defaultdict(list)
        for pos, word in enumerate(words):
            word_positions[word].append(pos)
        for word, positions in word_positions.items():
            # 使用差值编码压缩位置列表
            compressed_positions = [positions[0]]
            for i in range(1, len(positions)):
                compressed_positions.append(positions[i] - positions[i - 1])
            inverted_index[word].append((doc_id, compressed_positions))
    return inverted_index

# 布尔检索（使用位图运算优化）
def boolean_search(query, inverted_index):
    query = query.lower()
    if ' and ' in query:
        terms = query.split(' and ')
        sets = [set(doc_id for doc_id, _ in inverted_index.get(term.strip(), [])) for term in terms]
        return set.intersection(*sets) if sets else set()
    elif ' or ' in query:
        terms = query.split(' or ')
        sets = [set(doc_id for doc_id, _ in inverted_index.get(term.strip(), [])) for term in terms]
        return set.union(*sets) if sets else set()
    elif ' not ' in query:
        term, exclude = query.split(' not ')
        term_set = set(doc_id for doc_id, _ in inverted_index.get(term.strip(), []))
        exclude_set = set(doc_id for doc_id, _ in inverted_index.get(exclude.strip(), []))
        return term_set - exclude_set
    else:
        return set(doc_id for doc_id, _ in inverted_index.get(query.strip(), []))

# 短语检索（使用倒排索引优化）
def phrase_search(query, inverted_index):
    query_words = preprocess_text(query)
    if not query_words:
        return set()
    
    # 获取每个词的倒排列表
    postings = []
    for word in query_words:
        postings.append(inverted_index.get(word, []))
    
    # 如果没有完全匹配的词，返回空集
    if not all(postings):
        return set()
    
    # 使用指针法查找短语
    result = set()
    for doc_id, positions in postings[0]:
        for i in range(1, len(postings)):
            if not any(p[0] == doc_id for p in postings[i]):
                break
        else:
            # 检查位置是否连续
            all_positions = [positions]
            for i in range(1, len(postings)):
                all_positions.append([p[1] for p in postings[i] if p[0] == doc_id][0])
            # 解压缩位置列表
            for i in range(len(all_positions)):
                for j in range(1, len(all_positions[i])):
                    all_positions[i][j] += all_positions[i][j - 1]
            # 检查是否连续
            for pos in all_positions[0]:
                match = True
                for i in range(1, len(all_positions)):
                    if pos + i not in all_positions[i]:
                        match = False
                        break
                if match:
                    result.add(doc_id)
                    break
    return result

# 模糊检索（基于编辑距离，使用剪枝优化）
@lru_cache(maxsize=1000)
def fuzzy_search(query, max_distance=1):
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
        if abs(len(word) - len(query)) > max_distance:
            continue  # 剪枝：长度差大于最大距离的直接跳过
        if levenshtein_distance(query, word) <= max_distance:
            result.update(doc_id for doc_id, _ in inverted_index[word])
    return result

# 主函数
def main():
    directory = 'article'
    files = read_files(directory)
    global inverted_index
    inverted_index = build_inverted_index(files)

    while True:
        query = input("请输入检索词（支持布尔检索、短语检索、模糊检索，输入'quit'退出）：")
        if query == 'quit':
            break

        start_time = time.time()
        if '"' in query:  # 短语检索
            query = query.strip('"')
            result = phrase_search(query, inverted_index)
        elif '~' in query:  # 模糊检索
            query = query.strip('~')
            result = fuzzy_search(query)
        else:  # 布尔检索
            result = boolean_search(query, inverted_index)

        end_time = time.time()
        print(f"检索结果：{sorted(result)}")
        print(f"检索时间：{end_time - start_time:.20f}秒")

if __name__ == "__main__":
    main()