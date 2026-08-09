"""Backward-compatible entry point; use damage_detection_node for new launches."""

from perception.nodes.damage_detection_node import DamageDetectionNode, main

MockDamageDetectionNode = DamageDetectionNode

__all__ = ["DamageDetectionNode", "MockDamageDetectionNode", "main"]
