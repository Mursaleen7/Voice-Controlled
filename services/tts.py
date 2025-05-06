import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
import pygame
import threading
import time
import re
import random

# Load environment variables
load_dotenv()

class TextToSpeech:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Use a warmer, more natural voice
        self.voice = os.getenv('TTS_VOICE', 'nova')  # Changed default to nova for more natural voice
        self.temp_dir = tempfile.gettempdir()
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Queue for managing multiple speech requests
        self.speech_queue = []
        self.is_speaking = False
        self.queue_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.queue_thread.start()
        
        # Conversation starters and fillers for more natural speech
        self.conversation_starters = [
            "Hmm, ", "Let's see, ", "Okay, ", "Alright, ", "Sure, ", "Got it, "
        ]
        
        # Response variations for common actions
        self.response_variations = {
            "opening": ["Opening", "Launching", "Starting", "Getting"],
            "searching": ["Looking up", "Searching for", "Finding info about", "Checking"],
            "typing": ["Typing", "Entering", "Putting in"],
            "volume": ["Adjusting volume", "Changing the volume", "Setting volume"],
            "screenshot": ["Taking a screenshot", "Capturing the screen", "Grabbing a snapshot"]
        }
    
    def say(self, text, blocking=False):
        """Convert text to speech and play it"""
        if not text:
            return
            
        # Preprocess text to make it more conversational
        conversational_text = self._make_conversational(text)
        
        # Add speech request to queue
        self.speech_queue.append(conversational_text)
        
        # If blocking is True, wait until speech is completed
        if blocking:
            while conversational_text in self.speech_queue or self.is_speaking:
                time.sleep(0.1)
    
    def _process_speech_queue(self):
        """Process the speech queue in a separate thread"""
        while True:
            if self.speech_queue and not self.is_speaking:
                text = self.speech_queue.pop(0)
                self.is_speaking = True
                self._generate_and_play_speech(text)
                self.is_speaking = False
            time.sleep(0.1)
    
    def _make_conversational(self, text):
        """Make the text more conversational by adding markers, variations and pauses"""
        # Skip preprocessing for system messages like "Processing..." or "Listening..."
        if text in ["Processing...", "Listening...", "Responding..."]:
            return text
            
        # Don't add conversation starters to error messages
        if text.startswith("Error:") or text.startswith("Sorry, I encountered an error"):
            return text
            
        # Add random conversation starter (30% of the time when appropriate)
        if random.random() < 0.3 and not any(text.startswith(starter) for starter in self.conversation_starters):
            text = random.choice(self.conversation_starters) + text
            
        # Replace formal phrases with contractions
        contractions = {
            "I am": "I'm",
            "I have": "I've",
            "I will": "I'll",
            "cannot": "can't",
            "could not": "couldn't",
            "did not": "didn't",
            "does not": "doesn't",
            "do not": "don't",
            "had not": "hadn't",
            "has not": "hasn't",
            "have not": "haven't",
            "is not": "isn't",
            "it is": "it's",
            "should not": "shouldn't",
            "that is": "that's",
            "they are": "they're",
            "was not": "wasn't",
            "were not": "weren't",
            "what is": "what's",
            "will not": "won't",
            "would not": "wouldn't",
            "you are": "you're",
            "you have": "you've",
            "you will": "you'll"
        }
        
        for formal, contraction in contractions.items():
            # Use word boundaries to avoid partial word matches
            text = re.sub(r'\b' + formal + r'\b', contraction, text, flags=re.IGNORECASE)
            
        # Add SSML pauses for more natural speech rhythm
        # Note: OpenAI TTS supports basic SSML tags
        text = text.replace(". ", ". <break time='300ms'/> ")
        text = text.replace("! ", "! <break time='300ms'/> ")
        text = text.replace("? ", "? <break time='300ms'/> ")
        text = text.replace(", ", ", <break time='150ms'/> ")
        
        # Vary common action phrases
        for action_type, variations in self.response_variations.items():
            if action_type in text.lower():
                for phrase in variations:
                    if phrase.lower() in text.lower():
                        replacement = random.choice(variations)
                        text = re.sub(r'\b' + phrase + r'\b', replacement, text, flags=re.IGNORECASE)
                        break
                        
        return text
    
    def _generate_and_play_speech(self, text):
        """Generate speech using OpenAI API and play it"""
        try:
            # Generate a unique filename
            speech_file_path = os.path.join(self.temp_dir, f"speech_{int(time.time())}.mp3")
            
            # Create and save the speech file
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text
            )
            response.stream_to_file(speech_file_path)
            
            # Play the audio
            pygame.mixer.music.load(speech_file_path)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            # Clean up the temporary file
            try:
                os.remove(speech_file_path)
            except:
                pass
                
        except Exception as e:
            print(f"Error generating or playing speech: {str(e)}")

# Create a singleton instance
tts_service = TextToSpeech() 