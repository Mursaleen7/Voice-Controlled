import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Import TTS service
from services.tts import tts_service

load_dotenv()

class CommandProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('LLM_MODEL', 'gpt-4')
        self.browsers = ['safari', 'chrome', 'firefox', 'edge', 'opera', 'brave']
        # Check if TTS is enabled
        self.tts_enabled = os.getenv('TTS_ENABLED', 'true').lower() == 'true'

    def process_command(self, command_text):
        try:
            # Use Nagato agent to process the command
            from services.nagato_agent import nagato_agent
            
            # Check for browser-related and compound commands
            command_lower = command_text.lower()
            is_browser_command = any(browser in command_lower for browser in self.browsers)
            is_search_command = any(term in command_lower for term in ['search', 'look up', 'find', 'google'])
            
            # Check for compound commands like "open Safari and type what time is it in Ottawa"
            if ("open" in command_lower or "launch" in command_lower) and ("type" in command_lower or "search" in command_lower or "look up" in command_lower) and "and" in command_lower:
                # Parse the compound command
                compound_result = self._parse_compound_command(command_text)
                
                if compound_result:
                    app_name, text_to_type = compound_result
                    is_browser = any(browser in app_name.lower() for browser in self.browsers)
                    
                    # Create response message for opening app
                    opening_message = f"Opening {app_name}"
                    
                    # Audio feedback using exact message
                    if self.tts_enabled:
                        tts_service.say(opening_message)
                    
                    # First open the application
                    open_response = nagato_agent.process_command(f"open {app_name}")
                    
                    # For browsers, open a new tab first
                    if is_browser:
                        # Create new tab message
                        new_tab_message = f"Opening new tab in {app_name}"
                        
                        # Audio feedback using exact message
                        if self.tts_enabled:
                            tts_service.say(new_tab_message)
                            
                        # Open a new tab
                        nagato_agent.computer.open_new_browser_tab()
                        
                        # Create typing message
                        action_verb = "Searching for" if any(term in text_to_type.lower() for term in ["what", "how", "when", "where", "who", "why"]) else "Typing"
                        typing_message = f"{action_verb} {text_to_type}"
                        
                        # Audio feedback using exact message
                        if self.tts_enabled:
                            tts_service.say(typing_message)
                            
                        # Use modified command to ensure focus_browser=True
                        type_response = nagato_agent.computer.type_text(text_to_type, focus_browser=True)
                    else:
                        # Create typing message for non-browser
                        typing_message = f"Typing {text_to_type} in {app_name}"
                        
                        # Audio feedback using exact message
                        if self.tts_enabled:
                            tts_service.say(typing_message)
                            
                        # Regular typing for non-browser apps
                        type_response = nagato_agent.process_command(f"type {text_to_type}")
                    
                    # Final response message
                    final_response = f"{open_response.message} I opened a new tab and typed '{text_to_type}' for you."
                    
                    return final_response
            
            # Special handling for browser commands that don't explicitly mention "open"
            elif is_browser_command and (is_search_command or "go to" in command_lower or "visit" in command_lower or "open" in command_lower):
                # Extract the browser name
                browser_name = None
                for browser in self.browsers:
                    if browser in command_lower:
                        browser_name = browser.capitalize()
                        break
                
                if browser_name:
                    # Create opening browser message
                    opening_message = f"Opening {browser_name}"
                    
                    # Audio feedback using exact message
                    if self.tts_enabled:
                        tts_service.say(opening_message)
                        
                    # Open the browser
                    open_response = nagato_agent.process_command(f"open {browser_name}")
                    
                    # Create new tab message
                    new_tab_message = f"Opening new tab in {browser_name}"
                    
                    # Audio feedback using exact message
                    if self.tts_enabled:
                        tts_service.say(new_tab_message)
                        
                    # Open a new tab
                    nagato_agent.computer.open_new_browser_tab()
                    
                    # If there's a search or URL, focus and type it
                    search_terms = ["search", "look up", "find", "google", "what", "how", "when", "where", "who", "why"]
                    if any(term in command_lower for term in search_terms) or "go to" in command_lower or "visit" in command_lower:
                        # Extract the search query or URL
                        query = self._extract_search_or_url(command_text, browser_name)
                        if query:
                            # Create search message
                            search_message = f"Searching for {query}"
                            
                            # Audio feedback using exact message
                            if self.tts_enabled:
                                tts_service.say(search_message)
                                
                            type_response = nagato_agent.computer.type_text(query, focus_browser=True)
                            
                            # Final response message
                            final_response = f"{open_response.message} I opened a new tab and searched for '{query}'."
                            return final_response
                    
                    # Final response message for just opening browser and new tab
                    final_response = f"{open_response.message} I opened a new tab for you."
                    return final_response
            
            # Special handling for "search" commands without explicit "open" 
            elif is_search_command and not is_browser_command:
                # If they just say "search X" without specifying browser, we'll use default browser
                default_browser = "Safari"  # Default to Safari
                
                # Extract the search query
                search_query = command_text
                for term in ['search', 'look up', 'find', 'google']:
                    if term in search_query.lower():
                        search_query = search_query.lower().split(term, 1)[1].strip()
                        break
                
                # Create opening browser message
                opening_message = f"Opening {default_browser}"
                
                # Audio feedback using exact message
                if self.tts_enabled:
                    tts_service.say(opening_message)
                    
                # First open the browser
                open_response = nagato_agent.process_command(f"open {default_browser}")
                
                # Create new tab message
                new_tab_message = f"Opening new tab in {default_browser}"
                
                # Audio feedback using exact message
                if self.tts_enabled:
                    tts_service.say(new_tab_message)
                    
                # Then open a new tab
                nagato_agent.computer.open_new_browser_tab()
                
                # Create search message
                search_message = f"Searching for {search_query}"
                
                # Audio feedback using exact message
                if self.tts_enabled:
                    tts_service.say(search_message)
                    
                # Type with focus_browser=True
                type_response = nagato_agent.computer.type_text(search_query, focus_browser=True)
                
                # Final response message
                final_response = f"{open_response.message} I opened a new tab and searched for '{search_query}' for you."
                return final_response
            
            # Process normal command if it's not a special case
            response = nagato_agent.process_command(command_text)
            
            if response.success:
                if response.action_taken:
                    return f"{response.message}\n{response.action_taken}"
                return response.message
            else:
                # Fall back to conversational response if command fails
                return self._get_conversation_response(command_text)
                
        except Exception as e:
            print(f"Error processing command: {str(e)}")
            # Error message
            error_message = f"Sorry, I couldn't process that command: {str(e)}"
            
            # Audio feedback using exact error message
            if self.tts_enabled:
                tts_service.say(error_message)
                
            return error_message
            
    def _extract_search_or_url(self, command_text, browser_name):
        """Extract search query or URL from command"""
        try:
            command_lower = command_text.lower()
            result = None
            
            # Remove browser name from the command
            command_without_browser = command_lower.replace(browser_name.lower(), "")
            
            # Extract search query
            for term in ['search', 'look up', 'find', 'google']:
                if term in command_without_browser:
                    result = command_without_browser.split(term, 1)[1].strip()
                    break
            
            # Extract URL or website
            if not result:
                for term in ['go to', 'visit', 'open']:
                    if term in command_without_browser:
                        result = command_without_browser.split(term, 1)[1].strip()
                        break
            
            # Clean up result
            if result:
                # Remove filler words and punctuation at end
                for word in ["for", "about", "the", "website", "page"]:
                    if result.startswith(word + " "):
                        result = result[len(word) + 1:]
                
                result = result.strip('.,?! ')
                
            return result
            
        except Exception as e:
            print(f"Error extracting search/URL: {str(e)}")
            return None
            
    def _parse_compound_command(self, command_text):
        """Parse compound commands like 'open Safari and type what time is it in Ottawa'"""
        try:
            system_message = """You need to extract two pieces of information from a compound command:
            1. The application name (after "open" or "launch")
            2. The text to type or search (after "type", "search", "look up" or similar keywords)
            
            Respond with only these two items in the format: 
            application_name|text_to_type
            
            For example: 
            Input: "open Safari and type what time is it in Ottawa"
            Output: "Safari|what time is it in Ottawa"
            
            Input: "launch Chrome and search for best restaurants in NYC"
            Output: "Chrome|best restaurants in NYC"
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": command_text}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            parsed_result = response.choices[0].message.content.strip()
            if "|" in parsed_result:
                app_name, text_to_type = parsed_result.split("|", 1)
                return app_name.strip(), text_to_type.strip()
            return None
            
        except Exception as e:
            print(f"Error parsing compound command: {str(e)}")
            return None

    def _get_conversation_response(self, command_text):
        """Get conversational response when command processing fails"""
        system_message = """You are Nagato, a friendly and capable assistant. 
        Respond naturally to commands about controlling the computer, without mentioning 
        that you're an AI. Keep responses conversational and direct, as if you're 
        having a casual chat."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": command_text}
            ],
            temperature=0.7,
            max_tokens=150
        )

        return response.choices[0].message.content

# Create singleton instance
command_processor = CommandProcessor()