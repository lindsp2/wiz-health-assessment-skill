"""
Local PowerPoint (.pptx) Template Processor for Wiz Health Assessment.
=======================================================================
Replaces template tokens {{VARIABLE}} across all slides in a .pptx presentation,
handles multiline bullet expansions, highlights enabled preview features in soft green,
cleans up empty date pairs, and sweeps unfilled tokens without requiring external Office APIs.
"""

import copy
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
}

# Register namespaces so ET doesn't mangle tags when writing back XML
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def process_pptx_template(
    template_path: str,
    output_path: str,
    variables: Dict[str, Any],
    enabled_preview_titles: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Process a master .pptx template:
    1. Replaces all {{KEY}} tokens with their corresponding values.
    2. Expands multiline variables into distinct paragraphs preserving typography.
    3. Cleans up empty PI date pairs (e.g. ' / ').
    4. Highlights enabled preview features on preview slides.
    5. Sweeps any remaining unfilled {{...}} tokens.
    """
    template_file = Path(template_path)
    if not template_file.is_file():
        raise FileNotFoundError(f"PPTX template not found at: {template_path}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Flatten variable values to string
    var_dict = {}
    for k, v in variables.items():
        if isinstance(v, dict) and "value" in v:
            var_dict[k] = str(v["value"] if v["value"] is not None else "")
        else:
            var_dict[k] = str(v if v is not None else "")

    # Pre-clean empty PI date pairs
    for prefix in ["PI_T1", "PI_T2", "PI_T3"]:
        for s in range(1, 9):
            fa_val = var_dict.get(f"{prefix}_{s}_FA", "")
            la_val = var_dict.get(f"{prefix}_{s}_LA", "")
            if not fa_val and not la_val:
                var_dict[f"{prefix}_{s}_FA"] = ""
                var_dict[f"{prefix}_{s}_LA"] = ""

    enabled_titles = {t.strip().lower() for t in (enabled_preview_titles or set())}
    replacements_made = 0
    highlighted_count = 0
    swept_tokens = 0

    with zipfile.ZipFile(template_file, "r") as zin, zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)

            if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
                root = ET.fromstring(content)
                slide_modified = False

                # Process all text bodies in shapes and table cells
                for txBody in root.findall(".//p:txBody", NS) + root.findall(".//a:txBody", NS):
                    paragraphs = list(txBody.findall("a:p", NS))
                    for p in paragraphs:
                        t_elems = p.findall(".//a:t", NS)
                        if not t_elems:
                            continue

                        full_text = "".join(t.text or "" for t in t_elems)
                        if "{{" not in full_text:
                            continue

                        # Check if this paragraph contains multiline tokens
                        replaced_text = full_text
                        has_multiline = False

                        for k, v in var_dict.items():
                            tok = "{{" + k + "}}"
                            if tok in replaced_text:
                                if "\n" in v:
                                    has_multiline = True
                                replaced_text = replaced_text.replace(tok, v)
                                replacements_made += 1

                        # Clean up empty date pair slashes
                        replaced_text = re.sub(r"\{\{[^}]+\}\}\s*/\s*\{\{[^}]+\}\}", "", replaced_text)
                        replaced_text = re.sub(r"\{\{[^}]+\s*/\s*[^}]+\}\}", "", replaced_text)

                        if replaced_text != full_text:
                            slide_modified = True
                            if has_multiline and "\n" in replaced_text:
                                # Multiline expansion: split into separate paragraphs
                                lines = [l for l in replaced_text.split("\n") if l.strip()]
                                p_index = list(txBody).index(p)
                                for i, line in enumerate(lines):
                                    p_clone = copy.deepcopy(p)
                                    clone_t_elems = p_clone.findall(".//a:t", NS)
                                    if clone_t_elems:
                                        clone_t_elems[0].text = line
                                        for other in clone_t_elems[1:]:
                                            other.text = ""

                                    # Check for soft green highlight
                                    clean_line_title = line.lstrip("• ").split(" [")[0].strip().lower()
                                    if clean_line_title and clean_line_title in enabled_titles:
                                        # Add highlight to rPr
                                        for r in p_clone.findall(".//a:r", NS):
                                            rPr = r.find("a:rPr", NS)
                                            if rPr is None:
                                                rPr = ET.SubElement(r, "{http://schemas.openxmlformats.org/drawingml/2006/main}rPr")
                                            # Add highlight element
                                            hl = rPr.find("a:highlight", NS)
                                            if hl is None:
                                                hl = ET.SubElement(rPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}highlight")
                                                srgb = ET.SubElement(hl, "{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                                                srgb.set("val", "E0F5E0")
                                                highlighted_count += 1

                                    txBody.insert(p_index + i, p_clone)
                                txBody.remove(p)
                            else:
                                t_elems[0].text = replaced_text
                                for other in t_elems[1:]:
                                    other.text = ""

                # Token sweep for remaining unpopulated tokens
                for t in root.findall(".//a:t", NS):
                    if t.text and "{{" in t.text:
                        swept_count_in_text = len(re.findall(r"\{\{[^}]+\}\}", t.text))
                        if swept_count_in_text > 0:
                            swept_tokens += swept_count_in_text
                            t.text = re.sub(r"\{\{[^}]+\}\}", "", t.text)
                            slide_modified = True

                if slide_modified:
                    content = ET.tostring(root, encoding="utf-8")

            zout.writestr(item, content)

    return {
        "output_path": str(output_file),
        "file_size": os.path.getsize(output_file),
        "replacements_made": replacements_made,
        "highlighted_count": highlighted_count,
        "swept_tokens": swept_tokens
    }
