# src/nlp/processor.py
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from src.database import get_db_connection
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
            
            # Load spaCy for Named Entity Recognition (NER)
            # Using disable=['parser', 'lemmatizer'] for faster loading as we only need NER
            cls._instance.nlp = spacy.load("en_core_web_sm", disable=['parser', 'lemmatizer'])
            
            # Load FinBERT for financial sentiment analysis
            model_name = "ProsusAI/finbert"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            cls._instance.sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
            print("NLP models loaded successfully.")
        return cls._instance

    def analyze_text(self, text: str):
        """
        Analyzes a piece of text for sentiment and named entities.
        """
        if not text or not isinstance(text, str):
            return {"sentiment": None, "entities": []}
            
        # 1. Sentiment Analysis
        sentiment = self.sentiment_pipeline(text)[0]
        
        # 2. Named Entity Recognition
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            # We are interested in organizations, people, geopolitical entities, etc.
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'MONEY', 'PRODUCT']:
                entities.append({'text': ent.text, 'label': ent.label_})
                
        return {
            "sentiment": {"label": sentiment['label'], "score": round(sentiment['score'], 4)},
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
