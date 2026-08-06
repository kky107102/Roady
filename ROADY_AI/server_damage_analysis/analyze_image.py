from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2

from .analyzer import ServerDamageAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser(description="ROADY 서버 파손 분석")
    parser.add_argument("--model", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--imgsz", type=int, default=1024)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    analyzer = ServerDamageAnalyzer(args.model)
    payload, overlay, damage_mask = analyzer.predict(
        args.image, imgsz=args.imgsz, device=args.device
    )
    original_name = Path(args.image).name
    overlay_name = f"{Path(args.image).stem}_analysis.jpg"
    mask_name = f"{Path(args.image).stem}_damage_mask.png"
    payload["artifacts"] = {
        "original_image": original_name,
        "overlay_image": overlay_name,
        "mask_image": mask_name,
    }
    shutil.copy2(args.image, output / original_name)
    cv2.imwrite(str(output / overlay_name), overlay)
    cv2.imwrite(str(output / mask_name), damage_mask.astype("uint8") * 255)
    (output / "analysis.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(output / "analysis.json")


if __name__ == "__main__":
    main()
