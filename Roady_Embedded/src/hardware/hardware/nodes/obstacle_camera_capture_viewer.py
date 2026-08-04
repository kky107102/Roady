from __future__ import annotations

from hardware.nodes.wide_camera_capture_viewer import (
    CameraCaptureViewer,
    run_viewer,
)


class ObstacleCameraCaptureViewer(CameraCaptureViewer):
    def __init__(self) -> None:
        super().__init__(
            node_name="obstacle_camera_capture_viewer",
            default_topic="/camera/obstacle/image_raw",
            default_output_dir="~/roady_dataset/obstacle_lower_limb",
            filename_prefix="obstacle",
            window_name="ROADY obstacle-camera data capture",
        )


def main(args=None) -> None:
    run_viewer(ObstacleCameraCaptureViewer, args=args)


if __name__ == "__main__":
    main()
