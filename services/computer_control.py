import os
import subprocess
import time
from typing import Optional
from pydantic import BaseModel, Field
import pyautogui

class ComputerControl:
    def __init__(self):
        # List of common browsers for detection
        self.browsers = ['safari', 'chrome', 'firefox', 'edge', 'opera', 'brave']
    
    def open_application(self, app_name: str) -> str:
        """Open an application"""
        try:
            # Check if this is a browser
            is_browser = any(browser.lower() in app_name.lower() for browser in self.browsers)
            
            if os.name == 'posix':  # macOS/Linux
                subprocess.Popen(['open', '-a', app_name])
                # If it's a browser, give it a bit more time to open
                wait_time = 3 if is_browser else 1
                time.sleep(wait_time)
                return f"Opened {app_name}"
            elif os.name == 'nt':  # Windows
                subprocess.Popen(app_name)
                wait_time = 3 if is_browser else 1
                time.sleep(wait_time)
                return f"Opened {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"

    def open_new_browser_tab(self) -> str:
        """Open a new tab in the current browser"""
        try:
            # Wait to ensure browser is focused
            time.sleep(0.5)
            
            # Use keyboard shortcut to open new tab
            if os.name == 'posix':  # macOS
                pyautogui.hotkey('command', 't')  # Cmd+T for new tab on macOS
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 't')     # Ctrl+T for new tab
                
            time.sleep(0.3)  # Wait for the new tab to open
            return "Opened new browser tab"
        except Exception as e:
            return f"Failed to open new tab: {str(e)}"

    def adjust_volume(self, level: int) -> str:
        """Adjust system volume (0-100)"""
        try:
            if os.name == 'posix':  # macOS
                level = max(0, min(100, level))
                os.system(f"osascript -e 'set volume output volume {level}'")
                return f"Volume set to {level}%"
            # Add Windows implementation if needed
            return "Volume control not implemented for this OS"
        except Exception as e:
            return f"Failed to adjust volume: {str(e)}"

    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot"""
        try:
            if filename is None:
                # Create screenshots directory if it doesn't exist
                os.makedirs("screenshots", exist_ok=True)
                filename = f"screenshots/screenshot_{int(time.time())}.png"
            
            if os.name == 'posix':  # macOS
                os.system(f"screencapture '{filename}'")
                return f"Screenshot saved as {filename}"
            elif os.name == 'nt':  # Windows
                # Add Windows implementation using pyautogui or similar
                return "Screenshot not implemented for Windows yet"
            return "Screenshot not implemented for this OS"
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"
    
    def focus_browser_bar(self) -> str:
        """Focus the search/address bar in a browser"""
        try:
            # Wait to ensure the browser is ready
            time.sleep(0.5)
            
            # Use keyboard shortcut to focus address bar
            if os.name == 'posix':  # macOS
                pyautogui.hotkey('command', 'l')  # Cmd+L for address bar on macOS
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'l')     # Ctrl+L for address bar
                
            time.sleep(0.3)  # Wait for focus to complete
            return "Focused browser address bar"
        except Exception as e:
            return f"Failed to focus address bar: {str(e)}"
            
    def type_text(self, text: str, delay: float = 0.05, focus_browser: bool = False) -> str:
        """Type text into the currently active application"""
        try:
            # Add a small delay to ensure the application is focused
            time.sleep(0.5)
            
            # Focus browser address bar if requested
            if focus_browser:
                self.focus_browser_bar()
                
            # Type the text with a delay between characters for a more natural typing effect
            pyautogui.write(text, interval=delay)
            
            # If it looks like a search query, press Enter
            if focus_browser or any(term in text.lower() for term in ["search", "what", "how", "when", "where", "who", "why"]):
                time.sleep(0.2)
                pyautogui.press('return')
                
            return f"Typed the text: {text}"
        except Exception as e:
            return f"Failed to type text: {str(e)}"

# Create tools using Pydantic models
class OpenAppRequest(BaseModel):
    app_name: str = Field(..., description="Name of the application to open")

class VolumeRequest(BaseModel):
    level: int = Field(..., description="Volume level (0-100)", ge=0, le=100)

class ScreenshotRequest(BaseModel):
    filename: Optional[str] = Field(None, description="Optional filename for the screenshot")
    
class TypeTextRequest(BaseModel):
    text: str = Field(..., description="Text to type into the active application")
    delay: float = Field(0.05, description="Delay between keystrokes (seconds)")
    focus_browser: bool = Field(False, description="Whether to focus browser address bar before typing") 