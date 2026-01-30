from haruka_parser.v2.manager import ContextManager
from lxml.html import Element
from haruka_parser.v2.utils.lxml import remove_node, replace_node_with_element, node_to_text, node_to_text_fast
from haruka_parser.line_processing import have_chinese_characters, restore_replacements
from tabulate import tabulate
from haruka_parser.v2.doms.base_dom import BaseDom

class TableDom(BaseDom):
    def __init__(self):
        pass

    def _get_code_text(self, node: Element):
        code_text = str(node.text_content())
        code_text = "\n".join([line.rstrip() for line in code_text.split("\n") if line.strip()])
        # Remove common leading whitespace from all lines
        lines = code_text.split("\n")
        if lines:
            # Find minimum leading whitespace (excluding empty lines)
            min_indent = float('inf')
            for line in lines:
                if line:  # Skip empty lines
                    # Count leading whitespace (spaces and tabs)
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # Remove common leading whitespace from all lines
            if min_indent != float('inf') and min_indent > 0:
                code_text = "\n".join(line[min_indent:] if line else line for line in lines)
        return code_text

    def _process(self, node: Element, manager: ContextManager):
        # 查找所有不包含嵌套表格的表格
        # tables = node.xpath(".//table[not(.//table)]")
        
        # for table in tables:
        #     # 首先恢复表格以正确处理缩进
        #     if hasattr(table, 'html'):
        #         node.html = restore_replacements(node.html, manager.replacement_manager, manager.config, manager.info)
        
        # 查找不包含表格和标题的表格
        # tables = node.xpath(".//table[not(.//table or .//h1 or .//h2 or .//h3 or .//h4 or .//h5 or .//h6)]")

        if (node.tag != "table") or node.xpath("(.//table | .//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6)[1]"):
            return

        have_code = False
        for subnode in node.xpath(".//*[@data-line-number or @data-line-num or @data-code-line-number or @data-code-line-num or @data-linenumber or @data-linenum or @data-code-linenumber or @data-code-linenum]"):
            # print(subnode)
            have_code = True
            subnode.text = ""
        
        if node.xpath(".//code"):
            have_code = True

        # gitlab commit 类型的表格
        if have_code:
            code_text = self._get_code_text(node)
            manager.code_block += 1
            manager.code_length += len(code_text)
            manager.code_line += code_text.count("\n") + 1
            if manager.enable_code:
                code_text = f"```diff\n{code_text}\n```"
            new_element = replace_node_with_element(code_text, node, manager, "pre")
            manager.add_dom_meta(new_element, "code", {
                "text": code_text,
                "languages": "diff"
            }, old_node=node)
            return

        table_data = []
        headers = []
        
        # 查找所有表头
        ths = node.xpath(".//th")
        for th in ths:
            th_text = node_to_text(th)
            headers.append(th_text if th_text else "")
        
        trs = node.xpath(".//tr")
        for tr in trs:
            row_data = []
            tds = tr.xpath(".//td")
            for td in tds:
                # 移除任何脚本
                scripts = td.xpath(".//script")
                for script in scripts:
                    script.getparent().remove(script)
                
                # 获取每个td元素的文本
                td_text = node_to_text(td)
                row_data.append(td_text if td_text else "")
                
                col_span = td.get("colspan")
                if col_span:
                    try:
                        col_span = int(col_span)
                        if col_span > 100:
                            continue
                    except ValueError:
                        continue
                    # 为colspan添加空单元格
                    for _ in range(col_span - 1):
                        row_data.append("")
            
            if row_data:
                table_data.append(row_data)
        
        if len(table_data) == 0 or len(table_data[0]) == 0:
            return
        
        # 后处理
        # 确保所有行都有相同数量的列
        max_cols = max([len(row) for row in table_data])
        for row in table_data:
            if len(row) < max_cols:
                row.extend([""] * (max_cols - len(row)))
        
        # 去除所有单元格的空白
        for i in range(len(table_data)):
            for j in range(len(table_data[i])):
                table_data[i][j] = table_data[i][j].rstrip()
        
        # 如果任何列或行始终为空，则移除它们
        # 移除空列
        empty_columns = []
        for i in range(len(table_data[0])):
            if all([len(row[i]) == 0 for row in table_data]):
                empty_columns.append(i)
        
        for i in reversed(empty_columns):
            for row in table_data:
                del row[i]
        
        # 移除空行
        table_data = [row for row in table_data if len(row) > 0]
        
        # for i in range(len(table_data)):
        #     for j in range(len(table_data[i])):
        #         if table_data[i][j].lower() == "true":
        #             table_data[i][j] = 1
        #         elif table_data[i][j].lower() == "false":
        #             table_data[i][j] = 0
                # 从表格中移除任何换行符
                # table_data[i][j] = table_data[i][j].replace("\n", " ")

        # 检查表格至少有2行2列，否则丢弃
        if len(table_data) > 0 and len(table_data[0]) > 0:
            # 用markdown替换表格
            parent = node.getparent()
            if parent is not None:
                if len(headers) == 0:
                    headers = "firstrow"

                if len(headers) != len(table_data[0]) and len(headers) == len(table_data):
                    table_data = [[h, row[0] if isinstance(row, (list, tuple)) else row] for h, row in zip(headers, table_data)]
                    headers = "firstrow"

                rendered_table = tabulate(
                    table_data,
                    tablefmt=manager.table_format,
                    headers=headers,
                    disable_numparse=True
                )

                # 如果表格超长，回退到 plain 格式
                if len(table_data) == 1 or len(table_data[0]) == 1 or any(len(line) > 100 for line in rendered_table.split("\n")):
                    rendered_table = tabulate(
                        table_data,
                        tablefmt="plain",
                        headers=headers,
                        disable_numparse=True
                    )

                manager.table_block += 1
                new_element = replace_node_with_element(rendered_table, node, manager, "pre")
                manager.add_dom_meta(new_element, "table", {
                    "headers": headers,
                    "data": table_data,
                    "text": rendered_table,
                    "row_count": len(table_data),
                    "col_count": len(table_data[0]),
                }, old_node=node)

        else:
            # 移除空表格
            remove_node(node, manager)