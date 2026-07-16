"""AI Hub 513 라벨 아카이브에서 점자블록 레코드를 점검한다.

바깥 ZIP 안의 TL*.zip을 메모리에서 순차적으로 열어 원본을 풀지 않고 처리한다.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


KEYWORDS = ("점자블럭", "점자블록")


def is_target(path: str, record: dict) -> bool:
    labels = " ".join(str(a.get("label_name", "")) for a in record.get("annotations", []))
    return any(keyword in f"{path} {labels}" for keyword in KEYWORDS)


def inspect(archive: Path, output_dir: Path) -> dict:
    counters = {
        "defect": Counter(),
        "annotation_type": Counter(),
        "label_name": Counter(),
        "image_size": Counter(),
        "city_id": Counter(),
        "date": Counter(),
    }
    errors: list[dict] = []
    rows: list[dict] = []
    seen_image_ids: Counter[str] = Counter()
    seen_filenames: Counter[str] = Counter()
    scanned_json = 0
    inner_zip_count = 0

    with zipfile.ZipFile(archive) as outer:
        inner_names = sorted(name for name in outer.namelist() if name.lower().endswith(".zip"))
        for inner_name in inner_names:
            inner_zip_count += 1
            try:
                with zipfile.ZipFile(io.BytesIO(outer.read(inner_name))) as inner:
                    for json_name in inner.namelist():
                        if not json_name.lower().endswith(".json"):
                            continue
                        scanned_json += 1
                        try:
                            record = json.loads(inner.read(json_name))
                        except Exception as exc:  # 손상 레코드를 남기고 계속 진행
                            errors.append({"archive": inner_name, "path": json_name, "error": str(exc)})
                            continue
                        if not is_target(json_name, record):
                            continue

                        info = record.get("info", {})
                        description = record.get("description", {})
                        annotations = record.get("annotations", [])
                        image_id = str(info.get("image_id", ""))
                        filename = str(info.get("filename", ""))
                        width = info.get("width", 0)
                        height = info.get("height", 0)
                        seen_image_ids[image_id] += 1
                        seen_filenames[filename] += 1
                        counters["image_size"][f"{width}x{height}"] += 1
                        counters["city_id"][str(info.get("city_id", ""))] += 1
                        counters["date"][str(info.get("date", ""))] += 1

                        defect_values = []
                        annotation_types = []
                        for annotation in annotations:
                            defect = str(annotation.get("is_defect", "unknown"))
                            annotation_type = str(annotation.get("annotation_type", "unknown"))
                            label_name = str(annotation.get("label_name", "unknown"))
                            counters["defect"][defect] += 1
                            counters["annotation_type"][annotation_type] += 1
                            counters["label_name"][label_name] += 1
                            defect_values.append(defect)
                            annotation_types.append(annotation_type)

                        rows.append(
                            {
                                "inner_archive": inner_name,
                                "json_path": json_name,
                                "image_id": image_id,
                                "filename": filename,
                                "date": info.get("date", ""),
                                "city_id": info.get("city_id", ""),
                                "width": width,
                                "height": height,
                                "facility": description.get("facility", ""),
                                "state": description.get("state", ""),
                                "defect": "|".join(sorted(set(defect_values))),
                                "annotation_type": "|".join(sorted(set(annotation_types))),
                                "annotation_count": len(annotations),
                            }
                        )
            except (zipfile.BadZipFile, OSError) as exc:
                errors.append({"archive": inner_name, "path": "", "error": str(exc)})

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "tactile_manifest.csv"
    if rows:
        with manifest_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    profile = {
        "source_archive": str(archive),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inner_zip_count": inner_zip_count,
        "scanned_json_count": scanned_json,
        "target_image_count": len(rows),
        "duplicate_image_id_count": sum(1 for k, v in seen_image_ids.items() if k and v > 1),
        "duplicate_filename_count": sum(1 for k, v in seen_filenames.items() if k and v > 1),
        "parse_error_count": len(errors),
        "counters": {name: dict(counter.most_common()) for name, counter in counters.items()},
        "errors_sample": errors[:100],
    }
    (output_dir / "dataset_profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(profile, output_dir / "dataset_profile.md")
    return profile


def write_markdown(profile: dict, path: Path) -> None:
    counters = profile["counters"]
    lines = [
        "# AI Hub 점자블록 라벨 프로파일",
        "",
        f"- 내부 라벨 ZIP: {profile['inner_zip_count']:,}개",
        f"- 검사한 JSON: {profile['scanned_json_count']:,}개",
        f"- 선별한 점자블록 이미지: {profile['target_image_count']:,}개",
        f"- JSON 파싱 오류: {profile['parse_error_count']:,}개",
        f"- 중복 image_id: {profile['duplicate_image_id_count']:,}개",
        f"- 중복 filename: {profile['duplicate_filename_count']:,}개",
        "",
        "## 파손 상태(annotation 기준)",
        "",
    ]
    lines.extend(f"- {key}: {value:,}개" for key, value in counters["defect"].items())
    lines.extend(["", "## Annotation 종류", ""])
    lines.extend(f"- {key}: {value:,}개" for key, value in counters["annotation_type"].items())
    lines.extend(["", "## 주요 이미지 크기", ""])
    lines.extend(f"- {key}: {value:,}장" for key, value in list(counters["image_size"].items())[:10])
    lines.extend(
        [
            "",
            "> 이 결과는 라벨 배포 ZIP을 기준으로 한 1차 구조·분포 점검이다. 원천 이미지와의 짝 검증은 별도로 수행해야 한다.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True, help="AI Hub 라벨 배포 ZIP")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    profile = inspect(args.archive, args.output_dir)
    print(json.dumps({k: profile[k] for k in (
        "inner_zip_count", "scanned_json_count", "target_image_count", "parse_error_count"
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
