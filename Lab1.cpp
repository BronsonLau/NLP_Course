// Lab1:正向最大匹配分词的c++实现

#include <iostream>
#include <windows.h>
#include <fstream>
#include <string>
#include <unordered_set>
#include <unordered_map>
#include <map>
#include <vector>
#include <sstream>
#include <algorithm>
#include <iomanip>  // 控制输出格式
#include <regex>    // 用于去除标点符号
#include <locale>
#include <codecvt>


using namespace std;

// Trie 结构体
struct TrieNode {
    unordered_map<char, TrieNode*> children;
    bool isEndOfWord = false;
};

// Trie 类
class Trie {
private:
    TrieNode* root;

public:
    Trie() { root = new TrieNode(); }

    // 插入单词到 Trie
    void insert(const string& word) {
        TrieNode* node = root;
        for (char ch : word) {
            if (!node->children.count(ch)) {
                node->children[ch] = new TrieNode();
            }
            node = node->children[ch];
        }
        node->isEndOfWord = true;
    }

    // 在文本中从 start 位置查找最长匹配词
    string findLongestMatch(const string& text, int start) {
        TrieNode* node = root;
        string longestMatch;
        
        for (int i = start; i < text.size(); i++) {
            char ch = text[i];
            
            if (!node->children.count(ch)) {
                return longestMatch; 
            }
            node = node->children[ch];
            if (node->isEndOfWord) {
                longestMatch = text.substr(start, i - start + 1); // 更新最长匹配
            }
        }
        return longestMatch;
    }
};


// 判断字符串是否是中文标点组合
bool isAllChinesePunctuation(const string& word) {
    static const string chinesePunctuation = "，。！？、；：“”‘’—…【】《》（）〈〉";
    
    for (char ch : word) {
        if (chinesePunctuation.find(ch) == string::npos) {
            return false; 
        }
    }
    return true;
}


// 读取字典文件并构建 Trie
Trie LoadDictionary(const string& DictFile) { // debug:排除标点版
    Trie trie;
    ifstream file(DictFile);
    string line;
    while (getline(file, line)) {
        if (!isAllChinesePunctuation(line) && !line.empty()) {  // 只插入非标点组合的单词
            trie.insert(line);
        }
    }
    file.close();
    return trie;
}

// 读取停用词文件
unordered_set<string> LoadStopWords(const string& StopWordsFile) {
    unordered_set<string> stopwords;
    ifstream file(StopWordsFile);
    string line;
    while (getline(file, line)) {
        stopwords.insert(line);
    }
    file.close();
    return stopwords;
}

bool isChineseChar(const string& str) {
    wstring_convert<codecvt_utf8<wchar_t>> converter;
    wstring wstr = converter.from_bytes(str);

    if (wstr.empty()) return false;
    wchar_t ch = wstr[0];

    return (ch >= 0x4E00 && ch <= 0x9FFF); // 仅判断第一个字符是否是汉字
}


// 在 Trie 架构下进行最大匹配分词
vector<string> segmentText(const string& text, Trie& trie) {
    vector<string> segments;
    int i = 0;

    while (i < text.size()) {
        string longestMatch = trie.findLongestMatch(text, i);

        if (!longestMatch.empty()) {
            segments.push_back(longestMatch);
            i += longestMatch.length(); // 跳过匹配的词
        } else {
            // 处理 UTF-8 汉字（1-4 字节）
            unsigned char lead = text[i];
            int charLen = 1; // 默认 1 字节

            if (lead >= 0xC0 && lead <= 0xDF) charLen = 2; // 双字节字符
            else if (lead >= 0xE0 && lead <= 0xEF) charLen = 3; // 三字节字符（常见汉字）
            else if (lead >= 0xF0 && lead <= 0xF7) charLen = 4; // 四字节字符（扩展区）

            string singleChar = text.substr(i, charLen);

            if (isChineseChar(singleChar)) { 
                segments.push_back(singleChar); // 只存入合法的中文字符
            }
            i += charLen; // 跳过完整字符
        }
    }
    return segments;
}



// 去除标点符号（检查）
string removePunctuation(const string& word) {
    static regex punctRegex(R"(^[[:punct:]]+|[[:punct:]]+$)");
    return regex_replace(word, punctRegex, ""); 
}

// 计算词频（去除停用词 & 标点符号），同时计算新词总数
pair<map<string, int>, int> calculateFrequency(const vector<string>& segments, const unordered_set<string>& stopwords) {
    map<string, int> frequency;
    int validWordCount = 0;
    for (string word : segments) {
        word = removePunctuation(word); // 去除前后标点符号

        // 剔除乱码：必须是 1~3 个合法的汉字，且不在停用词表中
        if (stopwords.find(word) == stopwords.end()) {
            frequency[word]++;
            validWordCount++;
        }
    }

    return {frequency, validWordCount};
}

// 输出 Top10 词频，并显示词频百分比（六位小数）
void printTop10(const map<string, int>& frequency, int totalWords) {
    vector<pair<string, int>> freqVec(frequency.begin(), frequency.end());
    sort(freqVec.begin(), freqVec.end(), [](const pair<string, int>& a, const pair<string, int>& b) {
        return a.second > b.second;
    });

    cout << left << setw(10) << "词语" << setw(10) << "次数" << setw(15) << "频率(%)" << endl;
    cout << "-----------------------------------" << endl;

    for (int i = 0;i < freqVec.size() && i < 10 ; i++) {
        string word = freqVec[i].first;
        int count = freqVec[i].second;
        double percentage = (count * 100.000) / totalWords;

        cout << left << setw(10) << word 
             << setw(10) << count 
             << fixed << setprecision(6) << percentage << "%" << endl;
    }
}

// 主函数
int main() {
    SetConsoleOutputCP(65001);

    string textFile = "corpus.sentence.txt";
    string dictFile = "corpus.dict.txt";
    string stopwordsFile = "cn_stopwords.txt";

    // 读取文本
    ifstream textFileStream(textFile);
    stringstream buffer;
    buffer << textFileStream.rdbuf();
    string text = buffer.str();
    textFileStream.close();

    // 读取字典（用 Trie）
    Trie trie = LoadDictionary(dictFile);

    // 读取停用词
    unordered_set<string> stopwords = LoadStopWords(stopwordsFile);

    // 分词
    vector<string> segments = segmentText(text, trie);

    // 计算词频（去除停用词 & 标点符号），并获取新词总数
    auto [frequency, totalWords] = calculateFrequency(segments, stopwords);

    // 输出 Top10 词频
    printTop10(frequency, totalWords);
    printf("总词数：%d\n", totalWords);
    return 0;
}
