# fhdocx

本项目在`python-docx`基础上，做了一些调整，具体如下：

- 增加word文档的图表功能
- 重新打包为 fhdocx

以下为 python-docx 库的概述

*python-docx* is a Python library for reading, creating, and updating Microsoft Word 2007+ (.docx) files.

## Installation

```
pip install python-docx
```

## Example

```python
>>> from docx import Document

>>> document = Document()
>>> document.add_paragraph("It was a dark and stormy night.")
<docx.text.paragraph.Paragraph object at 0x10f19e760>
>>> document.save("dark-and-stormy.docx")

>>> document = Document("dark-and-stormy.docx")
>>> document.paragraphs[0].text
'It was a dark and stormy night.'
```

More information is available in the [python-docx documentation](https://python-docx.readthedocs.org/en/latest/)
