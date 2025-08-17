from dotenv import load_dotenv
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import os
import praw
import re
import string

# 
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

def clean_word(word):
    
    word = word.lower()
    
    # Remove stopwords
    if word in ENGLISH_STOP_WORDS:
        return ""
    
    # Remove digits
    word = "".join(char for char in word if not char.isdigit())
    
    # Remove punctuation
    word = "".join(char for char in word if char not in string.punctuation)
    
    # Remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    
    # Remove URLs
    if "http" in word or "www" in word or ".com" in word:
        return ""
    
    word = emoji_pattern.sub("", word)
    
    return word

def get_subreddit_words():
    word_collection = []
    subreddit = reddit.subreddit("stocks")
    submissions = subreddit.hot(limit=10)
    
    # Retrieves all title words for submissions
    for submission in submissions:
        title_words = submission.title.split()
        word_collection.extend(title_words)
        
        # Retrieves all comment words for submission
        for comment in submission.comments:
            comment_words = comment.body.split()
            word_collection.extend(comment_words)

    cleaned_words = []
    for word in word_collection:
        word = clean_word(word)
        if 1 < len(word) < 20:
            cleaned_words.append(word)

    return cleaned_words
    
print(get_subreddit_words())