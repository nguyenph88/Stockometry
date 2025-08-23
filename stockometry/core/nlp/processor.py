# src/nlp/processor.py
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from ...database import get_db_connection
import time

class NLPProcessor:
    """
    A singleton class to handle NLP processing to avoid reloading models.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Initializing NLP models...")
            cls._instance = super(NLPProcessor, cls).__new__(cls)
            
            try:
                # Load spaCy for Named Entity Recognition (NER)
                # Using disable=['parser', 'lemmatizer'] for faster loading as we only need NER
                cls._instance.nlp = spacy.load("en_core_web_sm", disable=['parser', 'lemmatizer'])
                print("spaCy model loaded successfully.")
            except Exception as e:
                print(f"Warning: Failed to load spaCy model: {e}")
                cls._instance.nlp = None
            
            try:
                # Load FinBERT for financial sentiment analysis
                model_name = "ProsusAI/finbert"
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                cls._instance.sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
                print("FinBERT sentiment model loaded successfully.")
            except Exception as e:
                print(f"Warning: Failed to load FinBERT model: {e}")
                cls._instance.sentiment_pipeline = None
            
            print("NLP models initialization completed.")
        return cls._instance

    def analyze_text(self, text: str):
        """
        Analyzes a piece of text for sentiment and named entities.
        """
        if not text or not isinstance(text, str):
            return {"sentiment": None, "entities": []}
        
        # 1. Sentiment Analysis
        sentiment = None
        if self.sentiment_pipeline:
            try:
                sentiment_result = self.sentiment_pipeline(text)[0]
                sentiment = {"label": sentiment_result['label'], "score": round(sentiment_result['score'], 4)}
            except Exception as e:
                print(f"Warning: Sentiment analysis failed: {e}")
                sentiment = {"label": "NEUTRAL", "score": 0.5}
        else:
            sentiment = {"label": "NEUTRAL", "score": 0.5}
        
        # 2. Named Entity Recognition
        entities = []
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    # We are interested in organizations, people, geopolitical entities, etc.
                    if ent.label_ in ['ORG', 'PERSON', 'GPE', 'MONEY', 'PRODUCT']:
                        entities.append({'text': ent.text, 'label': ent.label_})
            except Exception as e:
                print(f"Warning: NER analysis failed: {e}")
        else:
            # Fallback: simple entity extraction
            words = text.split()
            for word in words:
                if word.isupper() and len(word) > 2:
                    entities.append({'text': word, 'label': 'ORG'})
                
        return {
            "sentiment": sentiment,
            "entities": entities
        }

def process_articles_and_store_features():
    """
    Fetches unprocessed articles from the DB, analyzes them, and stores the features.
    """
    print("Starting NLP processing for unprocessed articles...")
    processor = NLPProcessor()
    
    # Add a new column to the articles table for NLP features, if it doesn't exist
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Use JSONB for efficient storage and querying of JSON data
                cursor.execute("""
                    ALTER TABLE articles ADD COLUMN IF NOT EXISTS nlp_features JSONB;
                """)
            conn.commit()
    except Exception as e:
        print(f"Error altering table: {e}")
        return

    # Fetch articles that haven't been processed yet
    fetch_query = "SELECT id, title, description FROM articles WHERE nlp_features IS NULL LIMIT 100;"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(fetch_query)
                articles_to_process = cursor.fetchall()

        if not articles_to_process:
            print("No new articles to process.")
            return

        print(f"Found {len(articles_to_process)} articles to process.")
        
        processed_count = 0
        start_time = time.time()

        for article_id, title, description in articles_to_process:
            # Combine title and description for a richer analysis
            text_to_analyze = (title or "") + ". " + (description or "")
            
            if not text_to_analyze.strip() or text_to_analyze == ". ":
                continue

            features = processor.analyze_text(text_to_analyze)
            
            # Store the features back in the database
            import json
            update_query = "UPDATE articles SET nlp_features = %s WHERE id = %s;"
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_query, (json.dumps(features), article_id))
                conn.commit()
            processed_count += 1

        end_time = time.time()
        print(f"Successfully processed {processed_count} articles in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        print(f"An error occurred during article processing: {e}")


if __name__ == '__main__':
    process_articles_and_store_features()
