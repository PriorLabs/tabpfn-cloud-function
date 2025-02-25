import os
import pandas as pd
import numpy as np
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, EasterMonday, Easter
from pandas.tseries.offsets import Day
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define French holidays
class FrenchHolidayCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday('New Years Day', month=1, day=1),
        EasterMonday,
        Holiday('Labour Day', month=5, day=1),
        Holiday('Victory in Europe Day', month=5, day=8),
        Holiday('Ascension Day', month=1, day=1, offset=[Easter(), Day(39)]),
        Holiday('Bastille Day', month=7, day=14),
        Holiday('Assumption Day', month=8, day=15),
        Holiday('All Saints Day', month=11, day=1),
        Holiday('Armistice Day', month=11, day=11),
        Holiday('Christmas Day', month=12, day=25)
    ]

def preprocess_text(text):
    """Basic text preprocessing for transaction descriptions."""
    if pd.isna(text):
        return ""
    # Convert to lowercase and remove special characters
    text = str(text).lower()
    # Keep only alphanumeric and spaces
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    return text

def preprocess_data(df: pd.DataFrame, transformers=None, is_training: bool = False) -> pd.DataFrame:
    """Main preprocessing pipeline that works for both training and prediction.
    
    Args:
        df: Input DataFrame
        transformers: Dictionary containing 'scaler', 'tfidf', and 'pca' transformers
        is_training: Whether this is training data (with category) or prediction data
    """
    logger.info(f"Starting preprocessing with {'training' if is_training else 'prediction'} mode")
    df = df.copy()
    
    # Handle missing values and categories
    if is_training:
        df = df.dropna(subset=['category'])
    
    # Standardize column names
    if 'dateOp' in df.columns:
        df['dateop'] = df['dateOp']
    
    # Fill missing transaction descriptions with empty string
    df['transaction_description'] = df['transaction_description'].fillna('')
    
    # Preprocess transaction descriptions
    logger.info("Preprocessing transaction descriptions")
    df['transaction_description'] = df['transaction_description'].apply(preprocess_text)
    
    # Convert amount to float (handle comma decimal separator)
    df['amount'] = df['amount'].astype(str).str.replace(',', '.').astype(float)
    
    # Basic feature engineering
    try:
        # Try DD/MM/YYYY format first
        df['dateop'] = pd.to_datetime(df['dateop'], format='%d/%m/%Y')
    except ValueError:
        # Then try ISO format
        df['dateop'] = pd.to_datetime(df['dateop'])
    
    # Date-based features
    df['month'] = df['dateop'].dt.month
    df['day_of_week'] = df['dateop'].dt.dayofweek
    
    # Business day feature
    cal = FrenchHolidayCalendar()
    holidays = cal.holidays(start=df['dateop'].min(), end=df['dateop'].max())
    df['is_business_day'] = (
        (df['dateop'].dt.dayofweek < 5) &  # Monday = 0, Sunday = 6
        ~df['dateop'].isin(holidays)
    ).astype(int)
    
    # Transaction amount features
    df['is_credit'] = (df['amount'] > 0).astype(int)
    df['absolute_amount'] = df['amount'].abs()
    
    # Create base features DataFrame
    features = pd.DataFrame({
        'amount': df['amount'],
        'absolute_amount': df['absolute_amount'],
        'day_of_week': df['day_of_week'],
        'month': df['month'],
        'is_business_day': df['is_business_day'],
        'is_credit': df['is_credit']
    })
    
    # Apply transformers if available
    if transformers is not None:
        logger.info("Applying transformers")
        try:
            # Scale numerical features if scaler exists
            if 'scaler' in transformers:
                logger.info("Scaling numerical features")
                numerical_features = ['amount', 'absolute_amount']
                features[numerical_features] = transformers['scaler'].transform(features[numerical_features])
            
            # Process text features if text transformers exist
            if all(k in transformers for k in ['tfidf', 'pca']):
                logger.info("Generating text embeddings")
                text_features = transformers['tfidf'].transform(df['transaction_description'])
                text_embeddings = transformers['pca'].transform(text_features.toarray())
                
                # Add text embeddings to features
                for i in range(text_embeddings.shape[1]):
                    features[f'desc_emb_{i}'] = text_embeddings[:, i]
        except Exception as e:
            logger.error(f"Error applying transformers: {str(e)}")
            raise
    
    logger.info(f"Preprocessing complete. Features shape: {features.shape}")
    return features 