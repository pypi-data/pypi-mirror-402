import re
import xml.etree.ElementTree as ET

def svg_clear(svg_code: str) -> str:
    """
    清理大模型生成的代码。正常的SVG从<svg开始，到</svg>结束。
    本函数会过滤掉<svg>标签之前和</svg>标签之后的所有内容。

    参数:
        svg_code: 原始字符串输入，其中可能包含SVG代码以及其他文本。

    返回:
        清理后的SVG代码字符串；如果未找到SVG代码，则返回空字符串。
    """
    # 定义正则表达式以查找SVG内容。
    # - <svg.*?</svg>: 匹配从一个<svg>标签开始到</svg>标签结束的所有内容。
    # - '?' 使'.*'变为非贪婪匹配，这样它会在找到第一个'</svg>'时就停止。
    # - re.DOTALL: 允许'.'匹配换行符，因为SVG代码可能跨越多行。
    # - re.IGNORECASE: 使匹配不区分大小写，可以匹配<svg>、<SVG>等。
    match = re.search(r"<svg.*?</svg>", svg_code, re.DOTALL | re.IGNORECASE)

    # 如果找到匹配项，则返回匹配到的完整SVG代码。
    if match:
        return match.group(0)

    # 否则，返回一个空字符串。
    return ""


def xml_drawio_clear(xml_code: str) -> str:
    """
    清理大模型生成的代码。正常的draw.io XML文件从<?xml version="1.0" encoding="UTF-8"?>
    <mxfile host="app.diagrams.net"...>开始，到</mxfile>结束。
    本函数会过滤掉<?xml ...>标签之前和</mxfile>标签之后的所有内容。

    参数:
        xml_code: 原始字符串输入，其中可能包含XML代码以及其他文本。

    返回:
        清理后的XML代码字符串；如果未找到XML代码，则返回空字符串。
    """
    # 定义正则表达式以查找完整的 draw.io XML 内容。
    # - <\?xml.*?\?>: 匹配 XML 声明 <?xml ... ?>。问号需要转义。
    # - \s*: 匹配 XML 声明和 mxfile 标签之间的任何空白字符（如换行符）。
    # - <mxfile.*?</mxfile>: 匹配从 <mxfile ...> 开始到 </mxfile> 结束的所有内容。
    # - re.DOTALL: 标志位，允许 '.' 匹配包括换行符在内的任何字符。
    pattern = r'<\?xml version="1.0" encoding="UTF-8"\?>\s*<mxfile.*?</mxfile>'

    # 针对prompt模板的过滤
    # if xml_code.startswith("```xml"):
    #     xml_code = xml_code[6:]
    #     logger.info("移除了```xml标记")
    # if xml_code.startswith("```"):
    #     xml_code = xml_code[3:]
    #     logger.info("移除了```标记")
    # if xml_code.endswith("```"):
    #     xml_code = xml_code[:-3]
    #     logger.info("移除了结尾```标记")

    # 正则过滤XML代码
    match = re.search(pattern, xml_code, re.DOTALL)

    过滤换行符
    xml_code = re.sub(r"<br\s*/?>", "", xml_code)

    xml_code = xml_code.strip()
    # 如果找到匹配项，则返回匹配到的完整XML代码。
    if match:
        return match.group(0)

    # 否则，返回一个空字符串。
    return ""

def json_clear(json_code: str) -> str:
    """
    清理大模型生成的JSON代码。正常的json从{或[开始，到}或]结束。
    本函数会过滤掉JSON对象或数组之外的所有内容。

    参数:
        json_code: 原始字符串输入，其中可能包含JSON代码以及其他文本。

    返回:
        清理后的有效JSON字符串；如果未找到，则返回空字符串。
    """
    cleaned_code = json_code.strip()

    # 寻找第一个 '{' 或 '['
    first_brace = cleaned_code.find('{')
    first_bracket = cleaned_code.find('[')

    start_pos = -1
    end_char = ''

    # 确定起始位置和对应的结束字符
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        start_pos = first_brace
        end_char = '}'
    elif first_bracket != -1:
        start_pos = first_bracket
        end_char = ']'
    else:
        # 如果没有找到起始符号，则返回空字符串
        return ""

    # 寻找与起始符号相匹配的最后一个结束符号
    end_pos = cleaned_code.rfind(end_char)

    # 如果没有找到结束符号，或者结束符号在开始符号之前，则无效
    if end_pos == -1 or end_pos < start_pos:
        return ""

    # 提取可能的JSON字符串
    potential_json = cleaned_code[start_pos : end_pos + 1]

    return potential_json

def html_clear(html_code: str) -> str:
    """
    清理开始的  “```html”，结尾的“```"
    """
    if html_code.startswith("```html"):
        html_code = html_code[7:]
    if html_code.endswith("```"):
        html_code = html_code[:-3]
    html_code = html_code.strip()
    return html_code

def xml_checker(xml_code: str) -> tuple[bool, str]:
    """
    检查drawio的元素数量是否足够，是否包含mxcell组件，是否存在信息异常
    """
    try:
        ET.fromstring(xml_code)
    except ET.ParseError as e:
        return False, f"❌ 错误：生成的XML格式无效: {e}，请重新生成"
    
    # 格式正确后，再检查内容是否过于简单
    if "<mxCell id=" not in xml_code or xml_code.count("<mxCell") < 5:
        return False, "❌ 错误：AI生成的XML内容过于简单，包含的组件少于5个，推断为不满足业务要求，请重新生成"

    return True, "✅ XML有效且内容符合基本要求"
    