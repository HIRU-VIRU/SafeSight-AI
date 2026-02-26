"""
Alert management system for SafeSight AI.
Handles violation alerts via console, sound, and webhooks.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import requests
from config.settings import (
    ENABLE_SOUND_ALERT, 
    ALERT_WEBHOOK_URL,
    CAMERA_ID
)


class AlertManager:
    """
    Manages violation alerts through multiple channels.
    Supports console output, optional sound alerts, and webhook notifications.
    """
    
    def __init__(self, 
                 enable_sound: bool = ENABLE_SOUND_ALERT,
                 webhook_url: Optional[str] = ALERT_WEBHOOK_URL):
        """
        Initialize alert manager.
        
        Args:
            enable_sound: Enable sound alerts
            webhook_url: Optional webhook URL for external notifications
        """
        self.enable_sound = enable_sound
        self.webhook_url = webhook_url
        
        if self.enable_sound:
            try:
                # Try to import sound library
                import winsound  # Windows
                self.sound_module = winsound
                self.sound_available = True
            except ImportError:
                try:
                    import os
                    if os.system("which aplay > /dev/null 2>&1") == 0:
                        # Linux with alsa-utils
                        self.sound_available = True
                        self.sound_module = None
                    else:
                        self.sound_available = False
                        print("⚠️  Sound alerts not available (install alsa-utils)")
                except:
                    self.sound_available = False
                    print("⚠️  Sound alerts not available")
        else:
            self.sound_available = False
    
    def send_alert(self, violation: Dict[str, Any], camera_id: str = CAMERA_ID):
        """
        Send violation alert through all configured channels.
        
        Args:
            violation: Violation dictionary with person_id and violations list
            camera_id: Camera identifier
        """
        # Console alert
        self._console_alert(violation, camera_id)
        
        # Sound alert
        if self.enable_sound and self.sound_available:
            self._sound_alert()
        
        # Webhook alert
        if self.webhook_url:
            self._webhook_alert(violation, camera_id)
    
    def _console_alert(self, violation: Dict[str, Any], camera_id: str):
        """
        Print formatted alert to console.
        
        Format:
        ⚠ PPE VIOLATION DETECTED
        Camera: Gate_01
        Time: 15:34:22
        Person ID: 3
        Violations: helmet, boots
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        violations_text = ", ".join(violation.get("violations", []))
        severity = violation.get("severity", "WARNING")
        icon = "🚨" if severity == "CRITICAL" else "⚠️"
        
        alert_message = f"""
{'='*50}
{icon}  PPE VIOLATION – {severity}
{'='*50}
Camera: {camera_id}
Time: {timestamp}
Person ID: {violation['person_id']}
Severity: {severity}
Violations: {violations_text}
{'='*50}
"""
        print(alert_message)
    
    def _sound_alert(self):
        """Play alert sound."""
        try:
            if self.sound_module:
                # Windows
                import winsound
                winsound.Beep(1000, 200)  # 1000 Hz for 200ms
            else:
                # Linux - use beep command via speaker-test
                import os
                os.system("speaker-test -t sine -f 1000 -l 1 > /dev/null 2>&1 &")
        except Exception as e:
            # Silently fail if sound not available
            pass
    
    def _webhook_alert(self, violation: Dict[str, Any], camera_id: str):
        """
        Send alert to webhook endpoint.
        
        Args:
            violation: Violation data
            camera_id: Camera identifier
        """
        try:
            timestamp = datetime.now().isoformat()
            
            payload = {
                "event": "ppe_violation",
                "camera_id": camera_id,
                "timestamp": timestamp,
                "person_id": violation["person_id"],
                "violations": violation.get("violations", []),
                "helmet_violation": violation.get("helmet_violation", False),
                "vest_violation": violation.get("vest_violation", False),
                "boots_violation": violation.get("boots_violation", False),
                "gloves_violation": violation.get("gloves_violation", False),
                "goggles_violation": violation.get("goggles_violation", False)
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Webhook alert sent successfully")
            else:
                print(f"⚠️  Webhook responded with status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Webhook timeout")
        except Exception as e:
            print(f"⚠️  Webhook error: {e}")
    
    def test_alert(self):
        """Test alert system with dummy data."""
        test_violation = {
            "person_id": 999,
            "violations": ["helmet", "vest"],
            "helmet_violation": True,
            "vest_violation": True,
            "boots_violation": False,
            "gloves_violation": False,
            "goggles_violation": False
        }
        
        print("\n🔔 Testing Alert System...")
        self.send_alert(test_violation, "TEST_CAMERA")
        print("✅ Alert test complete\n")
