import random
import pandas as pd
import os
import streamlit as st
import time

class VocabularyPractice:
    def __init__(self):
        """Initialize the vocabulary practice class"""
        self.words = []
        self.used_words = set()
        self.current_word = None
        self.is_playing = False
    
    def load_words_from_excel(self, file_path):
        """
        Load words from Excel file - collect words from all columns
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            bool: Success or failure
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Check if file has any columns
            if len(df.columns) > 0:
                # Collect words from all columns
                all_words = []
                for column in df.columns:
                    column_words = [str(word).strip() for word in df[column] if str(word).strip() and str(word).lower() != 'nan']
                    all_words.extend(column_words)
                
                self.words = all_words
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

    def toggle_play(self):
        """Toggle play state"""
        self.is_playing = not self.is_playing
        return self.is_playing

# Create HTML for text-to-speech using the browser's built-in capabilities
def get_text_to_speech_html(text):
    html = f"""
    <script>
        function speakText() {{
            var msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'en-US';
            window.speechSynthesis.speak(msg);
            
            // Wait and speak again
            setTimeout(function() {{
                var msg2 = new SpeechSynthesisUtterance('{text}');
                msg2.lang = 'en-US';
                window.speechSynthesis.speak(msg2);
            }}, 1500);
        }}
        
        // Speak immediately when loaded
        document.addEventListener('DOMContentLoaded', function() {{
            speakText();
        }});
    </script>
    <button onclick="speakText()" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
        Repeat Word
    </button>
    """
    return html

# Streamlit app
def main():
    st.set_page_config(page_title="Vocabulary Practice", page_icon="📚")
    
    st.title("📚 Vocabulary Practice App")
    st.write("Practice your vocabulary spelling with this app!")
    
    # Define the path to the wordlist file in the repository
    wordlist_path = "level234.xlsx"
    
    # Initialize session state
    if 'vocab_practice' not in st.session_state:
        st.session_state.vocab_practice = VocabularyPractice()
        # Try to load words immediately from local file
        if os.path.exists(wordlist_path):
            if st.session_state.vocab_practice.load_words_from_excel(wordlist_path):
                st.success(f"Successfully loaded {len(st.session_state.vocab_practice.words)} words from {wordlist_path}!")
            else:
                st.error(f"Failed to load words from {wordlist_path}.")
        else:
            st.error(f"Word list file not found at {wordlist_path}.")
    
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
        
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
        
    if 'correct_count' not in st.session_state:
        st.session_state.correct_count = 0
        
    if 'total_count' not in st.session_state:
        st.session_state.total_count = 0
        
    if 'current_word_component' not in st.session_state:
        st.session_state.current_word_component = None
    
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
                    # Get a new word
                    word = st.session_state.vocab_practice.get_random_word()
                    if word:
                        st.session_state.current_word_component = get_text_to_speech_html(word)
                        st.session_state.feedback = None  # Reset feedback
                        st.rerun()
        
        # Only show the practice area if playing
        if st.session_state.is_playing:
            st.subheader("Spell the word you hear:")
            
            # Display the text-to-speech component
            if st.session_state.current_word_component:
                st.components.v1.html(st.session_state.current_word_component, height=70)
            
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
                    st.rerun()
            
            # Display feedback
            if st.session_state.feedback:
                st.markdown(f"### {st.session_state.feedback}")
                
                # Next word button (only show after feedback)
                if st.button("Next Word"):
                    word = st.session_state.vocab_practice.get_random_word()
                    if word:
                        st.session_state.current_word_component = get_text_to_speech_html(word)
                        st.session_state.feedback = None  # Reset feedback
                        st.rerun()

if __name__ == "__main__":
    main()
