import tkinter as tk
from tkinter import ttk
import datetime
import math
import random
import os
from dotenv import load_dotenv

# Import the TTS service for UI state feedback
from services.tts import tts_service

# Load environment variables
load_dotenv()

class NagatoUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Nagato")
        self.root.geometry("400x600")
        self.root.minsize(400, 600)
        
        # Animation variables
        self.wave_points = 8
        self.animation_running = False
        self.wave_height = 20
        self.wave_speeds = [random.uniform(0.1, 0.2) for _ in range(self.wave_points)]
        self.wave_offsets = [random.uniform(0, 2 * math.pi) for _ in range(self.wave_points)]
        self.time = 0
        
        # Pulse animation variables
        self.pulse_alpha = 1.0
        self.pulse_increasing = False
        
        # Define font families with fallbacks
        self.title_font = ("Arial", 16, "bold")  # Simplified font definition
        self.text_font = ("Arial", 12)           # Simplified font definition
        self.button_font = ("Arial", 10, "bold") # Font for button
        self.speaker_font = ("Arial", 12, "bold") # Font for speaker labels
        
        # Check if TTS is enabled
        self.tts_enabled = os.getenv('TTS_ENABLED', 'true').lower() == 'true'
        
        self.setup_ui()
        self.start_pulse_animation()
        
    def create_gradient(self, canvas, color1, color2):
        """Create a vertical gradient on the canvas"""
        height = 600
        width = 400
        for i in range(height):
            # Calculate color for each line of pixels
            r1, g1, b1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
            r2, g2, b2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
            
            r = int(r1 + (r2 - r1) * i / height)
            g = int(g1 + (g2 - g1) * i / height)
            b = int(b1 + (b2 - b1) * i / height)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_line(0, i, width, i, fill=color)
        
    def setup_ui(self):
        # Create background canvas for gradient
        self.bg_canvas = tk.Canvas(
            self.root,
            width=400,
            height=600,
            highlightthickness=0,
            bg='#1A1A2E'  # Default background color
        )
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create gradient background (deep purple to dark blue)
        self.create_gradient(self.bg_canvas, '#2C1F4A', '#1A1A2E')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1A1A2E')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Spacer
        tk.Frame(main_frame, height=50, bg='#1A1A2E').pack()
        
        # Create wave/circle canvas
        self.wave_canvas = tk.Canvas(
            main_frame,
            width=200,
            height=100,
            bg='#1A1A2E',
            highlightthickness=0
        )
        self.wave_canvas.pack(pady=20)
        
        # Create the pulse circle
        self.pulse_circle = self.wave_canvas.create_oval(
            70, 20, 130, 80,  # Centered circle
            outline='#007AFF',
            width=2
        )
        
        # Create the wave lines
        self.wave_lines = []
        for i in range(4):
            line = self.wave_canvas.create_line(
                0, 0, 0, 0,
                fill=f"#{50+i*20:02x}{180+i*20:02x}ff",  # Brighter blue waves
                width=2,
                smooth=True
            )
            self.wave_lines.append(line)
            self.wave_canvas.itemconfig(line, state='hidden')
        
        # Status text with glowing effect
        self.status_label = tk.Label(
            main_frame,
            text="Tap to speak or type below",
            font=self.title_font,
            fg="#FFFFFF",
            bg='#1A1A2E'
        )
        self.status_label.pack(pady=20)
        
        # Create a frame for response area with scrolling capability
        response_frame = tk.Frame(main_frame, bg='#1A1A2E')
        response_frame.pack(pady=10, padx=25, fill=tk.BOTH, expand=True)
        
        # Response area using Text widget for more formatting control
        self.response_text = tk.Text(
            response_frame,
            font=self.text_font,
            fg="#E0E0E0",
            bg='#1A1A2E',
            width=40,
            height=10,
            wrap=tk.WORD,
            padx=5,
            pady=5,
            bd=0,
            highlightthickness=0,
            insertbackground='#FFFFFF'  # Cursor color
        )
        self.response_text.pack(fill=tk.BOTH, expand=True)
        
        # Create tags for formatting different parts of the conversation
        self.response_text.tag_configure("you", foreground="#C2C2FF", font=self.speaker_font)
        self.response_text.tag_configure("nagato", foreground="#8EFFBC", font=self.speaker_font)
        self.response_text.tag_configure("user_text", foreground="#E0E0E0", font=self.text_font)
        self.response_text.tag_configure("assistant_text", foreground="#FFFFFF", font=self.text_font)
        
        # Make the Text widget read-only
        self.response_text.config(state=tk.DISABLED)
        
        # Add text input area at the bottom of the UI
        input_frame = tk.Frame(main_frame, bg='#1A1A2E', pady=10)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # Text input field
        self.text_input = tk.Entry(
            input_frame,
            font=self.text_font,
            bg='#2A2A3E',
            fg='#FFFFFF',
            insertbackground='#FFFFFF',  # Cursor color
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground='#007AFF',
            highlightcolor='#007AFF'
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Bind Enter key to submit command
        self.text_input.bind("<Return>", self.submit_text_command)
        
        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            font=self.button_font,
            bg='#007AFF',
            fg='#FFFFFF',
            relief=tk.FLAT,
            padx=10,
            command=self.submit_text_command
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Bind click event for voice activation
        self.wave_canvas.bind("<Button-1>", self.activate_assistant)
        self.status_label.bind("<Button-1>", self.activate_assistant)
        
        # Initialize typing animation variables
        self.current_char = 0
        self.full_response = ""
        self.typing_in_progress = False
        self.typing_speed = [15, 25, 35, 45]  # Variable speeds for more natural typing
        
    def start_pulse_animation(self):
        if not self.animation_running:
            self.animate_pulse()
    
    def animate_pulse(self):
        if self.animation_running:
            # Hide pulse circle during wave animation
            self.wave_canvas.itemconfig(self.pulse_circle, state='hidden')
            return
            
        # Show and animate pulse circle
        self.wave_canvas.itemconfig(self.pulse_circle, state='normal')
        
        # Update alpha for pulsing effect
        if self.pulse_increasing:
            self.pulse_alpha += 0.2  # Faster transition
            if self.pulse_alpha >= 1.0:
                self.pulse_increasing = False
                # Wait longer at full brightness
                self.root.after(500, self.animate_pulse)
                return
        else:
            self.pulse_alpha -= 0.2  # Faster transition
            if self.pulse_alpha <= 0.2:
                self.pulse_increasing = True
                # Wait longer at dim state
                self.root.after(500, self.animate_pulse)
                return
        
        # Create color based on alpha without using alpha channel
        r = 0
        g = 122
        b = 255
        
        # Adjust brightness instead of alpha
        factor = self.pulse_alpha
        color = f'#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}'
        
        self.wave_canvas.itemconfig(
            self.pulse_circle,
            outline=color
        )
        
        # Slower pulse rate (500ms for fade + 500ms pause = 1 second cycle)
        self.root.after(100, self.animate_pulse)
        
    def animate_waves(self):
        if not self.animation_running:
            # Hide waves and show pulse
            for line in self.wave_lines:
                self.wave_canvas.itemconfig(line, state='hidden')
            self.wave_canvas.itemconfig(self.pulse_circle, state='normal')
            return
            
        # Hide pulse and show waves
        self.wave_canvas.itemconfig(self.pulse_circle, state='hidden')
        for line in self.wave_lines:
            self.wave_canvas.itemconfig(line, state='normal')
        
        self.time += 0.05  # Slower time progression
        canvas_width = 200
        canvas_height = 100
        center_y = canvas_height // 2
        
        # Create more natural wave movement
        for wave_idx, wave_line in enumerate(self.wave_lines):
            points = []
            base_amplitude = self.wave_height - (wave_idx * 4)  # Decreasing amplitude for each wave
            
            # Add multiple sine waves with different frequencies
            for i in range(self.wave_points * 2):  # Double the points for smoother waves
                x = i * canvas_width / (self.wave_points * 2 - 1)
                
                # Combine multiple sine waves
                y = center_y
                y += math.sin(self.time * 2 + x * 0.05) * base_amplitude * 0.5
                y += math.sin(self.time * 1.5 + x * 0.03) * base_amplitude * 0.3
                y += math.sin(self.time + x * 0.02) * base_amplitude * 0.2
                
                # Add small random variation
                y += random.uniform(-0.5, 0.5)
                
                points.extend([x, y])
            
            self.wave_canvas.coords(wave_line, *points)
        
        self.root.after(30, self.animate_waves)
    
    def submit_text_command(self, event=None):
        """Handle text command submission"""
        command = self.text_input.get().strip()
        if not command:
            return
        
        # Clear the input field
        self.text_input.delete(0, tk.END)
        
        # Update UI state
        self.status_label.config(text="Processing...")
        
        # Speak the status
        if self.tts_enabled:
            tts_service.say(self.status_label.cget("text"))
            
        self.wave_height = 10
        self.animation_running = True
        self.animate_waves()
        
        # Process the command
        self.handle_command(command)
        
    def activate_assistant(self, event=None):
        self.animation_running = True
        self.wave_height = 20
        self.status_label.config(text="Listening...")
        
        # Speak the status
        if self.tts_enabled:
            tts_service.say(self.status_label.cget("text"))
            
        self.animate_waves()
        
        # Start voice recognition in a separate thread to prevent UI freezing
        self.root.after(100, self.start_voice_recognition)
        
    def start_voice_recognition(self):
        from services.vtt import vtt_service
        import threading
        
        def recognition_thread():
            try:
                command = vtt_service.get_voice_command()
                # Use after to safely update UI from thread
                self.root.after(0, self.handle_command, command)
            except Exception as e:
                error_message = f"Error: {str(e)}"
                self.root.after(0, self.handle_error, error_message)
            
        thread = threading.Thread(target=recognition_thread)
        thread.daemon = True
        thread.start()
        
    def handle_command(self, command):
        self.status_label.config(text="Processing...")
        
        # Speak the status
        if self.tts_enabled and not command.startswith("Error:"):
            tts_service.say(self.status_label.cget("text"))
            
        self.wave_height = 10
        
        # Import and use the command processor
        from services.process_command import command_processor
        
        # Process the command
        try:
            response = command_processor.process_command(command)
            # Start the typing animation
            self.start_typing_animation(command, response)
        except Exception as e:
            error_message = f"Error processing command: {str(e)}"
            
            # Audio feedback for error
            if self.tts_enabled:
                tts_service.say(error_message)
                
            self.root.after(1000, lambda: self.show_response(error_message))
        
    def start_typing_animation(self, command, response):
        # Enable text widget for editing
        self.response_text.config(state=tk.NORMAL)
        
        # Clear previous text if this is a new conversation
        if not self.typing_in_progress:
            self.response_text.delete(1.0, tk.END)
        
        # Format user message with tags for styling
        self.response_text.insert(tk.END, "You: ", "you")
        self.response_text.insert(tk.END, command + "\n\n", "user_text")
        
        # Add Nagato's response header
        self.response_text.insert(tk.END, "Nagato: ", "nagato")
        
        # Store the response for typing animation
        self.full_response = response
        self.current_char = 0
        self.typing_in_progress = True
        
        # Stop wave animation and show we're typing
        self.animation_running = False
        self.status_label.config(text="Responding...")
        
        # Speak the status
        if self.tts_enabled:
            tts_service.say(self.status_label.cget("text"))
            # Then speak Nagato's full response
            tts_service.say(response)
        
        # Start typing animation
        self.type_next_char()
        
        # Scroll to the end
        self.response_text.see(tk.END)
        
        # Disable text widget to make it read-only
        self.response_text.config(state=tk.DISABLED)
        
    def type_next_char(self):
        if self.current_char < len(self.full_response):
            # Enable text widget for editing
            self.response_text.config(state=tk.NORMAL)
            
            # Add the next character with our styling
            next_char = self.full_response[self.current_char]
            self.response_text.insert(tk.END, next_char, "assistant_text")
            self.current_char += 1
            
            # Scroll to show the latest text
            self.response_text.see(tk.END)
            
            # Make read-only again
            self.response_text.config(state=tk.DISABLED)
            
            # Determine typing speed for natural flow
            if next_char in ".!?":
                delay = random.randint(70, 120)  # Longer pause after sentences
            elif next_char in ",;:":
                delay = random.randint(50, 80)   # Medium pause for punctuation
            else:
                # Random variation in typing speed
                delay = random.choice(self.typing_speed)
                
                # Occasionally add a longer pause for more realism (thinking pause)
                if random.random() < 0.03:  # 3% chance for a thinking pause
                    delay = random.randint(200, 300)
            
            self.root.after(delay, self.type_next_char)
        else:
            # Typing animation is complete
            self.typing_in_progress = False
            self.root.after(500, self.show_response_complete)
            
    def show_response_complete(self):
        self.status_label.config(text="Tap to speak or type below")
        
        # No need to speak the status again as we've already spoken the full response
        
        self.animation_running = False
        self.animate_pulse()  # Start pulse animation again
        
    def show_response(self, response_text):
        # Enable text widget for editing
        self.response_text.config(state=tk.NORMAL)
        
        # Clear and add formatted response
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, "Nagato: ", "nagato")
        self.response_text.insert(tk.END, response_text, "assistant_text")
        
        # Make read-only again
        self.response_text.config(state=tk.DISABLED)
        
        self.status_label.config(text="Tap to speak or type below")
        
        # Speak the exact response text
        if self.tts_enabled:
            tts_service.say(response_text)
            
        self.animation_running = False
        self.animate_pulse()  # Start pulse animation again
        
    def handle_error(self, error_message):
        # Audio feedback for error - use the exact error message
        if self.tts_enabled:
            tts_service.say(error_message)
            
        self.show_response(error_message)
        self.status_label.config(text="Tap to speak or type below")

def main():
    root = tk.Tk()
    app = NagatoUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
