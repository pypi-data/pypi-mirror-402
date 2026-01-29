from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from htmltodocx.schemas import ConfigSchema, DefaultTableStyleSchema, DefaultConfigSchema
"""
Базовая конфигурация для HTML → DOCX конвертера.

Содержит набор карт соответствий HTML/CSS‑стилей к параметрам python‑docx,
а также значения по умолчанию для абзацев, изображений и таблиц.

Эта конфигурация передаётся в HTMLtoDocx и определяет поведение парсера.

Содержимое
----------

align_map : dict[str, WD_PARAGRAPH_ALIGNMENT]
    Соответствие CSS‑свойства `text-align` значениям выравнивания абзацев
    в Word. Используется для тегов <p>, <td>, <th>, <div>, <span>.

align_image_class_map : dict[str, WD_PARAGRAPH_ALIGNMENT]
    Карта CSS‑классов, управляющих выравниванием изображений.
    Например, класс `image-style-block-align-center` задаёт центрирование
    изображения в Word.

vertical_align_map : dict[str, str]
    Соответствие CSS‑свойства `vertical-align` внутренним обозначениям
    вертикального выравнивания в таблицах (top, center, bottom).

border_side : list[str]
    Список сторон границы, используемый при разборе CSS‑свойств таблиц:
    top, left, bottom, right.

border_style : dict[str, str]
    Соответствие CSS‑стилей границ Word‑стилям:
    - `solid` → `single`
    - `dotted` → `dotted`
    - `double` → `double`
    и т.д.

default_settings : DefaultConfigSchema
    Значения по умолчанию для:
        - align_paragraph — выравнивание абзацев (justify)
        - align_image — выравнивание изображений (center)
        - vertical_align — вертикальное выравнивание в таблицах (center)
        - table_style — стиль границ таблиц (ширина, стиль, цвет)

base_config : ConfigSchema
    Итоговая конфигурация, объединяющая все карты соответствий и
    настройки по умолчанию. Передаётся в HTMLtoDocx и используется
    при обработке каждого HTML‑элемента.
"""

align_map = {
    "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
    "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
    "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
    "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
}

align_image_class_map = {
    "image-style-block-align-left": WD_PARAGRAPH_ALIGNMENT.LEFT,
    "image-style-block-align-right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
    "image-style-block-align-center": WD_PARAGRAPH_ALIGNMENT.CENTER,
}

vertical_align_map = {"top": "top", "middle": "center", "bottom": "bottom"}

border_side = ["top", "left", "bottom", "right"]

border_style = {
    "none": "nil",
    "solid": "single",
    "dotted": "dotted",
    "dashed": "dash",
    "double": "double",
    "groove": "threeDEmboss",
    "ridge": "threeDEngrave",
    "inset": "inset",
    "outset": "outset",
}

default_settings = DefaultConfigSchema(
    align_paragraph=WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
    align_image=WD_PARAGRAPH_ALIGNMENT.CENTER,
    vertical_align='center',
    table_style=DefaultTableStyleSchema(
        width="1pt", style="single", color="000000"
    )
)

base_config = ConfigSchema(
    align_map=align_map,
    align_image_class_map=align_image_class_map,
    vertical_align_map=vertical_align_map,
    border_side=border_side,
    border_style=border_style,
    default_settings=default_settings
)
