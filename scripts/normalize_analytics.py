"""Normalize GitHub Readme Stats cards to identical dimensions for a clean 50/50 layout."""
from pathlib import Path
import copy
import re
import xml.etree.ElementTree as ET

TARGET_W = 495
TARGET_H = 240
OUTER_FILL = "#0D0718"
OUTER_STROKE = "#7C3AED"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def num(value):
    if value is None:
        return None
    m = re.search(r"[-+]?\d*\.?\d+", str(value))
    return float(m.group()) if m else None


def local(tag):
    return tag.rsplit("}", 1)[-1]


def dimensions(root):
    vb = root.get("viewBox")
    if vb:
        parts = re.split(r"[ ,]+", vb.strip())
        if len(parts) == 4:
            return float(parts[2]), float(parts[3])
    return num(root.get("width")) or TARGET_W, num(root.get("height")) or TARGET_H


def normalize(path: Path):
    tree = ET.parse(path)
    old = tree.getroot()
    old_w, old_h = dimensions(old)

    new = ET.Element(f"{{{NS}}}svg", {
        "xmlns": NS,
        "width": "100%",
        "height": str(TARGET_H),
        "viewBox": f"0 0 {TARGET_W} {TARGET_H}",
        "preserveAspectRatio": "xMidYMid meet",
    })

    # Keep definitions/styles that the generated card may depend on.
    for child in list(old):
        if local(child.tag) in {"defs", "style", "title", "desc"}:
            new.append(copy.deepcopy(child))

    # One identical outer card for both analytics blocks.
    bg = ET.SubElement(new, f"{{{NS}}}rect", {
        "x": "1", "y": "1", "width": str(TARGET_W - 2),
        "height": str(TARGET_H - 2), "rx": "10",
        "fill": OUTER_FILL, "stroke": OUTER_STROKE, "stroke-width": "2",
    })

    content = ET.SubElement(new, f"{{{NS}}}g")
    offset_y = max(0.0, (TARGET_H - old_h) / 2.0)
    content.set("transform", f"translate(0,{offset_y:.2f})")

    # Copy the original card's visible content, excluding its full-card background/border.
    for child in list(old):
        tag = local(child.tag)
        if tag in {"defs", "style", "title", "desc"}:
            continue
        if tag == "rect":
            w = num(child.get("width"))
            h = num(child.get("height"))
            x = num(child.get("x")) or 0
            y = num(child.get("y")) or 0
            if w is not None and h is not None and x <= 2 and y <= 2 and w >= old_w * 0.94 and h >= old_h * 0.88:
                continue
        content.append(copy.deepcopy(child))

    tree = ET.ElementTree(new)
    tree.write(path, encoding="utf-8", xml_declaration=False)


if __name__ == "__main__":
    for name in ("stats.svg", "top-langs.svg"):
        p = Path("profile") / name
        if p.exists():
            normalize(p)
            print(f"Normalized {p} -> {TARGET_W}x{TARGET_H}")
