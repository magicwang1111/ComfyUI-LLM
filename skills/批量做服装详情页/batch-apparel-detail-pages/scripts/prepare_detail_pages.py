# -*- coding: utf-8 -*-
"""Prepare merchant-standard-driven batch apparel detail-page jobs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MATERIAL_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".txt",
    ".md",
    ".csv",
    ".tsv",
    ".xlsx",
    ".xls",
    ".docx",
    ".doc",
    ".pdf",
}

DEFAULT_WIDTH = 3072
DEFAULT_HEIGHT = 4096

STANDARD_ROOT_NAME = "详情页标准解析"
STANDARD_IMAGE_DIR_NAME = "标准详情页原图"
STANDARD_TEMPLATE_FILENAME = "标准详情页解析.json"
STANDARD_GUIDE_FILENAME = "模板说明.txt"

OUTPUT_DIR_NAME = "生成文件"
THUMBNAIL_DIR_NAME = "缩略预览图"
UPLOAD_GUIDE_FILENAME = "请上传资料说明.txt"
PRODUCT_INFO_FILENAME = "产品信息.txt"
REPLACEMENT_PLAN_FILENAME = "template_replacement_plan.json"

INSTRUCTION_FILENAMES = {
    "说明.txt",
    "要求.txt",
    "产品信息.txt",
    "requirements.txt",
    "requirement.txt",
    "copy.txt",
    "text.txt",
    "卖点.txt",
    "商品信息.txt",
}

TEXT_EXTENSIONS = {".txt", ".md"}
TABLE_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls"}
DOCUMENT_EXTENSIONS = {".docx", ".doc", ".pdf"}

ROLE_KEYWORDS = {
    "logo": ["logo", "品牌", "商标", "brand"],
    "digital_human": ["数字人", "模特", "真人", "人物", "model", "human", "person"],
    "garment": ["衣服", "服装", "上衣", "裤", "裙", "外套", "卫衣", "衬衫", "针织", "garment", "clothes", "shirt", "dress"],
    "main_image": ["主图", "首图", "首屏", "封面", "hero", "main", "cover"],
    "fabric": ["面料", "材质", "布料", "纹理", "fabric", "material", "texture"],
    "detail": ["细节", "工艺", "图案", "花边", "领口", "袖口", "下摆", "detail", "craft"],
    "color": ["颜色", "色卡", "配色", "color", "colour", "swatch"],
    "size_table": ["尺码", "尺寸", "测量", "size", "measurement", "measurements"],
    "parameter": ["参数", "规格", "成分", "安全类别", "parameter", "spec", "composition"],
    "wash": ["洗护", "清洗", "水洗", "wash", "care"],
    "scene": ["场景", "氛围", "室内", "户外", "scene", "lifestyle"],
    "copy": ["文案", "标题", "卖点", "说明", "copy", "text", "headline"],
    "table": ["表格", "table", "csv", "xlsx"],
}

FACT_RISK_KEYWORDS = [
    "尺码",
    "尺寸",
    "面料",
    "材质",
    "成分",
    "洗护",
    "参数",
    "规格",
    "认证",
    "检测",
    "质检",
    "安全类别",
    "价格",
    "销量",
    "评价",
    "size",
    "fabric",
    "material",
    "wash",
    "care",
    "cert",
    "price",
    "review",
]

SIMPLE_IMAGE_DIR_NAMES = ["图片", "images", "image", "商品图片", "素材", "主图"]
SIMPLE_REFERENCE_DIR_NAMES = ["参考图", "reference", "references"]
SIMPLE_INFO_FILENAMES = ["info.txt", "商品信息.txt", "卖点.txt", "要求.txt", "requirements.txt"]

MATERIAL_ROOT_NAME = "资料文件"
REFERENCE_ROOT_NAME = "详情页参考"
REFERENCE_IMAGE_FOLDER_NAME = "参考图"
MODULE_GUIDE_FILENAME = "请上传资料说明.txt"

REQUIRED_OUTPUTS = [("00", "详情页长图")]

SIMPLE_MODULES = [
    ("01", "首屏主视觉"),
    ("02", "整体与上身效果"),
    ("03", "颜色与款式展示"),
    ("04", "细节与面料说明"),
    ("05", "尺码与洗护信息"),
    ("06", "搭配与卖点场景"),
]

ADVANCED_MODULE_OUTPUTS = [
    ("01", "首屏主视觉图", "01_首屏主视觉图资料"),
    ("02", "商品整体图", "02_商品整体图资料"),
    ("03", "上身效果图", "03_上身效果图资料"),
    ("04", "多角度展示图", "04_多角度展示图资料"),
    ("05", "颜色展示图", "05_颜色展示图资料"),
    ("06", "细节放大图", "06_细节放大图资料"),
    ("07", "面料纹理图", "07_面料纹理图资料"),
    ("08", "工艺说明图", "08_工艺说明图资料"),
    ("09", "尺码测量图", "09_尺码测量图资料"),
    ("10", "尺码表图", "10_尺码表图资料"),
    ("11", "搭配场景图", "11_搭配场景图资料"),
    ("12", "版型对比图", "12_版型对比图资料"),
    ("13", "厚薄季节说明图", "13_厚薄季节说明图资料"),
    ("14", "功能卖点图", "14_功能卖点图资料"),
    ("15", "洗护说明图", "15_洗护说明图资料"),
    ("16", "包装配件图", "16_包装配件图资料"),
    ("17", "质检认证图", "17_质检认证图资料"),
]

IGNORE_PRODUCT_DIRS = {
    STANDARD_ROOT_NAME,
    "详情页模板",
    "模板",
    "template",
    "templates",
    OUTPUT_DIR_NAME,
    THUMBNAIL_DIR_NAME,
    MATERIAL_ROOT_NAME,
    REFERENCE_ROOT_NAME,
    *SIMPLE_IMAGE_DIR_NAMES,
    *SIMPLE_REFERENCE_DIR_NAMES,
}


STANDARD_GUIDE_TEXT = """本目录保存商家标准详情页的解析结果。

使用方式：
1. 将用户提供的标准详情页原图放入“标准详情页原图”。
2. 用视觉理解能力解析标准图的页面尺寸、分屏结构、图片区、文字区、标签、装饰元素、字体层级、颜色、留白和可替换槽位。
3. 将解析结果写入“标准详情页解析.json”。
4. 运行脚本创建每个产品的上传资料文件夹，或扫描已有产品素材文件夹。
5. 生成 template_replacement_plan.json，让用户确认每个槽位替换、保留、缺失和风险项。
6. 用户确认后再按模板原排版生成详情页长图。

注意：
- 标准图只用于学习版式、排版和视觉节奏。
- 生成前必须保护模板布局，不要随意重排模块或修改图片文字框位置。
- 不要复制标准图里的品牌 logo、价格、销量、评价、认证、质检报告、原商品图或大段原文案。
"""


PRODUCT_INFO_TEXT = """请填写当前产品的真实信息。

产品名称：
颜色：
尺码：
面料：
洗护：
核心卖点：
禁用词或不要写的内容：
替换要求：
缺少素材时是否允许保留模板原内容：

没有把握的信息请留空。详情页只使用当前产品资料能支撑的内容。
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or scan merchant-standard-driven apparel detail-page folders."
    )
    parser.add_argument("--input-dir", required=True, help="Target folder for the detail-page job.")
    parser.add_argument(
        "--mode",
        choices=["standard", "simple", "advanced"],
        default="standard",
        help="Default is standard: parse a merchant standard page and create product upload folders.",
    )
    parser.add_argument("--standard", dest="mode", action="store_const", const="standard", help="Shortcut for --mode standard.")
    parser.add_argument("--simple", dest="mode", action="store_const", const="simple", help="Legacy shortcut for --mode simple.")
    parser.add_argument("--advanced", dest="mode", action="store_const", const="advanced", help="Legacy shortcut for --mode advanced.")
    parser.add_argument("--output-dir", help="Optional separate output folder. Defaults to each product's 生成文件 folder.")
    parser.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"], default="png")
    parser.add_argument("--module-width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--module-height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--recursive", action="store_true", help="Include deeper nested files when scanning legacy modes.")
    parser.add_argument("--export-modules", action="store_true", help="Plan separate section/module images as well as 00_详情页长图.")

    parser.add_argument("--init-standard", action="store_true", help="Create 详情页标准解析 and guide files.")
    parser.add_argument("--standard-image", action="append", default=[], help="Standard detail-page image to copy into 标准详情页原图. May be repeated.")
    parser.add_argument("--template-json", help="Parsed standard template JSON. Defaults to 详情页标准解析/标准详情页解析.json.")
    parser.add_argument("--product-count", type=int, help="Number of product folders to create.")
    parser.add_argument("--product-names", help="Product names separated by | or comma. Missing names are auto-numbered.")
    parser.add_argument("--materials-root", help="Optional folder containing product material folders. Defaults to --input-dir.")
    parser.add_argument(
        "--product-dir",
        action="append",
        default=[],
        help="Selected product material folder. Repeat this option for batch generation from multiple folders.",
    )
    parser.add_argument(
        "--missing-material-strategy",
        default="keep_template_with_risk_flag",
        choices=["keep_template_with_risk_flag", "keep_template", "mark_missing"],
        help="How replacement plans should treat slots without matched product material.",
    )
    parser.add_argument(
        "--folder-granularity",
        choices=["section", "slot"],
        default="section",
        help="Default creates one upload folder per parsed page section. Use slot only for very fine-grained upload folders.",
    )
    parser.add_argument(
        "--approval-mode",
        choices=["confirm_plan", "direct_generation"],
        default="confirm_plan",
        help="confirm_plan blocks final generation until user confirmation; direct_generation records the plan but does not block when the user already authorized direct output.",
    )
    parser.add_argument(
        "--direct-generation",
        dest="approval_mode",
        action="store_const",
        const="direct_generation",
        help="Shortcut for --approval-mode direct_generation.",
    )
    parser.add_argument("--create-products", action="store_true", help="Create product upload folders from parsed standard template JSON.")
    parser.add_argument("--scan-products", action="store_true", help="Scan existing product folders against parsed standard template JSON.")
    parser.add_argument("--build-replacement-plan", action="store_true", help="Scan product materials and write template_replacement_plan.json before generation.")

    parser.add_argument("--init-template", action="store_true", help="Compatibility: create simple or advanced template.")
    parser.add_argument("--ensure-guides", action="store_true", help="Compatibility: add missing guide files.")
    parser.add_argument("--product-name", default="01_产品名称", help="Compatibility product folder name.")
    parser.add_argument("--overwrite-guides", action="store_true", help="Overwrite guide files when creating folders.")
    return parser.parse_args()


def safe_name(value: str, fallback: str = "product") -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value, flags=re.UNICODE).strip("._-")
    return cleaned[:90] or fallback


def write_text_if_needed(path: Path, text: str, overwrite: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def inspect_image(path: Path) -> dict[str, Any]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {"status": "skipped", "reason": "unsupported file format"}
    if Image is None:
        return {"status": "candidate", "width": None, "height": None, "reason": None}
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:  # noqa: BLE001
        return {"status": "skipped", "reason": f"cannot open image: {exc}"}
    if width < 256 or height < 256:
        return {"status": "skipped", "width": width, "height": height, "reason": "image too small"}
    return {"status": "candidate", "width": width, "height": height, "reason": None}


def iter_files(folder: Path, recursive: bool = False) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    pattern = "**/*" if recursive else "*"
    return sorted([path for path in folder.glob(pattern) if path.is_file()], key=lambda item: str(item).lower())


def iter_image_files(folder: Path, recursive: bool = False) -> list[Path]:
    return [path for path in iter_files(folder, recursive=recursive) if path.suffix.lower() in SUPPORTED_EXTENSIONS]


def is_guide_file(path: Path) -> bool:
    return path.name == UPLOAD_GUIDE_FILENAME or path.name == MODULE_GUIDE_FILENAME


def is_effective_material_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.startswith(".") or path.name.startswith("~"):
        return False
    if is_guide_file(path):
        return False
    if path.name in {PRODUCT_INFO_FILENAME, STANDARD_GUIDE_FILENAME}:
        return False
    if path.suffix.lower() not in MATERIAL_EXTENSIONS:
        return False
    if path.suffix.lower() in {".txt", ".md", ".csv", ".tsv"}:
        try:
            if not path.read_text(encoding="utf-8-sig", errors="ignore").strip():
                return False
        except Exception:  # noqa: BLE001
            return False
    return True


def material_files(folder: Path) -> list[Path]:
    return sorted([path for path in folder.rglob("*") if is_effective_material_file(path)], key=lambda item: str(item).lower())


def default_template_path(input_dir: Path) -> Path:
    return input_dir / STANDARD_ROOT_NAME / STANDARD_TEMPLATE_FILENAME


def init_standard_workspace(input_dir: Path, standard_images: list[str], overwrite: bool = False) -> dict[str, Any]:
    standard_root = input_dir / STANDARD_ROOT_NAME
    image_dir = standard_root / STANDARD_IMAGE_DIR_NAME
    created: list[str] = []
    copied: list[str] = []

    image_dir.mkdir(parents=True, exist_ok=True)
    guide_path = standard_root / STANDARD_GUIDE_FILENAME
    if write_text_if_needed(guide_path, STANDARD_GUIDE_TEXT, overwrite=overwrite):
        created.append(str(guide_path))

    for raw_image in standard_images:
        src = Path(raw_image).expanduser().resolve()
        if not src.exists() or not src.is_file():
            continue
        dest = image_dir / src.name
        if overwrite or not dest.exists():
            shutil.copy2(src, dest)
            copied.append(str(dest))

    return {
        "standard_root": str(standard_root),
        "standard_image_dir": str(image_dir),
        "created_files": created,
        "copied_standard_images": copied,
    }


def load_template(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"template json does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_slot(section: dict[str, Any], slot: dict[str, Any], index: int) -> dict[str, Any]:
    section_number = str(section.get("number") or section.get("section_number") or f"{index:02d}")
    section_name = str(section.get("section_name") or section.get("name") or f"模块{section_number}")
    slot_name = str(slot.get("slot_name") or slot.get("name") or slot.get("label") or f"资料{index:02d}")
    folder_name = slot.get("folder_name")
    if not folder_name:
        folder_name = f"{section_number}_{section_name}_{slot_name}"
    slot_type = str(slot.get("type") or slot.get("slot_type") or "mixed")
    guide = str(slot.get("guide") or slot.get("description") or f"请上传或填写“{slot_name}”需要的当前产品资料。")
    return {
        "section_number": section_number,
        "section_name": section_name,
        "slot_name": slot_name,
        "folder_name": safe_name(str(folder_name), fallback=f"{section_number}_{slot_name}"),
        "type": slot_type,
        "required": bool(slot.get("required", False)),
        "replaceable": bool(slot.get("replaceable", True)),
        "guide": guide,
    }


def template_slots(template: dict[str, Any]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for section_index, section in enumerate(template.get("sections", []), start=1):
        upload_slots = section.get("upload_slots") or section.get("slots") or []
        if not upload_slots:
            section_name = str(section.get("section_name") or section.get("name") or f"模块{section_index:02d}")
            upload_slots = [
                {
                    "slot_name": "本模块资料",
                    "folder_name": f"{section_index:02d}_{section_name}_上传本模块资料",
                    "type": "mixed",
                    "required": False,
                    "guide": "上传本模块需要的图片、文字、表格或要求。",
                }
            ]
        for slot_index, slot in enumerate(upload_slots, start=1):
            slots.append(normalize_slot(section, slot, slot_index))
    return slots


def template_sections(template: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for section_index, section in enumerate(template.get("sections", []), start=1):
        section_number = str(section.get("number") or section.get("section_number") or f"{section_index:02d}")
        section_name = str(section.get("section_name") or section.get("name") or f"模块{section_number}")
        upload_slots = section.get("upload_slots") or section.get("slots") or []
        normalized_slots = [normalize_slot(section, slot, slot_index) for slot_index, slot in enumerate(upload_slots, start=1)]
        if not normalized_slots:
            normalized_slots = [
                {
                    "section_number": section_number,
                    "section_name": section_name,
                    "slot_name": "本模块资料",
                    "folder_name": f"{section_number}_{section_name}",
                    "type": "mixed",
                    "required": False,
                    "guide": "上传本模块需要的图片、文字、表格或要求。",
                }
            ]
        sections.append(
            {
                "section_number": section_number,
                "section_name": section_name,
                "folder_name": safe_name(str(section.get("folder_name") or f"{section_number}_{section_name}"), fallback=f"{section_number}_{section_name}"),
                "layout_summary": str(section.get("layout_summary") or ""),
                "required": any(slot["required"] for slot in normalized_slots),
                "slots": normalized_slots,
            }
        )
    return sections


def parse_product_names(product_count: int, raw_names: str | None) -> list[str]:
    names: list[str] = []
    if raw_names:
        parts = re.split(r"[|,，\n]+", raw_names)
        names = [safe_name(part.strip()) for part in parts if part.strip()]
    while len(names) < product_count:
        names.append(f"{len(names) + 1:02d}_产品")
    return names[:product_count]


def slot_guide_text(slot: dict[str, Any]) -> str:
    required = "必填" if slot["required"] else "可选"
    return f"""本文件夹用于：{slot['slot_name']}

所属标准模块：{slot['section_number']}_{slot['section_name']}
资料类型：{slot['type']}
是否必填：{required}

请上传或填写：
{slot['guide']}

建议：
1. 图片资料直接放入本文件夹。
2. 文案资料写入 text.txt。
3. 表格或尺码资料可放入 table.csv、xlsx 或截图。
4. 特殊要求写入 requirements.txt。

注意：
- 只放当前产品自己的资料。
- 不要放其他产品图片。
- 不要上传无法证明当前槽位内容的杂图。
- 不要填写销量、评价、认证、功能数据等无法证明的信息。
"""


def section_guide_text(section: dict[str, Any]) -> str:
    required = "含必填资料" if section["required"] else "可选资料为主"
    slot_lines = []
    for slot in section["slots"]:
        must = "必填" if slot["required"] else "可选"
        slot_lines.append(f"- {slot['slot_name']}（{slot['type']}，{must}）：{slot['guide']}")
    slot_text = "\n".join(slot_lines)
    layout_text = section["layout_summary"] or "按标准详情页中本模块的版式、图文比例和视觉节奏生成。"
    return f"""本文件夹用于上传：{section['section_number']}_{section['section_name']}

本模块要求：{required}
标准图版式说明：{layout_text}

请把本模块需要的资料都放在这个文件夹里：
{slot_text}

建议放法：
1. 商品图、模特图、细节图、尺码图等图片直接放入本文件夹。
2. 文案、卖点、参数说明写入 text.txt。
3. 尺码表、颜色表、参数表可放入 table.csv、xlsx 或截图。
4. 特殊要求写入 requirements.txt。

注意：
- 只放当前产品自己的资料。
- 不要放其他产品图片。
- 不要填写销量、评价、认证、功能数据等无法证明的信息。
- 本模块可以包含多个图片或文字槽位，不需要再拆成很多小文件夹。
"""


def create_product_folders(
    input_dir: Path,
    template: dict[str, Any],
    product_count: int,
    product_names: list[str],
    folder_granularity: str = "section",
    overwrite: bool = False,
) -> dict[str, Any]:
    sections = template_sections(template)
    slots = template_slots(template)
    if folder_granularity == "section" and not sections:
        raise ValueError("template json has no sections")
    if folder_granularity == "slot" and not slots:
        raise ValueError("template json has no sections or upload slots")

    products: list[dict[str, Any]] = []
    for index, product_name in enumerate(product_names, start=1):
        product_folder_name = safe_name(product_name, fallback=f"{index:02d}_产品")
        if not re.match(r"^\d{2}_", product_folder_name):
            product_folder_name = f"{index:02d}_{product_folder_name}"
        product_dir = input_dir / product_folder_name
        product_dir.mkdir(parents=True, exist_ok=True)
        (product_dir / OUTPUT_DIR_NAME).mkdir(exist_ok=True)
        (product_dir / THUMBNAIL_DIR_NAME).mkdir(exist_ok=True)

        created_files: list[str] = []
        if write_text_if_needed(product_dir / PRODUCT_INFO_FILENAME, PRODUCT_INFO_TEXT, overwrite=overwrite):
            created_files.append(str(product_dir / PRODUCT_INFO_FILENAME))

        upload_records: list[dict[str, Any]] = []
        seen_names: dict[str, int] = {}
        if folder_granularity == "slot":
            for slot_index, slot in enumerate(slots, start=1):
                base_name = safe_name(slot["folder_name"], fallback=f"{slot_index:02d}_{slot['slot_name']}")
                seen_names[base_name] = seen_names.get(base_name, 0) + 1
                slot_folder_name = base_name if seen_names[base_name] == 1 else f"{base_name}_{seen_names[base_name]}"
                slot_dir = product_dir / slot_folder_name
                slot_dir.mkdir(parents=True, exist_ok=True)
                guide_path = slot_dir / UPLOAD_GUIDE_FILENAME
                if write_text_if_needed(guide_path, slot_guide_text(slot), overwrite=overwrite):
                    created_files.append(str(guide_path))
                if slot["type"].lower() in {"text", "copy", "caption", "table", "data"}:
                    seed_name = "table.csv" if slot["type"].lower() in {"table", "data"} else "text.txt"
                    seed_path = slot_dir / seed_name
                    if write_text_if_needed(seed_path, "", overwrite=False):
                        created_files.append(str(seed_path))
                upload_records.append({**slot, "folder_kind": "slot", "upload_dir": str(slot_dir)})
        else:
            for section in sections:
                base_name = safe_name(section["folder_name"], fallback=f"{section['section_number']}_{section['section_name']}")
                seen_names[base_name] = seen_names.get(base_name, 0) + 1
                section_folder_name = base_name if seen_names[base_name] == 1 else f"{base_name}_{seen_names[base_name]}"
                section_dir = product_dir / section_folder_name
                section_dir.mkdir(parents=True, exist_ok=True)
                guide_path = section_dir / UPLOAD_GUIDE_FILENAME
                if write_text_if_needed(guide_path, section_guide_text(section), overwrite=overwrite):
                    created_files.append(str(guide_path))
                text_path = section_dir / "text.txt"
                if write_text_if_needed(text_path, "", overwrite=False):
                    created_files.append(str(text_path))
                upload_records.append({**section, "folder_kind": "section", "upload_dir": str(section_dir)})

        products.append(
            {
                "product_name": product_folder_name,
                "product_dir": str(product_dir),
                "folder_granularity": folder_granularity,
                "upload_folder_count": len(upload_records),
                "slot_count": len(slots),
                "upload_folders": upload_records,
                "created_files": created_files,
                "output_dir": str(product_dir / OUTPUT_DIR_NAME),
                "planned_outputs": planned_outputs(product_dir / OUTPUT_DIR_NAME, "png", True, template),
            }
        )

    return {
        "product_count": len(products),
        "folder_granularity": folder_granularity,
        "upload_folder_count_per_product": len(sections) if folder_granularity == "section" else len(slots),
        "slot_count_per_product": len(slots),
        "products": products,
    }


def planned_outputs(output_dir: Path, output_format: str, export_modules: bool, template: dict[str, Any] | None = None) -> list[dict[str, str]]:
    ext = "jpg" if output_format == "jpeg" else output_format
    outputs = list(REQUIRED_OUTPUTS)
    if export_modules and template:
        for section in template.get("sections", []):
            number = str(section.get("number") or section.get("section_number") or "00")
            label = str(section.get("section_name") or section.get("name") or "模块图")
            outputs.append((number, label))
    return [
        {
            "number": number,
            "label": label,
            "path": str(output_dir / f"{number}_{label}.{ext}"),
        }
        for number, label in outputs
    ]


def product_dirs(input_dir: Path) -> list[Path]:
    ignored = {name.lower() for name in IGNORE_PRODUCT_DIRS}
    return sorted(
        [
            path
            for path in input_dir.iterdir()
            if path.is_dir() and not path.name.startswith(".") and path.name.lower() not in ignored
        ],
        key=lambda item: item.name.lower(),
    )


def scan_standard_products(input_dir: Path, template: dict[str, Any], output_format: str, export_modules: bool, folder_granularity: str = "section") -> dict[str, Any]:
    slots = template_slots(template)
    sections = template_sections(template)
    products: list[dict[str, Any]] = []
    for product_dir in product_dirs(input_dir):
        upload_records: list[dict[str, Any]] = []
        missing_required: list[str] = []
        records = slots if folder_granularity == "slot" else sections
        for record in records:
            if folder_granularity == "slot":
                upload_dir = product_dir / record["folder_name"]
                match_name = record["slot_name"]
                required = record["required"]
                missing_label = record["slot_name"]
            else:
                upload_dir = product_dir / record["folder_name"]
                match_name = record["section_name"]
                required = record["required"]
                missing_label = record["section_name"]
            if not upload_dir.exists():
                matches = sorted(product_dir.glob(f"*{match_name}*"))
                upload_dir = matches[0] if matches else upload_dir
            files = material_files(upload_dir) if upload_dir.exists() else []
            image_files = [path for path in files if path.suffix.lower() in SUPPORTED_EXTENSIONS]
            status = "ready" if files else "missing_required" if required else "empty_optional"
            if status == "missing_required":
                missing_required.append(missing_label)
            upload_records.append(
                {
                    **record,
                    "folder_kind": folder_granularity,
                    "upload_dir": str(upload_dir),
                    "status": status,
                    "material_count": len(files),
                    "image_count": len(image_files),
                    "materials": [str(path) for path in files],
                }
            )
        products.append(
            {
                "product_name": product_dir.name,
                "product_dir": str(product_dir),
                "folder_granularity": folder_granularity,
                "upload_folder_count": len(upload_records),
                "slot_count": len(slots),
                "ready_folder_count": len([folder for folder in upload_records if folder["status"] == "ready"]),
                "missing_required_upload_folders": missing_required,
                "missing_required_slots": missing_required,
                "upload_folders": upload_records,
                "output_dir": str(product_dir / OUTPUT_DIR_NAME),
                "planned_outputs": planned_outputs(product_dir / OUTPUT_DIR_NAME, output_format, export_modules, template),
            }
        )
    return {"product_count": len(products), "products": products}


def read_text_preview(path: Path, max_chars: int = 4000) -> str:
    if path.suffix.lower() not in (TEXT_EXTENSIONS | {".csv", ".tsv"}):
        return ""
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore").strip()[:max_chars]
    except Exception:  # noqa: BLE001
        return ""


def material_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return "image"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix in TABLE_EXTENSIONS:
        return "table"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    return "other"


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def detect_roles(path: Path, text: str) -> list[str]:
    haystack = f"{path.parent.name} {path.stem} {path.suffix} {text}".lower()
    roles: list[str] = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            roles.append(role)

    kind = material_kind(path)
    if kind == "table":
        roles.append("table")
    elif kind == "text" and not roles:
        roles.append("copy")
    elif kind == "image" and not roles:
        roles.append("main_image")
    return unique_values(roles)


def instruction_records(product_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in iter_files(product_dir, recursive=True):
        lower_name = path.name.lower()
        is_instruction = (
            path.name in INSTRUCTION_FILENAMES
            or lower_name in {name.lower() for name in INSTRUCTION_FILENAMES}
            or "说明" in path.name
            or "要求" in path.name
            or "requirement" in lower_name
        )
        if not is_instruction:
            continue
        text = read_text_preview(path, max_chars=6000)
        if text:
            records.append({"path": str(path), "text": text})
    return records


def collect_product_material_records(product_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in material_files(product_dir):
        text = read_text_preview(path)
        kind = material_kind(path)
        image_info = inspect_image(path) if kind == "image" else {}
        search_text = f"{path.parent.name} {path.stem} {path.suffix} {text}".lower()
        records.append(
            {
                "path": str(path),
                "filename": path.name,
                "kind": kind,
                "extension": path.suffix.lower(),
                "roles": detect_roles(path, text),
                "text_excerpt": text[:300] if text else "",
                "image_info": image_info,
                "_search_text": search_text,
            }
        )
    return records


def slot_search_text(section: dict[str, Any], slot: dict[str, Any]) -> str:
    return " ".join(
        [
            str(section.get("section_number", "")),
            str(section.get("section_name", "")),
            str(section.get("layout_summary", "")),
            str(slot.get("slot_name", "")),
            str(slot.get("type", "")),
            str(slot.get("guide", "")),
        ]
    ).lower()


def expected_roles_for_slot(section: dict[str, Any], slot: dict[str, Any]) -> list[str]:
    text = slot_search_text(section, slot)
    roles: list[str] = []
    for role, keywords in ROLE_KEYWORDS.items():
        if role in text or any(keyword.lower() in text for keyword in keywords):
            roles.append(role)

    slot_type = str(slot.get("type", "")).lower()
    slot_name = str(slot.get("slot_name", "")).lower()
    if "logo" in slot_type or "logo" in slot_name:
        roles.append("logo")
    if "image" in slot_type or "图" in slot_name:
        roles.append("main_image")
    if "text" in slot_type or "copy" in slot_type or "文案" in slot_name:
        roles.append("copy")
    if "table" in slot_type or "data" in slot_type or "表" in slot_name:
        roles.append("table")
    return unique_values(roles)


def slot_has_fact_risk(section: dict[str, Any], slot: dict[str, Any]) -> bool:
    text = slot_search_text(section, slot)
    return any(keyword.lower() in text for keyword in FACT_RISK_KEYWORDS)


def compatibility_score(slot: dict[str, Any], expected_roles: list[str], material: dict[str, Any]) -> int:
    kind = material["kind"]
    slot_type = str(slot.get("type", "")).lower()
    slot_name = str(slot.get("slot_name", "")).lower()
    expected = set(expected_roles)
    image_roles = {"logo", "digital_human", "garment", "main_image", "fabric", "detail", "color", "scene"}

    if kind == "image" and (expected & image_roles or "image" in slot_type or "图" in slot_name):
        return 15
    if kind == "text" and ("copy" in expected or "text" in slot_type or "文案" in slot_name):
        return 15
    if kind == "table" and ({"table", "size_table", "parameter"} & expected or "table" in slot_type or "表" in slot_name):
        return 18
    if kind == "document" and ({"copy", "parameter", "size_table", "wash"} & expected):
        return 8
    return 0


def public_material_record(material: dict[str, Any], score: int) -> dict[str, Any]:
    return {
        "path": material["path"],
        "filename": material["filename"],
        "kind": material["kind"],
        "roles": material["roles"],
        "score": score,
        "text_excerpt": material.get("text_excerpt", ""),
        "image_info": material.get("image_info", {}),
    }


def score_material_for_slot(section: dict[str, Any], slot: dict[str, Any], material: dict[str, Any]) -> int:
    expected_roles = expected_roles_for_slot(section, slot)
    material_roles = set(material.get("roles", []))
    expected = set(expected_roles)
    score = 0

    if expected and expected & material_roles:
        score += 55
    score += compatibility_score(slot, expected_roles, material)

    material_text = str(material.get("_search_text", ""))
    section_number = str(section.get("section_number", "")).lower()
    section_name = str(section.get("section_name", "")).lower()
    slot_name = str(slot.get("slot_name", "")).lower()

    if section_number and section_number in material_text:
        score += 8
    if section_name and section_name in material_text:
        score += 15
    if slot_name and slot_name in material_text:
        score += 20

    for role in expected_roles:
        for keyword in ROLE_KEYWORDS.get(role, []):
            if keyword.lower() in material_text:
                score += 6

    return min(score, 100)


def adaptation_rules_for_slot(slot: dict[str, Any], expected_roles: list[str]) -> list[str]:
    rules = [
        "保持模板槽位位置、比例、边距和视觉节奏",
        "module_shape_fidelity：先复刻模板模块外形、留白、装饰边界、卡片/圆形/云朵/表格等结构，再替换内容",
    ]
    slot_type = str(slot.get("type", "")).lower()
    expected = set(expected_roles)

    if {"logo", "digital_human", "garment", "main_image", "fabric", "detail", "color", "scene"} & expected or "image" in slot_type:
        rules.extend(["图片自动裁剪、缩放、居中或补背景，但不能拉伸变形", "主体不能被遮挡，服装细节优先完整可见"])
    if "copy" in expected or "text" in slot_type:
        rules.extend(["保持模板字号层级、颜色、行距和对齐方式", "文案自动换行或压缩，不能溢出或重叠"])
    if {"table", "size_table", "parameter"} & expected or "table" in slot_type:
        rules.extend(["保持模板表格表头、列宽、行高、线条、底色和文字样式", "数据列不一致时标记需要用户确认"])
    if "digital_human" in expected:
        rules.extend(
            [
                "current_product_clothing：数字人或模特必须穿当前产品服装，不能穿模板原商品或其他款",
                "先复刻模板人物姿势、神态、动作、镜头远近、主体占比、背景和光线方向，再生成上身图",
                "禁止白底人物硬贴；背景和道具要与模板场景一致或高度相似",
                "按写实摄影质感筛选结果，避免呆板表情、假光、塑料皮肤、手部异常和衣服边缘融化",
                "candidate_pool_selection：同一模板姿势至少生成多张候选，做拼图对比后只使用最接近模板的一张",
            ]
        )
    return rules


def quality_gates_for_slot(slot: dict[str, Any], expected_roles: list[str]) -> dict[str, Any]:
    slot_type = str(slot.get("type", "")).lower()
    expected = set(expected_roles)
    gates: dict[str, Any] = {
        "template_lock": ["position", "size_ratio", "margins", "crop_style", "visual_rhythm"],
        "module_shape_fidelity": [
            "section_order_matches_template",
            "slot_bbox_and_aspect_ratio_match_template",
            "decorative_shape_matches_template",
            "typography_hierarchy_matches_template",
            "spacing_and_white_space_match_template",
        ],
    }
    if {"digital_human", "scene"} & expected or "model_scene" in slot_type:
        gates["model_scene_quality_gates"] = [
            "current_product_clothing_visible_and_correct",
            "template_pose_expression_action_recreated",
            "template_camera_distance_and_subject_scale_recreated",
            "template_background_and_props_recreated_or_generated",
            "natural_window_or_template_matching_light_direction",
            "no_white_background_cutout",
            "no_wrong_garment",
            "no_stiff_expression",
            "no_obvious_ai_artifacts",
        ]
        gates["candidate_pool_selection"] = {
            "minimum_candidates_per_template_pose": 4,
            "make_contact_sheet_before_selection": True,
            "reject_if_wrong_garment_or_white_background": True,
            "reject_if_camera_distance_or_pose_does_not_match_template": True,
            "avoid_reusing_same_scene_unless_template_repeats_exactly": True,
        }
    if {"copy", "table", "size_table", "parameter"} & expected or "text" in slot_type or "table" in slot_type:
        gates["text_table_quality_gates"] = [
            "redraw_at_output_resolution",
            "no_overlap",
            "no_garbled_chinese",
            "facts_supported_by_product_materials_or_flagged",
        ]
    return gates


def generation_requirements(approval_mode: str) -> dict[str, Any]:
    return {
        "approval_mode": approval_mode,
        "direct_generation": approval_mode == "direct_generation",
        "template_slot_map": {
            "required": True,
            "fields": [
                "section_order",
                "section_bbox",
                "image_slot_bbox",
                "text_slot_bbox",
                "logo_slot_bbox",
                "table_slot_bbox",
                "decoration_shapes",
                "subject_safe_zone",
                "crop_mode",
                "module_shape_tags",
            ],
        },
        "style_tone_lock": {
            "extract_from_template": True,
            "preserve_palette_family": True,
            "preserve_logo_scale_and_weight": True,
            "preserve_soft_background_and_spacing": True,
            "do_not_let_dark_product_assets_dominate_page_chrome": True,
        },
        "visual_similarity_audit": {
            "required": True,
            "compare_full_page_preview": True,
            "compare_key_crops_to_template": True,
            "fail_if_page_feels_redesigned_instead_of_template_replaced": True,
            "review_dimensions": [
                "layout",
                "module_shape",
                "image_density",
                "typography",
                "palette",
                "lifestyle_photo_rhythm",
            ],
        },
        "lifestyle_scene_variation": {
            "required_when_template_has_multiple_model_modules": True,
            "minimum_distinct_scene_angles": 5,
            "map_each_generated_scene_to_a_template_reference_crop": True,
            "avoid_obvious_repetition": True,
        },
        "native_2k_master": {
            "enabled_when_user_requests_hd_or_2k": True,
            "minimum_width_px": 2160,
            "redraw_text_tables_lines_icons_at_target_resolution": True,
            "do_not_only_upscale_finished_low_res_png": True,
        },
        "preview_and_crop_qa": [
            "full_page_preview",
            "hero_crop",
            "fabric_detail_crop",
            "size_table_crop",
            "model_scene_crop",
            "bottom_repeat_crop",
        ],
    }


def replacement_for_slot(
    section: dict[str, Any],
    slot: dict[str, Any],
    materials: list[dict[str, Any]],
    missing_strategy: str,
) -> dict[str, Any]:
    expected_roles = expected_roles_for_slot(section, slot)
    scored = sorted(
        [
            (score_material_for_slot(section, slot, material), material)
            for material in materials
        ],
        key=lambda item: item[0],
        reverse=True,
    )
    candidates = [(score, material) for score, material in scored if score >= 25]
    risk_flags: list[str] = []

    if not slot.get("replaceable", True):
        action = "keep_template"
        matched: list[dict[str, Any]] = []
        risk_flags.append("slot_marked_not_replaceable")
    elif candidates and candidates[0][0] >= 45:
        action = "replace"
        matched = [public_material_record(material, score) for score, material in candidates[:3]]
    elif candidates:
        action = "needs_confirmation"
        matched = [public_material_record(material, score) for score, material in candidates[:3]]
        risk_flags.append("low_confidence_match")
    else:
        action = "keep_template" if missing_strategy != "mark_missing" else "needs_confirmation"
        matched = []
        if slot.get("required", False):
            risk_flags.append("missing_required_material")

    if slot_has_fact_risk(section, slot) and action in {"keep_template", "needs_confirmation"}:
        risk_flags.append("product_fact_requires_confirmation")
    elif slot_has_fact_risk(section, slot) and action == "replace":
        risk_flags.append("verify_product_fact_material")

    return {
        "section_number": section["section_number"],
        "section_name": section["section_name"],
        "slot_name": slot["slot_name"],
        "slot_type": slot["type"],
        "required": slot["required"],
        "replaceable": slot.get("replaceable", True),
        "expected_roles": expected_roles,
        "action": action,
        "missing_material_strategy": missing_strategy,
        "matched_materials": matched,
        "adaptation_rules": adaptation_rules_for_slot(slot, expected_roles),
        "quality_gates": quality_gates_for_slot(slot, expected_roles),
        "risk_flags": unique_values(risk_flags),
    }


def replacement_summary(replacements: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "replace_count": len([item for item in replacements if item["action"] == "replace"]),
        "keep_template_count": len([item for item in replacements if item["action"] == "keep_template"]),
        "needs_confirmation_count": len([item for item in replacements if item["action"] == "needs_confirmation"]),
        "missing_required_count": len([item for item in replacements if "missing_required_material" in item["risk_flags"]]),
        "risk_count": len([item for item in replacements if item["risk_flags"]]),
    }


def discover_material_product_dirs(materials_root: Path) -> list[Path]:
    if not materials_root.exists() or not materials_root.is_dir():
        return []

    direct_files = [path for path in iter_files(materials_root, recursive=False) if is_effective_material_file(path)]
    if direct_files or instruction_records(materials_root):
        return [materials_root]

    child_names = [path.name.lower() for path in product_dirs(materials_root)]
    slot_like_keywords = ["主图", "首屏", "场景", "模特", "数字人", "面料", "细节", "颜色", "尺码", "参数", "洗护", "logo"]
    if child_names and any(any(keyword.lower() in name for keyword in slot_like_keywords) for name in child_names):
        return [materials_root]

    children = product_dirs(materials_root)
    if children:
        return children
    return [materials_root]


def selected_product_dirs(raw_dirs: list[str]) -> list[Path]:
    dirs: list[Path] = []
    seen: set[str] = set()
    for raw_dir in raw_dirs:
        path = Path(raw_dir).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"selected product folder does not exist: {path}")
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        dirs.append(path)
    return dirs


def build_replacement_plan(
    input_dir: Path,
    materials_root: Path,
    template: dict[str, Any],
    template_path: Path,
    missing_strategy: str,
    approval_mode: str,
    explicit_product_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    if explicit_product_dirs:
        product_source_dirs = explicit_product_dirs
    elif not materials_root.exists() or not materials_root.is_dir():
        raise FileNotFoundError(f"materials root does not exist: {materials_root}")
    else:
        product_source_dirs = discover_material_product_dirs(materials_root)
    if not product_source_dirs:
        raise FileNotFoundError("no product material folders were selected or discovered")

    sections = template_sections(template)
    products: list[dict[str, Any]] = []
    used_root_paths: set[str] = set()
    status = "direct_generation_ready" if approval_mode == "direct_generation" else "needs_user_confirmation"
    requires_user_confirmation = approval_mode != "direct_generation"
    generation_rules = generation_requirements(approval_mode)

    for product_source_dir in product_source_dirs:
        materials = collect_product_material_records(product_source_dir)
        instructions = instruction_records(product_source_dir)
        replacements: list[dict[str, Any]] = []
        matched_paths: set[str] = set()

        for section in sections:
            for slot in section["slots"]:
                replacement = replacement_for_slot(section, slot, materials, missing_strategy)
                replacements.append(replacement)
                if replacement["action"] in {"replace", "needs_confirmation"}:
                    for material in replacement["matched_materials"]:
                        matched_paths.add(material["path"])

        product_output_dir = input_dir / safe_name(product_source_dir.name, fallback="01_产品") / OUTPUT_DIR_NAME
        if product_source_dir.resolve() == (input_dir / product_source_dir.name).resolve():
            product_output_dir = product_source_dir / OUTPUT_DIR_NAME
        product_output_dir.mkdir(parents=True, exist_ok=True)
        plan_path = product_output_dir / REPLACEMENT_PLAN_FILENAME

        unmapped = [
            public_material_record(material, 0)
            for material in materials
            if material["path"] not in matched_paths and not is_guide_file(Path(material["path"]))
        ]
        product_plan = {
            "status": status,
            "approval_mode": approval_mode,
            "template_locked": True,
            "template_json": str(template_path),
            "product_name": product_source_dir.name,
            "product_dir": str(product_source_dir),
            "output_dir": str(product_output_dir),
            "instructions": instructions,
            "replacement_summary": replacement_summary(replacements),
            "replacements": replacements,
            "unmapped_materials": unmapped,
            "generation_requirements": generation_rules,
            "requires_user_confirmation": requires_user_confirmation,
        }
        plan_path.write_text(json.dumps(product_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        product_plan["plan_path"] = str(plan_path)
        products.append(product_plan)
        used_root_paths.add(str(product_source_dir))

    summary_plan = {
        "status": status,
        "mode": "standard",
        "approval_mode": approval_mode,
        "template_locked": True,
        "missing_material_strategy": missing_strategy,
        "input_dir": str(input_dir),
        "materials_root": str(materials_root),
        "selected_product_dirs": [str(path) for path in explicit_product_dirs] if explicit_product_dirs else [],
        "template_json": str(template_path),
        "product_count": len(products),
        "generation_requirements": generation_rules,
        "requires_user_confirmation": requires_user_confirmation,
        "products": products,
    }
    summary_path = input_dir / STANDARD_ROOT_NAME / REPLACEMENT_PLAN_FILENAME
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "materials_root": str(materials_root),
        "product_count": len(products),
        "summary_plan_path": str(summary_path),
        "products": products,
        "scanned_product_dirs": sorted(used_root_paths),
        "selected_product_dirs": [str(path) for path in explicit_product_dirs] if explicit_product_dirs else [],
    }


def run_standard(args: argparse.Namespace, input_dir: Path) -> int:
    if args.init_standard:
        result = init_standard_workspace(input_dir, args.standard_image, overwrite=args.overwrite_guides)
        print(json.dumps({"status": "ok", "mode": "standard", "action": "init_standard", **result}, ensure_ascii=False, indent=2))
        return 0

    template_path = Path(args.template_json).expanduser().resolve() if args.template_json else default_template_path(input_dir)
    try:
        template = load_template(template_path)
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "mode": "standard",
                    "reason": "template json is required before creating or scanning product folders",
                    "template_json": str(template_path),
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    summary: dict[str, Any] = {
        "status": "ok",
        "mode": "standard",
        "input_dir": str(input_dir),
        "template_json": str(template_path),
        "template_name": template.get("template_name", "商家标准详情页"),
        "section_count": len(template.get("sections", [])),
        "slot_count": len(template_slots(template)),
        "folder_granularity": args.folder_granularity,
    }

    if args.create_products:
        if not args.product_count or args.product_count < 1:
            print(json.dumps({**summary, "status": "blocked", "reason": "product-count is required with --create-products"}, ensure_ascii=False, indent=2))
            return 2
        names = parse_product_names(args.product_count, args.product_names)
        summary["action"] = "create_products"
        summary.update(create_product_folders(input_dir, template, args.product_count, names, folder_granularity=args.folder_granularity, overwrite=args.overwrite_guides))
    elif args.build_replacement_plan:
        materials_root = Path(args.materials_root).expanduser().resolve() if args.materials_root else input_dir
        summary["action"] = "build_replacement_plan"
        try:
            explicit_product_dirs = selected_product_dirs(args.product_dir) if args.product_dir else []
            summary.update(
                build_replacement_plan(
                    input_dir,
                    materials_root,
                    template,
                    template_path,
                    args.missing_material_strategy,
                    args.approval_mode,
                    explicit_product_dirs=explicit_product_dirs,
                )
            )
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({**summary, "status": "blocked", "reason": "failed to build replacement plan", "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
    elif args.scan_products:
        summary["action"] = "scan_products"
        summary.update(scan_standard_products(input_dir, template, args.output_format, args.export_modules, folder_granularity=args.folder_granularity))
    else:
        summary["action"] = "inspect_template"
        summary["sections"] = template_sections(template)
        summary["slots"] = template_slots(template)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def collect_simple_images(product_dir: Path, recursive: bool) -> list[Path]:
    images: dict[str, Path] = {}
    for folder_name in SIMPLE_IMAGE_DIR_NAMES:
        for path in iter_image_files(product_dir / folder_name, recursive=True):
            images[str(path.resolve())] = path
    for path in iter_image_files(product_dir, recursive=False):
        images[str(path.resolve())] = path
    if recursive:
        ignored = {name.lower() for name in IGNORE_PRODUCT_DIRS}
        for child in product_dir.iterdir():
            if child.is_dir() and child.name.lower() not in ignored:
                for path in iter_image_files(child, recursive=True):
                    images[str(path.resolve())] = path
    return sorted(images.values(), key=lambda item: str(item).lower())


def collect_info_files(product_dir: Path) -> list[Path]:
    names = {name.lower() for name in SIMPLE_INFO_FILENAMES}
    return sorted([path for path in product_dir.iterdir() if path.is_file() and path.name.lower() in names], key=lambda item: item.name.lower())


def simple_product_has_material(product_dir: Path, recursive: bool) -> bool:
    return bool(collect_simple_images(product_dir, recursive=recursive) or collect_info_files(product_dir))


def simple_groups(input_dir: Path, recursive: bool) -> list[Path]:
    subdirs = [path for path in product_dirs(input_dir) if simple_product_has_material(path, recursive=recursive)]
    if subdirs:
        return subdirs
    return [input_dir] if simple_product_has_material(input_dir, recursive=recursive) else []


def run_simple(args: argparse.Namespace, input_dir: Path, output_dir: Path | None) -> int:
    products: list[dict[str, Any]] = []
    skipped_files: list[dict[str, Any]] = []
    for product_dir in simple_groups(input_dir, recursive=args.recursive):
        valid_images: list[dict[str, Any]] = []
        for image in collect_simple_images(product_dir, recursive=args.recursive):
            record = {"filename": image.name, "path": str(image), **inspect_image(image)}
            if record["status"] == "candidate":
                valid_images.append(record)
            else:
                skipped_files.append(record)
        if not valid_images:
            continue
        active_modules = [{"number": number, "label": label} for number, label in SIMPLE_MODULES]
        out_dir = output_dir / f"{safe_name(product_dir.name)}_详情页" if output_dir else product_dir / OUTPUT_DIR_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        products.append(
            {
                "product_name": product_dir.name,
                "source_dir": str(product_dir),
                "valid_image_count": len(valid_images),
                "valid_images": valid_images,
                "info_files": [str(path) for path in collect_info_files(product_dir)],
                "active_module_count": len(active_modules),
                "suggested_modules": active_modules,
                "output_dir": str(out_dir),
                "planned_outputs": legacy_outputs(out_dir, args.output_format, args.export_modules, active_modules),
            }
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": "simple",
                "input_dir": str(input_dir),
                "product_count": len(products),
                "products": products,
                "skipped_file_count": len(skipped_files),
                "skipped_files": skipped_files,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def legacy_outputs(output_dir: Path, output_format: str, export_modules: bool, modules: list[dict[str, Any]]) -> list[dict[str, str]]:
    ext = "jpg" if output_format == "jpeg" else output_format
    outputs = list(REQUIRED_OUTPUTS)
    if export_modules:
        outputs.extend((module["number"], module["label"]) for module in modules)
    return [{"number": number, "label": label, "path": str(output_dir / f"{number}_{label}.{ext}")} for number, label in outputs]


def find_module_folder(material_root: Path, expected_folder_name: str) -> Path | None:
    exact = material_root / expected_folder_name
    if exact.exists() and exact.is_dir():
        return exact
    expected_number = expected_folder_name.split("_", 1)[0]
    if not material_root.exists():
        return None
    for child in material_root.iterdir():
        if child.is_dir() and child.name.startswith(f"{expected_number}_"):
            return child
    return None


def advanced_groups(input_dir: Path) -> list[Path]:
    if (input_dir / MATERIAL_ROOT_NAME).exists():
        return [input_dir]
    return [path for path in product_dirs(input_dir) if (path / MATERIAL_ROOT_NAME).exists()]


def run_advanced(args: argparse.Namespace, input_dir: Path, output_dir: Path | None) -> int:
    products: list[dict[str, Any]] = []
    for product_dir in advanced_groups(input_dir):
        active_modules: list[dict[str, Any]] = []
        skipped_modules: list[dict[str, Any]] = []
        material_root = product_dir / MATERIAL_ROOT_NAME
        for number, label, folder_name in ADVANCED_MODULE_OUTPUTS:
            module_dir = find_module_folder(material_root, folder_name)
            if not module_dir:
                skipped_modules.append({"number": number, "label": label, "status": "missing_folder"})
                continue
            files = material_files(module_dir)
            if files:
                active_modules.append(
                    {
                        "number": number,
                        "label": label,
                        "material_folder": str(module_dir),
                        "material_count": len(files),
                        "image_count": len([path for path in files if path.suffix.lower() in SUPPORTED_EXTENSIONS]),
                        "material_files": [str(path) for path in files],
                    }
                )
            else:
                skipped_modules.append({"number": number, "label": label, "material_folder": str(module_dir), "status": "empty_folder"})
        if not active_modules:
            continue
        out_dir = output_dir / f"{safe_name(product_dir.name)}_详情页" if output_dir else product_dir / OUTPUT_DIR_NAME
        out_dir.mkdir(parents=True, exist_ok=True)
        products.append(
            {
                "product_name": product_dir.name,
                "source_dir": str(product_dir),
                "active_module_count": len(active_modules),
                "active_modules": active_modules,
                "skipped_modules": skipped_modules,
                "output_dir": str(out_dir),
                "planned_outputs": legacy_outputs(out_dir, args.output_format, True, active_modules),
            }
        )
    print(json.dumps({"status": "ok", "mode": "advanced", "input_dir": str(input_dir), "product_count": len(products), "products": products}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    if not input_dir.exists() or not input_dir.is_dir():
        print(json.dumps({"status": "blocked", "reason": "input folder does not exist", "input_dir": str(input_dir)}, ensure_ascii=False, indent=2))
        return 2

    if args.mode == "standard":
        return run_standard(args, input_dir)
    if args.mode == "advanced":
        return run_advanced(args, input_dir, output_dir)
    return run_simple(args, input_dir, output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
