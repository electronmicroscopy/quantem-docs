"""Splice Colin's clean, hand-drawn diffraction pattern into the logo source.

Colin redrew the diffraction pattern by itself and exported it as a
diffraction-only PDF on the same logos_53 artboard, so every dot already sits
in the logo's coordinate frame (viewBox 0 0 460.8 266.4). We keep the pristine
EELS / structure / tomography / wordmark artwork and swap in these exact dots,
tagged data-qem="dif" so the classifier trusts them verbatim. The build then
draws each dot as-is and animates it by a uniform scale about its own centre;
no ellipse fitting, no resizing.

    python scripts/merge_diffraction_only.py

Inputs
    assets/src/logo53_exact.svg            base artwork (dif dropped, rest kept)
    assets/src/logo_diffraction_only.svg   clean diffraction, exact coordinates
Output
    assets/src/logo53_exact.svg            rewritten in place
"""

import os
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "assets", "src"))
BASE = os.path.join(SRC, "logo53_exact.svg")
DIF = os.path.join(SRC, "logo_diffraction_only.svg")


def main():
    tree = ET.parse(BASE)
    root = tree.getroot()

    # drop the previous diffraction (all tagged), keep everything else
    dropped = 0
    for el in [e for e in root if e.get("data-qem") == "dif"]:
        root.remove(el)
        dropped += 1
    print(f"dropped previous diffraction paths: {dropped}")

    # append the clean dots verbatim, tagged so classify() trusts them
    dtree = ET.parse(DIF)
    added = 0
    for el in dtree.getroot().iter(f"{{{SVG}}}path"):
        new = ET.SubElement(root, f"{{{SVG}}}path")
        new.set("fill", el.get("fill"))
        new.set("d", el.get("d"))
        new.set("data-qem", "dif")
        added += 1
    print(f"added clean diffraction paths: {added}")

    tree.write(BASE, encoding="unicode", xml_declaration=True)
    print(f"wrote {os.path.relpath(BASE)}")


if __name__ == "__main__":
    main()
