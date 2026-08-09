from datetime import datetime, timezone
import json

import numpy as np
import pytest

from storage.damage_repository import DamageLocation, DamageRepository


def test_save_event_uses_server_payload_shape(tmp_path):
    repository = DamageRepository(tmp_path)
    event = repository.save_event(
        images=[np.zeros((2, 2, 3), dtype=np.uint8)],
        location=DamageLocation(latitude=12.4, longitude=8.7),
        robot_id=1,
        description="도로 균열 감지",
        captured_at=datetime(2026, 7, 28, 8, 30, 15, tzinfo=timezone.utc),
    )
    event_files = repository.list_pending_events()
    assert len(event_files) == 1
    assert len(list((tmp_path / "images").glob("*.jpg"))) == 1
    assert json.loads(event_files[0].read_text(encoding="utf-8")) == repository.to_dict(event)
    assert repository.to_dict(event) == {
        "eventId": event_files[0].stem,
        "robotId": 1,
        "description": "도로 균열 감지",
        "latitude": 12.4,
        "longitude": 8.7,
        "capturedAt": "2026-07-28T08:30:15",
        "images": [next((tmp_path / "images").glob("*.jpg")).name],
    }


def test_save_event_adds_optional_ai_metadata_without_changing_existing_fields(tmp_path):
    repository = DamageRepository(tmp_path)
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    event = repository.save_event(
        images=[image, image],
        location=DamageLocation(37.5, 127.0),
        metadata={"ai": {"roi_source": "tactile_block"}},
    )

    payload = repository.to_dict(event)

    assert payload["metadata"]["ai"]["roi_source"] == "tactile_block"
    assert payload["images"] == list(event.image_paths)


@pytest.mark.parametrize("robot_id", [0, -1])
def test_save_event_rejects_invalid_robot_id(tmp_path, robot_id):
    repository = DamageRepository(tmp_path)
    with pytest.raises(ValueError):
        repository.save_event(
            images=[np.zeros((2, 2, 3), dtype=np.uint8)],
            location=DamageLocation(latitude=12.4, longitude=8.7),
            robot_id=robot_id,
        )


def test_save_event_connects_up_to_three_images_with_same_event_id(tmp_path):
    repository = DamageRepository(tmp_path)
    repository.save_event(
        images=[
            np.full((2, 2, 3), fill_value=value, dtype=np.uint8)
            for value in (10, 20, 30)
        ],
        location=DamageLocation(latitude=12.4, longitude=8.7),
    )
    event_file = repository.list_pending_events()[0]
    image_files = sorted((tmp_path / "images").glob("*.jpg"))
    event_id = event_file.stem
    assert [path.name for path in image_files] == [
        f"{event_id}_01.jpg",
        f"{event_id}_02.jpg",
        f"{event_id}_03.jpg",
    ]


def test_save_event_selects_only_original_for_upload(tmp_path):
    repository = DamageRepository(tmp_path)
    event = repository.save_event(
        images=[
            np.full((2, 2, 3), fill_value=10, dtype=np.uint8),
            np.full((2, 2, 3), fill_value=20, dtype=np.uint8),
        ],
        upload_image_indices=[0],
        location=DamageLocation(latitude=12.4, longitude=8.7),
    )
    payload = repository.to_dict(event)

    assert len(repository.resolve_image_paths(payload)) == 2
    assert repository.resolve_upload_image_paths(payload) == [
        repository.resolve_image_paths(payload)[0]
    ]
    assert payload["uploadImages"] == [event.image_paths[0]]


def test_save_event_can_select_tactile_roi_for_upload(tmp_path):
    repository = DamageRepository(tmp_path)
    event = repository.save_event(
        images=[
            np.full((2, 2, 3), fill_value=10, dtype=np.uint8),
            np.full((2, 2, 3), fill_value=20, dtype=np.uint8),
        ],
        upload_image_indices=[1],
        location=DamageLocation(latitude=12.4, longitude=8.7),
    )
    payload = repository.to_dict(event)

    assert payload["uploadImages"] == [event.image_paths[1]]
    assert repository.resolve_upload_image_paths(payload) == [
        repository.resolve_image_paths(payload)[1]
    ]


def test_legacy_event_uploads_first_stored_image_as_original(tmp_path):
    repository = DamageRepository(tmp_path)
    event = repository.save_event(
        images=[
            np.full((2, 2, 3), fill_value=10, dtype=np.uint8),
            np.full((2, 2, 3), fill_value=20, dtype=np.uint8),
        ],
        location=DamageLocation(latitude=12.4, longitude=8.7),
    )
    payload = repository.to_dict(event)

    assert "uploadImages" not in payload
    assert repository.resolve_upload_image_paths(payload) == [
        repository.resolve_image_paths(payload)[0]
    ]


def test_save_event_rejects_more_than_three_images(tmp_path):
    repository = DamageRepository(tmp_path)
    with pytest.raises(ValueError, match="between 1 and 3"):
        repository.save_event(
            images=[np.zeros((2, 2, 3), dtype=np.uint8) for _ in range(4)],
            location=DamageLocation(latitude=12.4, longitude=8.7),
        )


def test_delete_event_removes_json_and_all_connected_images(tmp_path):
    repository = DamageRepository(tmp_path)
    repository.save_event(
        images=[
            np.full((2, 2, 3), fill_value=value, dtype=np.uint8)
            for value in (10, 20, 30)
        ],
        location=DamageLocation(latitude=12.4, longitude=8.7),
    )
    event_path = repository.list_pending_events()[0]
    event = repository.load_event_file(event_path)
    image_paths = repository.resolve_image_paths(event)
    repository.delete_event(event_path)
    assert not event_path.exists()
    assert all(not path.exists() for path in image_paths)
    assert repository.list_pending_events() == []
