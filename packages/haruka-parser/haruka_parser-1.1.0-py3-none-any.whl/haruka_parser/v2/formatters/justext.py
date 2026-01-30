import re
import ahocorasick
from haruka_parser.justext.core import classify_paragraphs, revise_paragraph_classification_fast
from haruka_parser.justext.utils import get_stoplist

HEADINGS_PATTERN = re.compile(r"\bh\d\b")
MULTIPLE_WHITESPACE_PATTERN = re.compile(r"\s+", re.UNICODE)

def normalize_whitespace(text):
    """将多个空白字符转换为单个空格"""
    return MULTIPLE_WHITESPACE_PATTERN.sub(lambda x: " ", text)


class JustextParagraphAdapter:
    """
    适配器类，让 haruka_parser 的 Paragraph 可以被 justext 分类算法使用。
    包装 haruka_parser.Paragraph，提供 justext.Paragraph 所需的接口。
    """
    def __init__(self, haruka_paragraph):
        self.haruka_paragraph = haruka_paragraph
        self.dom_path = haruka_paragraph.dom_path
        self.xpath = haruka_paragraph.xpath
        
        # justext 需要的属性
        self.chars_count_in_links = 0
        self.tags_count = 0
        self.text_nodes = []
        
        # 从 haruka_paragraph 计算属性
        for item in haruka_paragraph.items:
            self.text_nodes.append(item.text)
            if item.tag == 'a':
                self.chars_count_in_links += len(item.text)
            self.tags_count += 1
        
        # 分类结果 (会被 justext 算法设置)
        self.cf_class = ""      # context-free 分类: short/neargood/good/bad
        self.class_type = ""    # 最终分类: short/neargood/good/bad
        self.heading = False    # 是否是标题 (会被 classify_paragraphs 设置)
    
    @property
    def is_heading(self):
        """检查是否为标题元素 (h1-h6)"""
        return bool(HEADINGS_PATTERN.search(self.dom_path))
    
    @property
    def text(self):
        """获取规范化后的文本"""
        text = "".join(self.text_nodes)
        return normalize_whitespace(text.strip())
    
    def __len__(self):
        """返回文本长度"""
        return len(self.text)
    
    @property
    def words_count(self):
        """返回单词数量"""
        return len(self.text.split())
    
    def stopwords_count(self, stopwords):
        """计算停用词数量"""
        return sum(word.lower() in stopwords for word in self.text.split())
    
    def stopwords_density(self, stopwords):
        """计算停用词密度"""
        if self.words_count == 0:
            return 0
        return self.stopwords_count(stopwords) / self.words_count
    
    def links_density(self):
        """计算链接密度"""
        text_length = len(self.text)
        if text_length == 0:
            return 0
        return self.chars_count_in_links / text_length

class JustextParagraphCJKAdapter(JustextParagraphAdapter):
    def __init__(self, haruka_paragraph, stoplist):
        self.stoplist = stoplist
        self.automaton = ahocorasick.Automaton()
        for stopword in stoplist:
            self.automaton.add_word(stopword, stopword)
        self.automaton.make_automaton()
        super().__init__(haruka_paragraph)
    
    @property
    def words_count(self):
        """返回单词数量"""
        return len(self.text)
    
    def stopwords_count(self, stopwords):
        """
        使用pyahocorasick高效统计停用词数量
        """
        cnt = 0
        for end_index, found_word in self.automaton.iter(self.text):
            cnt += 1
        return cnt


def tag_justext_paragraphs(paragraphs, language="English"):
    stoplist = get_stoplist(language)    

    if language in ["Chinese"]:
        justext_paragraphs = [JustextParagraphCJKAdapter(p, stoplist) for p in paragraphs]
        classify_paragraphs(justext_paragraphs, stoplist, 30, 100, 0.05, 0.15, 0.25, True)
        revise_paragraph_classification_fast(justext_paragraphs, 150)
    else:
        justext_paragraphs = [JustextParagraphAdapter(p) for p in paragraphs]
        classify_paragraphs(justext_paragraphs, stoplist, 50, 150, 0.1, 0.2, 0.25, True)
        revise_paragraph_classification_fast(justext_paragraphs, 150)

    res = []
    for p in justext_paragraphs:
        p.haruka_paragraph.priority.append(f"justext_{p.cf_class}")
        res.append(p.haruka_paragraph)
    return res
