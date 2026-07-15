import re
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = ROOT_DIR / "skills"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str
    path: Path
    instructions: str
    display_name: str = ""
    default_prompt: str = ""

    def read_resource(self, relative_path):
        resource = (self.path / relative_path).resolve()
        if self.path.resolve() not in resource.parents or not resource.is_file():
            raise ValueError(f"Skill resource is not allowed: {relative_path}")
        return resource.read_text(encoding="utf-8")


@dataclass
class RouteDecision:
    skill_name: str
    mode: str = "auto"
    confidence: float = 0.0
    input_roles: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def needs_input(self):
        return self.confidence < 0.75 or bool(self.missing_inputs)

    def to_dict(self):
        return {
            "skill_name": self.skill_name,
            "mode": self.mode,
            "confidence": round(float(self.confidence), 3),
            "input_roles": list(self.input_roles),
            "missing_inputs": list(self.missing_inputs),
            "reason": self.reason,
            "status": "needs_input" if self.needs_input else "ready",
        }


def _frontmatter(text):
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter.")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("SKILL.md frontmatter is not closed.")
    metadata = {}
    lines = parts[1].splitlines()
    current_key = None
    continuation = []
    for raw in lines:
        if raw.startswith((" ", "\t")) and current_key:
            value = raw.strip()
            if value:
                continuation.append(value)
            continue
        if current_key and continuation:
            metadata[current_key] = " ".join(continuation)
            continuation = []
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        current_key = key.strip()
        value = value.strip().strip("'\"")
        if value in {">", ">-", "|", "|-"}:
            metadata[current_key] = ""
        else:
            metadata[current_key] = value
    if current_key and continuation:
        metadata[current_key] = " ".join(continuation)
    return metadata


def _openai_metadata(skill_dir):
    path = skill_dir / "agents" / "openai.yaml"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    result = {}
    for key in ("display_name", "short_description", "default_prompt"):
        match = re.search(rf"^\s*{key}:\s*[\"']?(.*?)[\"']?\s*$", text, re.MULTILINE)
        if match:
            result[key] = match.group(1).strip().strip("'\"")
    return result


class SkillRegistry:
    def __init__(self, root=SKILLS_DIR):
        self.root = Path(root).resolve()
        self.skills = {}
        self.errors = []
        self._discover()

    def _discover(self):
        if not self.root.is_dir():
            return
        for skill_file in sorted(self.root.rglob("SKILL.md")):
            try:
                text = skill_file.read_text(encoding="utf-8")
                meta = _frontmatter(text)
                name = str(meta.get("name") or "").strip()
                description = str(meta.get("description") or "").strip()
                if not name or not description:
                    raise ValueError("name and description are required.")
                if name in self.skills:
                    raise ValueError(f"Duplicate skill name: {name}")
                agent_meta = _openai_metadata(skill_file.parent)
                self.skills[name] = SkillDefinition(
                    name=name,
                    description=description,
                    path=skill_file.parent.resolve(),
                    instructions=text,
                    display_name=agent_meta.get("display_name", name),
                    default_prompt=agent_meta.get("default_prompt", ""),
                )
            except (OSError, UnicodeError, ValueError) as exc:
                self.errors.append({"path": str(skill_file), "error": str(exc)})

    def names(self):
        return sorted(self.skills)

    def get(self, name):
        try:
            return self.skills[name]
        except KeyError as exc:
            raise ValueError(f"Unknown skill: {name}") from exc

    def catalog(self):
        return [
            {"name": skill.name, "description": skill.description}
            for skill in sorted(self.skills.values(), key=lambda item: item.name)
        ]


_ROUTE_RULES = [
    ("batch-apparel-detail-pages", ("详情页", "详情模板", "detail page")),
    ("batch-ai-tryon", ("换装", "试衣", "try-on", "try on")),
    ("batch-clothing-white-bg-images", ("白底", "去模特", "平铺图", "挂拍", "white background")),
    ("batch-clothing-product-images", ("商品主图", "电商主图", "批量主图", "product image")),
    ("print-pattern-derivation", ("印花", "花型", "纹样", "pattern derivation")),
    ("hot-style-analyzer", ("爆款分析", "爆款基因", "hot style")),
    ("world-buyer", ("买手", "找款", "货盘", "world buyer")),
    ("fashion-design-analysis", ("服装设计", "设计总监", "款式图", "设计拆解")),
    ("clothing-display-image-to-image", ("陈列", "橱窗", "showroom", "visual merchandising")),
    ("outfit-flatlay-stylist", ("搭配", "穿搭", "flatlay", "flat lay")),
]


_VISUAL_REQUIRED = {
    "batch-apparel-detail-pages",
    "batch-ai-tryon",
    "batch-clothing-white-bg-images",
    "batch-clothing-product-images",
    "clothing-display-image-to-image",
    "hot-style-analyzer",
    "outfit-flatlay-stylist",
    "print-pattern-derivation",
}


def _print_mode(prompt):
    normalized = prompt.lower()
    mapping = [
        ("全套", "1-7-full-set"),
        ("全部", "1-7-full-set"),
        ("小碎花", "3-small-dense"),
        ("大花", "4-large-negative-space"),
        ("新色", "2-new-colorway"),
        ("换色", "2-new-colorway"),
        ("几何", "5-geometric-companion"),
        ("伴生", "5-geometric-companion"),
        ("季节", "6-seasonal-trend"),
        ("趋势", "6-seasonal-trend"),
        ("总览", "7-family-overview"),
    ]
    for token, mode in mapping:
        if token in normalized:
            return mode
    number = re.search(r"(?:模式|方向|编号)?\s*([1-7])(?:\D|$)", normalized)
    if number:
        return f"{number.group(1)}-selected"
    return "1-gene-extension"


def route_with_rules(registry, prompt, skill_override="auto", image_count=0, input_path=""):
    prompt = str(prompt or "").strip()
    if skill_override and skill_override != "auto":
        registry.get(skill_override)
        selected = skill_override
        confidence = 1.0
        reason = "User selected skill_override."
    else:
        normalized = prompt.lower()
        selected = ""
        for name, tokens in _ROUTE_RULES:
            if name in registry.skills and any(token.lower() in normalized for token in tokens):
                selected = name
                break
        confidence = 0.95 if selected else 0.0
        reason = "Matched explicit task keywords." if selected else "No deterministic skill match."

    mode = _print_mode(prompt) if selected == "print-pattern-derivation" else "auto"
    roles = []
    if image_count:
        roles.append(f"comfyui_image_batch:{image_count}")
    if input_path:
        roles.append("input_path")
    missing = []
    if selected in _VISUAL_REQUIRED and not image_count and not input_path:
        missing.append("请提供 IMAGE 输入，或在 input_path 中指定包含参考图片的路径。")
    return RouteDecision(selected, mode, confidence, roles, missing, reason)
