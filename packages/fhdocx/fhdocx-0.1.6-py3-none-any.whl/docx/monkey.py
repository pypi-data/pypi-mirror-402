from typing import IO, Union
import docx.oxml
from docx.document import Document as _Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.package import OpcPackage
from docx.opc.packuri import PackURI
from docx.oxml.ns import nsdecls
from docx.oxml.parser import parse_xml
from docx.oxml.shape import CT_GraphicalObjectData, CT_Inline
from docx.oxml.xmlchemy import BaseOxmlElement, ZeroOrOne
from docx.parts.document import DocumentPart
from docx.text.run import Run
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
from docx.opc.pkgwriter import PackageWriter
from pptx.parts.chart import ChartPart as PptChart


# 扩展Document类以添加图表至文档
def add_chart_document(self, chart_type, x, y, cx, cy, chart_data):
    """
    在文档中添加一个新的图表。
    :param chart_type: 图表类型，来自pptx.enum.chart.XL_CHART_TYPE
    :param x: 图表左上角X坐标
    :param y: 图表左上角Y坐标
    :param cx: 图表宽度
    :param cy: 图表高度
    :param chart_data: 图表数据，ChartData实例
    :return: 创建的图表对象
    """
    run = self.add_paragraph().add_run()
    return run.add_chart(chart_type, x, y, cx, cy, chart_data)


# 添加方法到Document类
_Document.add_chart = add_chart_document


# 修改OpcPackage类以支持新的part命名规则
def next_partname(self, tmpl):
    """
    修改part名称生成逻辑，适应从PPT到DOCX的转换。
    """
    tmpl = tmpl.replace("/ppt", "/word")  # 更改路径以适应Word文档结构
    partnames = [part.partname for part in self.iter_parts()]
    for n in range(1, len(partnames) + 2):  # 生成唯一的新part名称
        candidate_partname = tmpl % n
        if candidate_partname not in partnames:
            return PackURI(candidate_partname)
    raise Exception("ProgrammingError: ran out of candidate_partnames")


OpcPackage.next_partname = next_partname

# 扩展CT_GraphicalObjectData类以包含图表元素
CT_GraphicalObjectData.cChart = ZeroOrOne("c:chart")


# CT_Inline类增加静态方法用于创建新的图表内联对象
def new_chart(cls, shape_id, rId, x, y, cx, cy):
    """
    创建一个新的图表内联对象。
    """
    inline = parse_xml(cls._chart_xml())  # 解析内联XML模板
    inline.extent.cx = cx  # 设置宽度
    inline.extent.cy = cy  # 设置高度
    chart = CT_Chart.new(rId)  # 创建图表元素
    inline.graphic.graphicData._insert_cChart(chart)  # 将图表元素插入图形数据
    return inline


CT_Inline.new_chart_inline = classmethod(new_chart)


# 提供_chart_xml的静态方法用于生成图表内联XML模板
def _chart_xml(cls):
    """
    返回图表内联元素的XML字符串模板。
    """
    return (
            "<wp:inline %s>\n"
            "  <wp:extent cx='0' cy='0'/>\n"
            '  <wp:effectExtent l="0" t="0" r="0" b="0"/>\n'
            '  <wp:docPr id="1" name="Chart 1"/>\n'
            "  <wp:cNvGraphicFramePr/>\n"
            "  <a:graphic %s>\n"
            '    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/>\n'
            "  </a:graphic>\n"
            "</wp:inline>" % (nsdecls("wp", "a"), nsdecls("a"))
    )


CT_Inline._chart_xml = classmethod(_chart_xml)


# 定义CT_Chart类以处理图表元素
class CT_Chart(BaseOxmlElement):
    @classmethod
    def new(cls, rId):
        """
        创建一个新的图表元素，关联给定的关系ID。
        """
        chart = parse_xml(cls._chart_xml(rId))  # 解析图表XML模板
        chart.id = rId  # 设置关系ID
        return chart

    @classmethod
    def _chart_xml(cls, rId):
        """
        返回图表元素的XML字符串模板。
        """
        return '<c:chart %s r:id="%s"/>\n' % (nsdecls("c", "r"), rId)


docx.oxml.register_element_cls("c:chart", CT_Chart)  # 注册CT_Chart类到oxml解析器


# 扩展DocumentPart类以获取或添加图表
def get_or_add_chart(self, chart_type, x, y, cx, cy, chart_data):
    """
    获取已存在的图表Part，或创建并添加新图表Part。
    """
    chart_part = PptChart.new(chart_type, chart_data, self.package)  # 创建图表Part
    rId = self.relate_to(chart_part, RT.CHART)  # 建立与图表Part的关系
    return rId, chart_part.chart  # 返回关系ID和图表对象


DocumentPart.get_or_add_chart = get_or_add_chart


# 添加新方法以创建新的图表内联对象
def new_chart_inline(self, chart_type, x, y, cx, cy, chart_data):
    """
    创建新的图表内联对象，并关联图表Part。
    """
    rId, chart = self.get_or_add_chart(chart_type, x, y, cx, cy, chart_data)
    shape_id = self.next_id  # 获取下一个形状ID
    return CT_Inline.new_chart_inline(shape_id, rId, x, y, cx, cy), chart


DocumentPart.new_chart_inline = new_chart_inline


# 扩展Run类以直接在运行对象中添加图表
def add_chart(self, chart_type, x, y, cx, cy, chart_data):
    """
    在当前运行对象中添加图表。
    """
    inline, chart = self.part.new_chart_inline(chart_type, x, y, cx, cy, chart_data)
    self._r.add_drawing(inline)  # 将图表内联对象添加到当前运行的绘图元素中
    return chart


Run.add_chart = add_chart


# 修改OpcPackage的保存方法以处理可能的before_marshal异常
def save(self, pkg_file: Union[str, IO[bytes]]):
    """
    保存OPC包到指定的文件路径或二进制流。
    """
    for part in self.parts:
        try:
            part.before_marshal()  # 尝试调用各Part的预处理方法
        except AttributeError:  # 如果Part没有此方法则忽略异常
            pass
    PackageWriter.write(pkg_file, self.rels, self.parts)  # 执行实际的保存操作


OpcPackage.save = save
