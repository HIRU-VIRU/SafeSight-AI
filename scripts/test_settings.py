"""Test settings loading."""
from config import settings

print("="*50)
print("SafeSight AI - Settings Test")
print("="*50)
print(f"CONF_THRESHOLD: {settings.CONF_THRESHOLD}")
print(f"IOU_THRESHOLD: {settings.IOU_THRESHOLD}")
print(f"MODEL_PATH: {settings.MODEL_PATH}")
print(f"CAMERA_ID: {settings.CAMERA_ID}")
print("="*50)
