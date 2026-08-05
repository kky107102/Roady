"""Backward-compatible entry point for the tactile camera node."""

from hardware.nodes.tactile_camera_node import TactileCameraNode, main

__all__ = ["TactileCameraNode", "main"]


if __name__ == "__main__":
    main()
