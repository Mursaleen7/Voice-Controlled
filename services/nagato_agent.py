from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from services.computer_control import ComputerControl, OpenAppRequest, VolumeRequest, ScreenshotRequest, TypeTextRequest
from openai import OpenAI
import os
import json
import random

# Import the TTS service
from services.tts import tts_service

class CommandType(Enum):
    OPEN_APP = "open_app"
    VOLUME = "volume"
    SCREENSHOT = "screenshot"
    TYPE_TEXT = "type_text"
    CONVERSATION = "conversation"

class Command(BaseModel):
    type: CommandType
    content: dict

class NagatoResponse(BaseModel):
    message: str
    action_taken: Optional[str] = None
    success: bool = True
    voice_feedback: Optional[str] = None  # Added field for voice feedback

class NagatoAgent:
    def __init__(self):
        self.computer = ComputerControl()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Check if TTS is enabled
        self.tts_enabled = os.getenv('TTS_ENABLED', 'true').lower() == 'true'
        
        # Add conversational response variations
        self.open_app_responses = [
            "Got it! {}",
            "Sure thing! {}",
            "On it! {}",
            "No problem! {}"
        ]
        
        self.volume_responses = [
            "All set! {}",
            "Done! {}",
            "There you go! {}",
            "Got it! {}"
        ]
        
        self.screenshot_responses = [
            "Captured! {}",
            "Got that! {}",
            "Snap! {}",
            "Done! {}"
        ]
        
        self.type_text_responses = [
            "Just did that for you!",
            "All typed up!",
            "Done and done!",
            "Taken care of!"
        ]
        
        self.error_responses = [
            "Oops! Something went wrong: {}",
            "That didn't work: {}",
            "I ran into a problem: {}",
            "Sorry about that: {}"
        ]
        
    def process_command(self, text: str) -> NagatoResponse:
        """Process natural language command and execute appropriate action"""
        try:
            # Use LLM to parse the command and determine intent
            parsed = self.parse_command(text)
            
            if parsed.type == CommandType.OPEN_APP:
                request = OpenAppRequest(**parsed.content)
                result = self.computer.open_application(request.app_name)
                
                # Create conversational response message
                message = random.choice(self.open_app_responses).format(result)
                action = f"Opened {request.app_name}"
                
                # Use the exact feedback text
                if self.tts_enabled:
                    feedback_text = f"{message} {action}"
                    tts_service.say(feedback_text)
                    
                return NagatoResponse(
                    message=message,
                    action_taken=action,
                    success=True,
                    voice_feedback=feedback_text if self.tts_enabled else None
                )
                
            elif parsed.type == CommandType.VOLUME:
                request = VolumeRequest(**parsed.content)
                result = self.computer.adjust_volume(request.level)
                
                # Create conversational response message
                message = random.choice(self.volume_responses).format(result)
                action = f"Volume set to {request.level}%"
                
                # Use the exact feedback text
                if self.tts_enabled:
                    feedback_text = f"{message} {action}"
                    tts_service.say(feedback_text)
                
                return NagatoResponse(
                    message=message,
                    action_taken=action,
                    success=True,
                    voice_feedback=feedback_text if self.tts_enabled else None
                )
                
            elif parsed.type == CommandType.SCREENSHOT:
                request = ScreenshotRequest(**parsed.content)
                result = self.computer.take_screenshot(request.filename)
                
                # Create conversational response message
                message = random.choice(self.screenshot_responses).format(result)
                action = "Screenshot saved"
                
                # Use the exact feedback text
                if self.tts_enabled:
                    feedback_text = f"{message} {action}"
                    tts_service.say(feedback_text)
                
                return NagatoResponse(
                    message=message,
                    action_taken=action,
                    success=True,
                    voice_feedback=feedback_text if self.tts_enabled else None
                )
                
            elif parsed.type == CommandType.TYPE_TEXT:
                request = TypeTextRequest(**parsed.content)
                # Check if this is browser-related for automatic focus
                browsers = ['safari', 'chrome', 'firefox', 'edge', 'opera', 'brave']
                
                # Auto-detect if this is likely a search query
                is_search_query = any(term in text.lower() for term in ['search', 'look up', 'find', 'google', 'what', 'how', 'when', 'where', 'who', 'why'])
                
                # Set focus_browser parameter if provided or if this looks like a search query
                focus_browser = request.focus_browser or is_search_query
                
                result = self.computer.type_text(request.text, request.delay, focus_browser)
                action_message = "Searched for" if focus_browser else "Typed"
                
                # Create conversational response message
                message = random.choice(self.type_text_responses)
                action = f"{action_message}: {request.text}"
                
                # Use the exact feedback text
                if self.tts_enabled:
                    feedback_text = f"{message} {action}"
                    tts_service.say(feedback_text)
                
                return NagatoResponse(
                    message=message,
                    action_taken=action,
                    success=True,
                    voice_feedback=feedback_text if self.tts_enabled else None
                )
                
            else:
                # Create conversational response for fallback
                message = "I'm not quite sure how to help with that yet."
                
                # Use the exact feedback text
                if self.tts_enabled:
                    tts_service.say(message)
                
                return NagatoResponse(
                    message=message,
                    success=False,
                    voice_feedback=message if self.tts_enabled else None
                )
                
        except Exception as e:
            # Create error message with variation
            error_message = random.choice(self.error_responses).format(str(e))
            
            # Use the exact feedback text
            if self.tts_enabled:
                tts_service.say(error_message)
                
            return NagatoResponse(
                message=error_message,
                success=False,
                voice_feedback=error_message if self.tts_enabled else None
            )

    def parse_command(self, text: str) -> Command:
        """Use LLM to parse the command and determine the intent"""
        
        function_descriptions = {
            "functions": [
                {
                    "name": "open_application",
                    "description": "Open an application on the computer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application to open"
                            }
                        },
                        "required": ["app_name"]
                    }
                },
                {
                    "name": "adjust_volume",
                    "description": "Adjust the system volume",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "integer",
                                "description": "Volume level (0-100)",
                                "minimum": 0,
                                "maximum": 100
                            }
                        },
                        "required": ["level"]
                    }
                },
                {
                    "name": "take_screenshot",
                    "description": "Take a screenshot of the screen",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Optional filename for the screenshot"
                            }
                        }
                    }
                },
                {
                    "name": "type_text",
                    "description": "Type text into the current application",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to type"
                            },
                            "delay": {
                                "type": "number",
                                "description": "Delay between keystrokes (seconds)",
                                "default": 0.05
                            },
                            "focus_browser": {
                                "type": "boolean",
                                "description": "Whether to focus the browser's address/search bar before typing",
                                "default": False
                            }
                        },
                        "required": ["text"]
                    }
                }
            ]
        }

        try:
            # Ask LLM to understand the command
            response = self.client.chat.completions.create(
                model=os.getenv('LLM_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": """You are a command parser for a computer control system. 
                    Analyze user commands and map them to the appropriate function call. 
                    For volume commands, understand relative terms (louder/quieter) and convert them to appropriate levels.
                    
                    For typing commands:
                    - If a command mentions typing something or entering text, use the type_text function.
                    - If a command mentions searching or looking up info, use type_text with focus_browser=true.
                    - If a command contains search terms like "what", "how", "when", etc., use type_text with focus_browser=true.
                    
                    For compound commands (e.g. "open <app> and type <text>"), only parse the first part of the command.
                    Respond only with the function call, no other text."""},
                    {"role": "user", "content": text}
                ],
                functions=function_descriptions["functions"],
                function_call="auto"
            )

            # Extract the function call
            if response.choices[0].message.function_call:
                func_name = response.choices[0].message.function_call.name
                func_args = json.loads(response.choices[0].message.function_call.arguments)

                # Map to appropriate command type
                if func_name == "open_application":
                    return Command(
                        type=CommandType.OPEN_APP,
                        content={"app_name": func_args["app_name"]}
                    )
                elif func_name == "adjust_volume":
                    return Command(
                        type=CommandType.VOLUME,
                        content={"level": func_args["level"]}
                    )
                elif func_name == "take_screenshot":
                    return Command(
                        type=CommandType.SCREENSHOT,
                        content={"filename": func_args.get("filename")}
                    )
                elif func_name == "type_text":
                    return Command(
                        type=CommandType.TYPE_TEXT,
                        content={
                            "text": func_args["text"],
                            "delay": func_args.get("delay", 0.05),
                            "focus_browser": func_args.get("focus_browser", False)
                        }
                    )

            return Command(
                type=CommandType.CONVERSATION,
                content={}
            )

        except Exception as e:
            print(f"Error parsing command: {str(e)}")
            return Command(
                type=CommandType.CONVERSATION,
                content={}
            )

# Create singleton instance
nagato_agent = NagatoAgent() 