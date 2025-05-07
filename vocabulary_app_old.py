import random
import pandas as pd
import os
import time
import streamlit as st
from gtts import gTTS
import pygame
import tempfile
import threading
import io

class VocabularyPractice:
    def __init__(self):
        """Initialize the vocabulary practice class"""
        self.words = []
        self.used_words = set()
        self.current_word = None
        self.is_playing = False
        self.temp_audio_file = None
        
        # Initialize pygame mixer
        pygame.mixer.init()
    
    def load_words_from_excel(self, file):
        """
        Load words from Excel file
        
        Args:
            file: Uploaded file or file path
            
        Returns:
            bool: Success or failure
        """
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Get words from the first column
            if len(df.columns) > 0:
                words_column = df.iloc[:, 0]  # Get the first column
                self.words = [str(word).strip() for word in words_column if str(word).strip()]  # Convert to list and remove whitespace
                self.used_words = set()  # Reset used words
                return len(self.words) > 0
            else:
                st.error("No columns found in the Excel file!")
                return False
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
            return False
    
    def get_random_word(self):
        """
        Get a random word from the list that hasn't been used yet
        
        Returns:
            str: A random word
        """
        if not self.words:
            st.error("No words available!")
            return None
            
        # Reset used words if all words have been used
        if len(self.used_words) >= len(self.words):
            st.info("All words have been used once. Starting over...")
            self.used_words = set()
            
        # Get words that haven't been used yet
        available_words = [word for word in self.words if word not in self.used_words]
        if not available_words:
            available_words = self.words  # Just in case
            
        # Select random word
        selected_word = random.choice(available_words)
        self.used_words.add(selected_word)
        self.current_word = selected_word
        return selected_word
    
    def speak_word(self, word):
        """
        Convert text to speech and play it
        
        Args:
            word (str): Word to be spoken
        """
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                self.temp_audio_file = temp_file.name
            
            # Generate speech file using Google TTS
            tts = gTTS(text=word, lang='en', slow=False)
            tts.save(self.temp_audio_file)
            
            # Play the audio
            pygame.mixer.music.load(self.temp_audio_file)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Clean up
            pygame.mixer.music.unload()
        except Exception as e:
            st.error(f"Error during speech playback: {e}")
            return False
            
        return True
    
    def speak_current_word_twice(self):
        """Speak the current word twice"""
        if not self.current_word:
            st.warning("No word selected yet!")
            return
            
        # Speak word twice
        self.speak_word(self.current_word)
        time.sleep(0.5)  # Brief pause
        self.speak_word(self.current_word)
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Remove temp audio file if it exists
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
        except:
            pass  # Ignore errors when cleaning up

    def toggle_play(self):
        """Toggle play state"""
        self.is_playing = not self.is_playing
        return self.is_playing
        
    def check_spelling(self, user_input):
        """
        Check if the user's spelling is correct
        
        Args:
            user_input (str): User's spelling attempt
            
        Returns:
            bool: Whether the spelling is correct
        """
        if not self.current_word:
            return False
            
        return user_input.strip().lower() == self.current_word.strip().lower()

# Streamlit app
def main():
    st.set_page_config(page_title="Vocabulary Practice", page_icon="📚")
    
    st.title("📚 Vocabulary Practice App")
    st.write("Practice your vocabulary spelling with this app!")
    
    # Initialize session state
    if 'vocab_practice' not in st.session_state:
        st.session_state.vocab_practice = VocabularyPractice()
    
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
        
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
        
    if 'correct_count' not in st.session_state:
        st.session_state.correct_count = 0
        
    if 'total_count' not in st.session_state:
        st.session_state.total_count = 0
    
    # File uploader
    uploaded_file = st.file_uploader("Upload an Excel file with words in the first column:", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        if st.button("Load Words"):
            if st.session_state.vocab_practice.load_words_from_excel(uploaded_file):
                st.success(f"Successfully loaded {len(st.session_state.vocab_practice.words)} words!")
                
    # Display word count if words are loaded
    if hasattr(st.session_state.vocab_practice, 'words') and st.session_state.vocab_practice.words:
        st.write(f"Total words: {len(st.session_state.vocab_practice.words)}")
        st.write(f"Words practiced this session: {len(st.session_state.vocab_practice.used_words)}")
        
        # Stats display
        if st.session_state.total_count > 0:
            accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
            st.write(f"Correct: {st.session_state.correct_count}/{st.session_state.total_count} ({accuracy:.1f}%)")
    
        # Play/Stop button
        col1, col2 = st.columns([1, 4])
        with col1:
            button_label = "Stop" if st.session_state.is_playing else "Start"
            if st.button(button_label):
                st.session_state.is_playing = st.session_state.vocab_practice.toggle_play()
                
                if st.session_state.is_playing:
                    # Get a new word and speak it
                    word = st.session_state.vocab_practice.get_random_word()
                    if word:
                        # Run in a thread to not block the UI
                        threading.Thread(
                            target=st.session_state.vocab_practice.speak_current_word_twice
                        ).start()
                        st.session_state.feedback = None  # Reset feedback
                        st.experimental_rerun()
        
        # Only show the practice area if playing
        if st.session_state.is_playing:
            st.subheader("Spell the word you hear:")
            
            with st.form(key="spelling_form"):
                user_spelling = st.text_input("Your spelling:", key="spelling_input")
                submit_button = st.form_submit_button("Check Spelling")
                
                if submit_button:
                    is_correct = st.session_state.vocab_practice.check_spelling(user_spelling)
                    st.session_state.total_count += 1
                    
                    if is_correct:
                        st.session_state.feedback = "✅ Correct!"
                        st.session_state.correct_count += 1
                    else:
                        st.session_state.feedback = f"❌ Incorrect. The correct spelling is: {st.session_state.vocab_practice.current_word}"
                    
                    # Get ready for next word
                    st.experimental_rerun()
            
            # Repeat word button
            if st.button("Repeat Word"):
                threading.Thread(
                    target=st.session_state.vocab_practice.speak_current_word_twice
                ).start()
            
            # Display feedback
            if st.session_state.feedback:
                st.markdown(f"### {st.session_state.feedback}")
                
                # Next word button (only show after feedback)
                if st.button("Next Word"):
                    word = st.session_state.vocab_practice.get_random_word()
                    if word:
                        threading.Thread(
                            target=st.session_state.vocab_practice.speak_current_word_twice
                        ).start()
                        st.session_state.feedback = None  # Reset feedback
                        st.experimental_rerun()

if __name__ == "__main__":
    main()
