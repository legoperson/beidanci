import random
import pandas as pd
import os
import streamlit as st
import time
import requests
from datetime import datetime, timedelta

class VocabularyPractice:
    def __init__(self):
        """Initialize the vocabulary practice class"""
        self.words = []
        self.word_meanings = {}  # Store word meanings from CSV file
        self.word_examples = {}  # Store word examples from CSV file
        self.used_words = set()
        self.current_word = None
        self.is_playing = False
        self.study_words = []  # Words selected for current study session
        self.study_mode = False  # Whether in study mode
        self.study_start_time = None
    
    def load_words_from_csv(self, file_path):
        """
        Load words, meanings, and examples from CSV file
        Expected format: Column 1 = Word, Column 2 = Meaning, Column 3 = Example
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            bool: Success or failure
        """
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Check if file has at least 3 columns
            if len(df.columns) >= 3:
                # Clear existing data
                self.words = []
                self.word_meanings = {}
                self.word_examples = {}
                
                # Get column names (use first 3 columns regardless of names)
                word_col = df.columns[0]
                meaning_col = df.columns[1] 
                example_col = df.columns[2]
                
                # Load words, meanings and examples
                for index, row in df.iterrows():
                    word = str(row[word_col]).strip()
                    meaning = str(row[meaning_col]).strip()
                    example = str(row[example_col]).strip()
                    
                    if word and word.lower() != 'nan' and meaning and meaning.lower() != 'nan':
                        self.words.append(word)
                        self.word_meanings[word.lower()] = meaning
                        if example and example.lower() != 'nan':
                            self.word_examples[word.lower()] = example
                        else:
                            self.word_examples[word.lower()] = f"{word}"
                
                self.used_words = set()  # Reset used words
                return len(self.words) > 0
            else:
                st.error("CSV file must have at least 3 columns (Word, Meaning, Example)!")
                return False
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            return False
    
    def select_study_words(self, n):
        """
        Select n random words for study session
        
        Args:
            n (int): Number of words to select
            
        Returns:
            list: Selected words
        """
        if not self.words:
            return []
        
        # Select n random words (or all words if n > total words)
        n = min(n, len(self.words))
        self.study_words = random.sample(self.words, n)
        self.used_words = set()  # Reset used words for this study session
        
        return self.study_words
    
    def get_random_study_word(self):
        """
        Get a random word from the current study words that hasn't been used yet
        
        Returns:
            str: A random word from study words
        """
        if not self.study_words:
            st.error("No study words available!")
            return None
            
        # Reset used words if all study words have been used
        if len(self.used_words) >= len(self.study_words):
            st.info("All study words have been used once. Starting over...")
            self.used_words = set()
            
        # Get study words that haven't been used yet
        available_words = [word for word in self.study_words if word not in self.used_words]
        if not available_words:
            available_words = self.study_words  # Just in case
            
        # Select random word
        selected_word = random.choice(available_words)
        self.used_words.add(selected_word)
        self.current_word = selected_word
        return selected_word
    
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
    
    def start_study_mode(self):
        """Start study mode"""
        self.study_mode = True
        self.study_start_time = datetime.now()

# Create HTML for text-to-speech: word twice, then example once
def get_text_to_speech_html(word, example=""):
    # Escape quotes for JavaScript
    word_escaped = word.replace("'", "\\'").replace('"', '\\"')
    example_escaped = example.replace("'", "\\'").replace('"', '\\"')
    
    html = f"""
    <script>
        function speakText() {{
            // Clear any existing speech
            window.speechSynthesis.cancel();
            
            // Speak word first time
            var msg1 = new SpeechSynthesisUtterance('{word_escaped}');
            msg1.lang = 'en-US';
            msg1.rate = 0.8;
            
            // Speak word second time
            var msg2 = new SpeechSynthesisUtterance('{word_escaped}');
            msg2.lang = 'en-US';
            msg2.rate = 0.8;
            
            // Speak example sentence
            var msg3 = new SpeechSynthesisUtterance('{example_escaped}');
            msg3.lang = 'en-US';
            msg3.rate = 0.7;
            
            // Start speaking
            window.speechSynthesis.speak(msg1);
            
            msg1.onend = function() {{
                setTimeout(function() {{
                    window.speechSynthesis.speak(msg2);
                }}, 500);
            }};
            
            msg2.onend = function() {{
                setTimeout(function() {{
                    window.speechSynthesis.speak(msg3);
                }}, 1000);
            }};
        }}
        
        // Speak immediately when loaded
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(speakText, 500);
        }});
    </script>
    <button onclick="speakText()" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
        🔊 Repeat Word & Example
    </button>
    """
    return html

# Streamlit app
def main():
    st.set_page_config(page_title="Vocabulary Learn Practice", page_icon="📚")
    
    st.title("📚 Vocabulary Learn and Practice App")
    st.write("Practice your vocabulary spelling with this app!")
    
    # Define the path to the CSV file
    csv_path = "level234_meaning.csv"
    
    # Initialize session state
    if 'vocab_practice' not in st.session_state:
        st.session_state.vocab_practice = VocabularyPractice()
        # Try to load words immediately from local CSV file
        if os.path.exists(csv_path):
            if st.session_state.vocab_practice.load_words_from_csv(csv_path):
                st.success(f"Successfully loaded {len(st.session_state.vocab_practice.words)} words from {csv_path}!")
            else:
                st.error(f"Failed to load words from {csv_path}.")
        else:
            st.error(f"CSV file not found at {csv_path}. Please make sure level234.csv exists with columns: Word, Meaning, Example.")
    
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
        
    if 'spell_checked' not in st.session_state:
        st.session_state.spell_checked = False
    
    if 'user_input_word' not in st.session_state:
        st.session_state.user_input_word = ""
        
    if 'study_mode' not in st.session_state:
        st.session_state.study_mode = False
        
    if 'study_words_selected' not in st.session_state:
        st.session_state.study_words_selected = False
        
    if 'meanings_loaded' not in st.session_state:
        st.session_state.meanings_loaded = False
    
    # Display word count if words are loaded
    if hasattr(st.session_state.vocab_practice, 'words') and st.session_state.vocab_practice.words:
        st.write(f"Total words: {len(st.session_state.vocab_practice.words)}")
        
        # Study mode setup
        if not st.session_state.study_words_selected and not st.session_state.is_playing:
            st.subheader("📖 Study Setup")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                n_words = st.number_input("Number of words to study:", 
                                        min_value=1, 
                                        max_value=len(st.session_state.vocab_practice.words), 
                                        value=min(10, len(st.session_state.vocab_practice.words)))
                st.info("💡 Note: Word meanings and examples will be loaded from the CSV file")
            with col2:
                if st.button("Select Words for Study"):
                    with st.spinner("Selecting words..."):
                        selected_words = st.session_state.vocab_practice.select_study_words(n_words)
                        if selected_words:
                            st.session_state.study_words_selected = True
                            st.session_state.meanings_loaded = True
                            st.session_state.study_mode = False
                            st.rerun()
        
        # Show study words and meanings
        if st.session_state.study_words_selected and not st.session_state.study_mode and not st.session_state.is_playing:
            st.subheader("📚 Study Words")
            st.write(f"Selected {len(st.session_state.vocab_practice.study_words)} words for study:")
            
            if st.button("Start Learning"):
                st.session_state.vocab_practice.start_study_mode()
                st.session_state.study_mode = True
                st.rerun()
        
        # Study mode - show words, meanings, and examples
        if st.session_state.study_mode and not st.session_state.is_playing:
            st.subheader("📖 Learning Phase")
            st.write("Study these words, their meanings, and examples:")
            
            # Show study words with meanings and examples in a nice format
            for i, word in enumerate(st.session_state.vocab_practice.study_words, 1):
                with st.container():
                    st.markdown(f"### {i}. {word}")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        meaning = st.session_state.vocab_practice.word_meanings.get(word.lower(), "No meaning available")
                        st.markdown(f"**Meaning:** {meaning}")
                    with col2:
                        example = st.session_state.vocab_practice.word_examples.get(word.lower(), "No example available")
                        st.markdown(f"**Example:** {example}")
                    
                    st.divider()
            
            # Show Start Test button immediately
            st.success("✅ Ready to start the test!")
            if st.button("Start Test", type="primary"):
                st.session_state.is_playing = True
                # Get first word from study words
                word = st.session_state.vocab_practice.get_random_study_word()
                if word:
                    example = st.session_state.vocab_practice.word_examples.get(word.lower(), "")
                    st.session_state.current_word_component = get_text_to_speech_html(word, example)
                    st.session_state.feedback = None
                    st.session_state.spell_checked = False
                    st.session_state.user_input_word = ""
                    st.rerun()
        
        # Test mode
        if st.session_state.is_playing:
            st.write(f"Words practiced this session: {len(st.session_state.vocab_practice.used_words)}/{len(st.session_state.vocab_practice.study_words)}")
            
            # Stats display
            if st.session_state.total_count > 0:
                accuracy = (st.session_state.correct_count / st.session_state.total_count) * 100
                st.write(f"Correct: {st.session_state.correct_count}/{st.session_state.total_count} ({accuracy:.1f}%)")
        
            # Stop button
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Stop Test"):
                    st.session_state.is_playing = False
                    st.session_state.study_words_selected = False
                    st.session_state.study_mode = False
                    st.session_state.meanings_loaded = False
                    st.session_state.correct_count = 0
                    st.session_state.total_count = 0
                    st.session_state.feedback = None
                    st.session_state.spell_checked = False
                    st.session_state.user_input_word = ""
                    st.rerun()
            
            st.subheader("Spell the word you hear:")
            st.write("Listen carefully: The word will be spoken twice, followed by an example sentence.")
            
            # Display the text-to-speech component
            if st.session_state.current_word_component:
                st.components.v1.html(st.session_state.current_word_component, height=70)
            
            # Input form
            if not st.session_state.spell_checked:
                with st.form(key="spelling_form"):
                    user_spelling = st.text_input("Your spelling:", key="spelling_input")
                    submit_button = st.form_submit_button("Check Spelling")
                    
                    if submit_button and user_spelling:
                        st.session_state.user_input_word = user_spelling
                        
                        is_correct = st.session_state.vocab_practice.check_spelling(user_spelling)
                        st.session_state.total_count += 1
                        st.session_state.spell_checked = True
                        
                        if is_correct:
                            st.session_state.feedback = "✅ Correct!"
                            st.session_state.correct_count += 1
                        else:
                            st.session_state.feedback = f"❌ Incorrect. \n\nYour spelling: **{user_spelling}** \n\nCorrect spelling: **{st.session_state.vocab_practice.current_word}**"
                        
                        st.rerun()
            
            # Display feedback
            if st.session_state.feedback:
                st.markdown(f"### {st.session_state.feedback}")
                
                # Show meaning and example
                current_word_lower = st.session_state.vocab_practice.current_word.lower()
                if current_word_lower in st.session_state.vocab_practice.word_meanings:
                    meaning = st.session_state.vocab_practice.word_meanings[current_word_lower]
                    st.markdown(f"**Meaning:** *{meaning}*")
                
                if current_word_lower in st.session_state.vocab_practice.word_examples:
                    example = st.session_state.vocab_practice.word_examples[current_word_lower]
                    st.markdown(f"**Example:** *{example}*")
                
                # Next word button
                if st.button("Next Word"):
                    word = st.session_state.vocab_practice.get_random_study_word()
                    if word:
                        example = st.session_state.vocab_practice.word_examples.get(word.lower(), "")
                        st.session_state.current_word_component = get_text_to_speech_html(word, example)
                        st.session_state.feedback = None
                        st.session_state.spell_checked = False
                        st.session_state.user_input_word = ""
                        st.rerun()

if __name__ == "__main__":
    main()
