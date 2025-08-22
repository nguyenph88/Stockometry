# src/nlp/processor.py
"""
NLP processor for the Stock Analysis Bot.
This module processes articles to extract sentiment and entity information.
"""

import json
from src.database import get_db_connection

def process_articles_and_store_features():
    """
    Processes articles that don't have NLP features yet.
    Extracts sentiment and entities, then stores the results back to the database.
    """
    print("Starting NLP processing of articles...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Find articles without NLP features
                cursor.execute("""
                    SELECT id, title, description 
                    FROM articles 
                    WHERE nlp_features IS NULL 
                    AND title IS NOT NULL
                    LIMIT 100;
                """)
                
                articles = cursor.fetchall()
                
                if not articles:
                    print("No articles found that need NLP processing.")
                    return
                
                print(f"Found {len(articles)} articles to process...")
                
                for article_id, title, description in articles:
                    # Simple NLP processing (placeholder implementation)
                    # In a real implementation, this would use proper NLP libraries
                    nlp_features = _extract_nlp_features(title, description)
                    
                    # Update the article with NLP features
                    cursor.execute("""
                        UPDATE articles 
                        SET nlp_features = %s 
                        WHERE id = %s
                    """, (json.dumps(nlp_features), article_id))
                
                conn.commit()
                print(f"Successfully processed {len(articles)} articles.")
                
    except Exception as e:
        print(f"Error during NLP processing: {e}")
        raise

def _extract_nlp_features(title, description):
    """
    Extracts NLP features from article title and description.
    This is a simplified implementation for testing purposes.
    """
    text = f"{title} {description}".lower()
    
    # Simple sentiment analysis based on keywords
    positive_words = ['profit', 'surge', 'gain', 'positive', 'growth', 'success', 'record', 'stellar']
    negative_words = ['tumble', 'plummet', 'fear', 'concern', 'tariff', 'regulation', 'recall', 'fail']
    
    positive_score = sum(1 for word in positive_words if word in text)
    negative_score = sum(1 for word in negative_words if word in text)
    
    # Determine sentiment label and score
    if positive_score > negative_score:
        sentiment = {"label": "positive", "score": 0.8}
    elif negative_score > positive_score:
        sentiment = {"label": "negative", "score": 0.8}
    else:
        sentiment = {"label": "neutral", "score": 0.5}
    
    # Simple entity extraction (company names)
    entities = []
    company_keywords = ['nvda', 'nvidia', 'apple', 'microsoft', 'amazon', 'google', 'tesla', 'ford', 'boeing']
    
    for company in company_keywords:
        if company in text:
            entities.append({"text": company.title(), "label": "ORG"})
    
    return {
        "sentiment": sentiment,
        "entities": entities
    }