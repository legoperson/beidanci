import random
import pandas as pd
import os
import streamlit as st
import time
from datetime import datetime, timedelta

class VocabularyPractice:
    def __init__(self):
        """Initialize the vocabulary practice class"""
        self.words = []
        self.word_meanings = {}  # Store word meanings
        self.used_words = set()
        self.current_word = None
        self.is_playing = False
        self.study_words = []  # Words selected for current study session
        self.study_mode = False  # Whether in study mode
        self.study_start_time = None
    
    def load_words_from_excel(self, file_path):
        """
        Load words from Excel file - collect words and meanings from columns
        
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
                # If there are at least 2 columns, assume first is word, second is meaning
                if len(df.columns) >= 2:
                    word_col = df.columns[0]
                    meaning_col = df.columns[1]
                    
                    # Collect words and meanings
                    all_words = []
                    word_meanings = {}
                    
                    for idx, row in df.iterrows():
                        word = str(row[word_col]).strip()
                        meaning = str(row[meaning_col]).strip()
                        
                        if word and word.lower() != 'nan' and meaning and meaning.lower() != 'nan':
                            all_words.append(word)
                            word_meanings[word] = meaning
                    
                    self.words = all_words
                    self.word_meanings = word_meanings
                else:
                    # Only one column, collect words only
                    all_words = []
                    for column in df.columns:
                        column_words = [str(word).strip() for word in df[column] if str(word).strip() and str(word).lower() != 'nan']
                        all_words.extend(column_words)
                    
                    self.words = all_words
                    self.word_meanings = {}  # No meanings available
                
                self.used_words = set()  # Reset used words
                return len(self.words) > 0
            else:
                st.error("No columns found in the Excel file!")
                return False
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
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
        
    def can_start_test(self):
        """Check if 5 minutes have passed since study started"""
        if not self.study_start_time:
            return False
        return datetime.now() - self.study_start_time >= timedelta(minutes=5)

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
        
    if 'spell_checked' not in st.session_state:
        st.session_state.spell_checked = False
    
    if 'user_input_word' not in st.session_state:
        st.session_state.user_input_word = ""
        
    if 'study_mode' not in st.session_state:
        st.session_state.study_mode = False
        
    if 'study_words_selected' not in st.session_state:
        st.session_state.study_words_selected = False
    
    # Display word count if words are loaded
    if hasattr(st.session_state.vocab_practice, 'words') and st.session_state.vocab_practice.words:
        st.write(f"Total words: {len(st.session_state.vocab_practice.words)}")
        
        # Study mode setup
        if not st.session_state.study_words_selected and not st.session_state.is_playing:
            st.subheader("📖 Study Setup")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                n_words = st.number_input("Number of words to study:", min_value=1, max_value=len(st.session_state.vocab_practice.words), value=10)
            with col2:
                if st.button("Select Words for Study"):
                    selected_words = st.session_state.vocab_practice.select_study_words(n_words)
                    if selected_words:
                        st.session_state.study_words_selected = True
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
        
        # Study mode - show words and meanings
        if st.session_state.study_mode and not st.session_state.is_playing:
            st.subheader("📖 Learning Phase")
            
            # Show study words with meanings
            for i, word in enumerate(st.session_state.vocab_practice.study_words, 1):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{i}. {word}**")
                with col2:
                    meaning = st.session_state.vocab_practice.word_meanings.get(word, "No meaning available")
                    st.write(f"*{meaning}*")
            
            # Check if 5 minutes have passed
            if st.session_state.vocab_practice.can_start_test():
                st.success("✅ 5 minutes study time completed!")
                if st.button("Start Test"):
                    st.session_state.is_playing = True
                    # Get first word from study words
                    word = st.session_state.vocab_practice.get_random_study_word()
                    if word:
                        st.session_state.current_word_component = get_text_to_speech_html(word)
                        st.session_state.feedback = None
                        st.session_state.spell_checked = False
                        st.session_state.user_input_word = ""
                        st.rerun()
            else:
                # Show countdown
                elapsed_time = datetime.now() - st.session_state.vocab_practice.study_start_time
                remaining_time = timedelta(minutes=5) - elapsed_time
                remaining_seconds = int(remaining_time.total_seconds())
                
                if remaining_seconds > 0:
                    minutes = remaining_seconds // 60
                    seconds = remaining_seconds % 60
                    st.info(f"⏰ Study time remaining: {minutes:02d}:{seconds:02d}")
                    # Auto-refresh every second
                    time.sleep(1)
                    st.rerun()
        
        # Test mode (existing functionality, but using study words)
        if st.session_state.is_playing:
            st.write(f"Words practiced this session: {len(st.session_state.vocab_practice.used_words)}")
            
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
                    st.session_state.correct_count = 0
                    st.session_state.total_count = 0
                    st.session_state.feedback = None
                    st.session_state.spell_checked = False
                    st.session_state.user_input_word = ""
                    st.rerun()
            
            st.subheader("Spell the word you hear:")
            
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
                
                # Show meaning if available
                if st.session_state.vocab_practice.current_word in st.session_state.vocab_practice.word_meanings:
                    meaning = st.session_state.vocab_practice.word_meanings[st.session_state.vocab_practice.current_word]
                    st.write(f"**Meaning:** {meaning}")
                
                # Next word button
                if st.button("Next Word"):
                    word = st.session_state.vocab_practice.get_random_study_word()
                    if word:
                        st.session_state.current_word_component = get_text_to_speech_html(word)
                        st.session_state.feedback = None
                        st.session_state.spell_checked = False
                        st.session_state.user_input_word = ""
                        st.rerun()

if __name__ == "__main__":
    main()
