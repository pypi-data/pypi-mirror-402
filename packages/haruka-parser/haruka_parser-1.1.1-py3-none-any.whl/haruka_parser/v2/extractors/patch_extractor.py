from haruka_parser.v2.formatters.justext import tag_justext_paragraphs
from haruka_parser.v2.manager import ContextManager
from haruka_parser.v2.doms.turndown_dom import TurndownDom

class TrafJustextMixPatchExtractor():
    def __init__(self):
        self.turndown_dom = TurndownDom()
    
    def extract(self, paragraphs, dom_attrs, language="English"):
        manager, paragraphs = ContextManager.from_paragraphs_dict(paragraphs)
        manager.dom_attrs = dom_attrs

        paragraphs = self.clean_link_list(paragraphs)
        paragraphs = self.set_title(paragraphs)

        # 使用 justext 算法标记 paragraphs
        paragraphs = tag_justext_paragraphs(paragraphs, language)

        self.turndown_dom.smart_paragraphs_priority(paragraphs, manager)

        func_0 = lambda x: ("traf" in x and "read" in x) or "is_title" in x
        func_1 = lambda x: "traf" in x or "is_title" in x
        output_text_0 = self.turndown_dom.process_paragraphs(paragraphs, manager, func_0)
        output_text_1 = self.turndown_dom.process_paragraphs(paragraphs, manager, func_1)
        
        if len(output_text_0) / (len(output_text_1)+1) < 0.5:
            accept_func = func_1
        else:
            accept_func = func_0
        justext_mix_res = self.turndown_dom.process_paragraphs(paragraphs, manager, lambda x: accept_func(x) or "justext_good" in x)
        
        return justext_mix_res
    
    def clean_link_list(self, paragraphs):
        for paragraph in paragraphs:
            if "link_list" in paragraph.priority:
                paragraph.priority.remove("link_list")
            for item in paragraph.items:
                if "link_list" in item.priority:
                    item.priority.remove("link_list")
        return paragraphs

    def set_title(self, paragraphs):
        for paragraph in paragraphs:
            if ("traf" in paragraph.priority or "read" in paragraph.priority) and paragraph.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                paragraph.priority.append("is_title")
        return paragraphs
