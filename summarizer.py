from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
import nltk
from nltk.tokenize import sent_tokenize
import warnings
from langdetect import detect, DetectorFactory
from googletrans import Translator
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

warnings.filterwarnings("ignore", category=UserWarning)

# Set seed for consistent language detection
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class NoteSummarizer:
    def __init__(self):
        """Initialize the summarizer with multilingual support"""
        self.translator = Translator()
        self.supported_languages = {
            'te': 'Telugu' ,
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish'
        }
        
        try:
            # Initialize multilingual models
            self._init_english_model()
            self._init_multilingual_model()
            
            print(f"Models loaded successfully on {'GPU' if self.device == 0 else 'CPU'}")
            
        except Exception as e:
            print(f"Error loading models: {e}")
            raise Exception("Could not load any summarization model")
    
    def _init_english_model(self):
        """Initialize English-specific model"""
        try:
            # Use a lightweight model that works well for summarization
            model_name = "facebook/bart-large-cnn"
            
            # Check if CUDA is available
            self.device = 0 if torch.cuda.is_available() else -1
            
            # Initialize the summarization pipeline
            self.english_summarizer = pipeline(
                "summarization",
                model=model_name,
                tokenizer=model_name,
                device=self.device
            )
            
            self.english_tokenizer = AutoTokenizer.from_pretrained(model_name)
            
        except Exception as e:
            print(f"Error loading English model: {e}")
            # Fallback to a smaller model
            try:
                model_name = "sshleifer/distilbart-cnn-6-6"
                self.english_summarizer = pipeline(
                    "summarization",
                    model=model_name,
                    device=self.device
                )
                self.english_tokenizer = AutoTokenizer.from_pretrained(model_name)
                print("English fallback model loaded successfully")
            except Exception as fallback_error:
                print(f"English fallback model also failed: {fallback_error}")
                raise Exception("Could not load any English summarization model")
    
    def _init_multilingual_model(self):
        """Initialize multilingual model"""
        try:
            # Use mBART for multilingual summarization
            model_name = "facebook/mbart-large-cc25"
            
            self.multilingual_summarizer = pipeline(
                "summarization",
                model=model_name,
                tokenizer=model_name,
                device=self.device
            )
            
            self.multilingual_tokenizer = AutoTokenizer.from_pretrained(model_name)
            
        except Exception as e:
            print(f"Multilingual model not available: {e}")
            # Use English model as fallback for all languages
            self.multilingual_summarizer = self.english_summarizer
            self.multilingual_tokenizer = self.english_tokenizer
    
    def detect_language(self, text):
        """Detect the language of the input text"""
        try:
            if not text or len(text.strip()) < 10:
                return 'en'  # Default to English for short texts
            
            detected_lang = detect(text)
            
            # Map some common language codes
            lang_mapping = {
                'ca': 'es',  # Catalan to Spanish
                'zh-cn': 'zh',  # Simplified Chinese
                'zh-tw': 'zh',  # Traditional Chinese
            }
            
            detected_lang = lang_mapping.get(detected_lang, detected_lang)
            
            # Check if we support this language
            if detected_lang in self.supported_languages:
                return detected_lang
            else:
                return 'en'  # Default to English for unsupported languages
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'en'  # Default to English on error
    
    def translate_text(self, text, target_lang='en', source_lang='auto'):
        """Translate text to target language"""
        try:
            if source_lang == target_lang:
                return text
            
            # Handle long texts by splitting into chunks
            if len(text) > 5000:
                sentences = sent_tokenize(text)
                translated_sentences = []
                
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + sentence) < 5000:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            translated = self.translator.translate(
                                current_chunk.strip(), 
                                src=source_lang, 
                                dest=target_lang
                            )
                            translated_sentences.append(translated.text)
                        current_chunk = sentence + " "
                
                if current_chunk:
                    translated = self.translator.translate(
                        current_chunk.strip(), 
                        src=source_lang, 
                        dest=target_lang
                    )
                    translated_sentences.append(translated.text)
                
                return " ".join(translated_sentences)
            else:
                translated = self.translator.translate(text, src=source_lang, dest=target_lang)
                return translated.text
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original text if translation fails
    
    def preprocess_text(self, text):
        """Clean and preprocess the input text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove very short sentences (likely not meaningful)
        sentences = sent_tokenize(text)
        meaningful_sentences = [s for s in sentences if len(s.split()) > 3]
        
        return ' '.join(meaningful_sentences)
    
    def chunk_text(self, text, max_chunk_length=1000, tokenizer=None):
        """Split text into chunks that fit within model limits"""
        if tokenizer is None:
            tokenizer = self.english_tokenizer
            
        # Get token count
        tokens = tokenizer.encode(text)
        
        if len(tokens) <= max_chunk_length:
            return [text]
        
        # Split into sentences and group into chunks
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed the limit
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            test_tokens = len(tokenizer.encode(test_chunk))
            
            if test_tokens <= max_chunk_length:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def summarize_text(self, text, max_length=150, min_length=50, summary_type="balanced", target_language=None):
        """
        Summarize the input text with multilingual support
        
        Args:
            text (str): Input text to summarize
            max_length (int): Maximum length of summary
            min_length (int): Minimum length of summary
            summary_type (str): Type of summary - "brief", "balanced", or "detailed"
            target_language (str): Target language for summary (None for auto-detect)
        
        Returns:
            dict: Contains summary text and metadata
        """
        try:
            if not text or len(text.strip()) < 50:
                return {
                    "summary": "Text too short to summarize effectively.",
                    "original_length": len(text.split()),
                    "summary_length": 0,
                    "compression_ratio": 0,
                    "detected_language": "en",
                    "language_name": "English"
                }
            
            # Detect language
            detected_lang = self.detect_language(text)
            lang_name = self.supported_languages.get(detected_lang, "Unknown")
            
            # Use target language if specified, otherwise use detected language
            if target_language and target_language in self.supported_languages:
                summary_lang = target_language
            else:
                summary_lang = detected_lang
            
            # Adjust parameters based on summary type
            if summary_type == "brief":
                max_length = min(max_length, 100)
                min_length = min(min_length, 30)
            elif summary_type == "detailed":
                max_length = min(max_length * 2, 300)
                min_length = min(min_length * 1.5, 100)
            
            # Preprocess the text
            processed_text = self.preprocess_text(text)
            
            # Choose appropriate model and tokenizer
            if detected_lang == 'en':
                summarizer = self.english_summarizer
                tokenizer = self.english_tokenizer
                working_text = processed_text
            else:
                # For non-English text, translate to English for better summarization
                working_text = self.translate_text(processed_text, target_lang='en', source_lang=detected_lang)
                summarizer = self.english_summarizer
                tokenizer = self.english_tokenizer
            
            # Split into chunks if necessary
            chunks = self.chunk_text(working_text, tokenizer=tokenizer)
            
            summaries = []
            for chunk in chunks:
                try:
                    result = summarizer(
                        chunk,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False,
                        truncation=True
                    )
                    summaries.append(result[0]['summary_text'])
                except Exception as chunk_error:
                    print(f"Error summarizing chunk: {chunk_error}")
                    # If individual chunk fails, try with more conservative settings
                    try:
                        result = summarizer(
                            chunk,
                            max_length=min(max_length, 100),
                            min_length=min(min_length, 20),
                            do_sample=False,
                            truncation=True
                        )
                        summaries.append(result[0]['summary_text'])
                    except:
                        summaries.append("Could not summarize this section.")
            
            # Combine summaries if multiple chunks
            if len(summaries) > 1:
                combined_summary = ' '.join(summaries)
                # If combined summary is too long, summarize it again
                if len(combined_summary.split()) > max_length * 1.5:
                    try:
                        final_result = summarizer(
                            combined_summary,
                            max_length=max_length,
                            min_length=min_length,
                            do_sample=False,
                            truncation=True
                        )
                        final_summary = final_result[0]['summary_text']
                    except:
                        final_summary = combined_summary[:max_length * 6]  # Rough character limit
                else:
                    final_summary = combined_summary
            else:
                final_summary = summaries[0] if summaries else "Could not generate summary."
            
            # Translate summary back to target language if needed
            if summary_lang != 'en' and summary_lang != detected_lang:
                final_summary = self.translate_text(final_summary, target_lang=summary_lang, source_lang='en')
            elif summary_lang != 'en' and detected_lang != 'en':
                final_summary = self.translate_text(final_summary, target_lang=summary_lang, source_lang='en')
            
            # Calculate metrics
            original_word_count = len(text.split())
            summary_word_count = len(final_summary.split())
            compression_ratio = (original_word_count - summary_word_count) / original_word_count if original_word_count > 0 else 0
            
            return {
                "summary": final_summary,
                "original_length": original_word_count,
                "summary_length": summary_word_count,
                "compression_ratio": round(compression_ratio * 100, 1),
                "detected_language": detected_lang,
                "language_name": lang_name,
                "target_language": summary_lang,
                "target_language_name": self.supported_languages.get(summary_lang, "Unknown")
            }
            
        except Exception as e:
            print(f"Error in summarization: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "original_length": len(text.split()) if text else 0,
                "summary_length": 0,
                "compression_ratio": 0,
                "detected_language": "en",
                "language_name": "English"
            }
    
    def extract_key_points(self, text, num_points=5, target_language=None):
        """Extract key points from the text with language support"""
        try:
            sentences = sent_tokenize(text)
            if len(sentences) <= num_points:
                key_points = sentences
            else:
                # Simple extractive approach - take sentences from different parts of the text
                step = len(sentences) // num_points
                key_points = []
                
                for i in range(0, len(sentences), step):
                    if len(key_points) < num_points and i < len(sentences):
                        key_points.append(sentences[i])
            
            # Translate key points if target language is specified
            if target_language and target_language != 'en':
                detected_lang = self.detect_language(text)
                if detected_lang != target_language:
                    translated_points = []
                    for point in key_points:
                        translated_point = self.translate_text(point, target_lang=target_language, source_lang=detected_lang)
                        translated_points.append(translated_point)
                    key_points = translated_points
            
            return key_points
            
        except Exception as e:
            print(f"Error extracting key points: {e}")
            return ["Could not extract key points."]
    
    def get_supported_languages(self):
        """Return list of supported languages"""
        return self.supported_languages

# Create a global instance (optional, for easier importing)
note_summarizer = NoteSummarizer()