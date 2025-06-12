import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
import torch

from src.preprocessing.data_preprocessor import fetch_courses_from_db, clean_course_data, feature_engineer_course_data
from src.utils.logging_utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

# Load pre-trained model and tokenizer for embeddings
# Using a small, efficient model for sentence embeddings
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

def get_sentence_embeddings(texts: list[str]) -> torch.Tensor:
    """Generates sentence embeddings for a list of texts using a pre-trained Transformer model."""
    logger.info("Generating sentence embeddings...")
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = model(**inputs)
    # Mean pooling to get sentence embeddings
    sentence_embeddings = mean_pooling(model_output, inputs['attention_mask'])
    logger.info("Embeddings generated.")
    return sentence_embeddings

def mean_pooling(model_output, attention_mask):
    """Performs mean pooling to get sentence embeddings."""
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def get_recommendations(course_id: int, courses_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Recommends similar courses based on content descriptions.

    Args:
        course_id: The ID of the course for which to find recommendations.
        courses_df: DataFrame containing processed course data with 'description' column.
        top_n: Number of top recommendations to return.

    Returns:
        A DataFrame of recommended courses.
    """
    logger.info(f"Generating {top_n} recommendations for course ID: {course_id}")

    if courses_df.empty or 'description' not in courses_df.columns:
        logger.error("Courses DataFrame is empty or missing 'description' column.")
        return pd.DataFrame()

    target_course = courses_df[courses_df['id'] == course_id]
    if target_course.empty:
        logger.warning(f"Course with ID {course_id} not found.")
        return pd.DataFrame()

    # Generate embeddings for all course descriptions
    all_descriptions = courses_df['description'].tolist()
    course_embeddings = get_sentence_embeddings(all_descriptions)

    # Get embedding for the target course
    target_course_index = target_course.index[0]
    target_embedding = course_embeddings[target_course_index].unsqueeze(0) # Add batch dimension

    # Calculate cosine similarity between target course and all other courses
    similarities = cosine_similarity(target_embedding, course_embeddings).flatten()

    # Create a Series of similarities, excluding the target course itself
    similarity_scores = pd.Series(similarities, index=courses_df.index)
    similarity_scores = similarity_scores.drop(target_course_index) # Exclude self

    # Sort by similarity and get top N recommendations
    top_recommendations_indices = similarity_scores.nlargest(top_n).index
    recommended_courses = courses_df.loc[top_recommendations_indices]

    logger.info(f"Recommendations generated for course ID {course_id}.")
    return recommended_courses

if __name__ == "__main__":
    logger.info("--- Recommendation Model Module ---")

    # 1. Fetch and preprocess data
    courses_df = fetch_courses_from_db()
    if courses_df is not None and not courses_df.empty:
        cleaned_df = clean_course_data(courses_df)
        # No need for feature_engineer_course_data for this model, as we use raw description for embeddings
        # featured_df = feature_engineer_course_data(cleaned_df)

        logger.info(f"Fetched and cleaned {len(cleaned_df)} courses.")

        # Example: Get recommendations for the first course in the DataFrame
        if not cleaned_df.empty:
            first_course_id = cleaned_df['id'].iloc[0]
            logger.info(f"Attempting to get recommendations for course ID: {first_course_id}")
            recommendations = get_recommendations(first_course_id, cleaned_df, top_n=3)

            if not recommendations.empty:
                logger.info(f"Top 3 recommendations for course ID {first_course_id}:\n{recommendations[['title', 'url']]}")
            else:
                logger.warning(f"No recommendations found for course ID {first_course_id}.")
        else:
            logger.warning("No courses available in the cleaned DataFrame to generate recommendations.")
    else:
        logger.error("Failed to fetch or preprocess course data. Cannot run recommendation model.") 