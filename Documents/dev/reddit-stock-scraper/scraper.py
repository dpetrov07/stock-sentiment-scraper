from dotenv import load_dotenv
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import os
import praw
import re
import string

TICKER_TO_NAME = {
    "AAPL": "Apple",
    "AMD": "Advanced Micro Devices",
    "AMZN": "Amazon",
    "GOOG": "Google",
    "META": "Facebook",
    "NVDA": "Nvidia",
    "SMCI": "Super Micro Computer",
    "SPOT": "Spotify",
    "TSLA": "Tesla"
}
STOCK_KEYWORDS = set(TICKER_TO_NAME.keys()) | set(name.upper() for name in TICKER_TO_NAME.values())
TARGET_SUBREDDITS = {"stocks", "investing"}

# Retrieves Reddit API
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)
print(reddit)

def pre_clean_text(text):
    # Remove newlines and non breaking spaces
    text = text.replace('\n', ' ').replace('\xa0', ' ')
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+|\S+\.com\b', '', text)
    # Minimize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Cleans sentence of any non alpha characters
def get_clean_sentence(sentence):
    # List of emoji types
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
    cleaned_sentence = []
    
    for word in sentence.split():
        word = word.lower()
        # Remove stopwords
        if word in ENGLISH_STOP_WORDS:
            continue
        # Remove digits
        word = "".join(char for char in word if not char.isdigit())
        # Remove punctuation
        word = "".join(char for char in word if char not in string.punctuation)
        # Remove emojis
        word = emoji_pattern.sub("", word)
        if word:
            cleaned_sentence.append(word)
    return cleaned_sentence

# Gets any posts with targeted ticker in title or post description
def collect_texts(target_subreddits, tickers):
    raw_texts = []
    for target_subreddit in target_subreddits:
        subreddit = reddit.subreddit(target_subreddit) 
        submissions = list(subreddit.hot(limit=30))

        # Adds submission text only if targeted ticker found
        for submission in submissions:
            title = submission.title
            description_text = getattr(submission, "selftext", "")
            title_description_text = f"{title} {description_text}"
            words = re.findall(r"\b\w+\b", title_description_text)
            # Adds top level comments of post if ticker found
            if any(word.upper() in tickers for word in words):
                if title:
                    raw_texts.append(pre_clean_text(title))
                if description_text:
                    raw_texts.append(pre_clean_text(description_text))
                for comment in submission.comments:
                    raw_texts.append(pre_clean_text(comment.body))
    return raw_texts

def get_ticker_sentences(texts, tickers, max_sentence_length=30, window=7):
    ticker_sentences = []
    # Groups into sentences and words in each
    for text in texts:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        for sentence in sentences:
            words = re.findall(r"\b\w+\b", sentence)
            # Filters sentences with stock tickers found
            for ticker in tickers:
                if any(word.upper() == ticker for word in words):
                    if len(words) <= max_sentence_length:
                        ticker_sentences.append(get_clean_sentence(sentence))
                # Filters for stock ticker in longer sentences
                else:
                    ticker_indexes = [i for i, word in enumerate(words) 
                                            if word.upper() == ticker]
                    # Extract words around ticker and extra words at end
                    for index in ticker_indexes:
                        start = max(0, index - window)
                        end = min(len(words), index + window + 5)
                        ticker_context = " ".join(words[start:end])
                        ticker_sentences.append(get_clean_sentence(ticker_context))
    return ticker_sentences

subreddit_texts = collect_texts(TARGET_SUBREDDITS, STOCK_KEYWORDS)
# print(subreddit_texts)
ticker_sentences = get_ticker_sentences(subreddit_texts, STOCK_KEYWORDS)
print(ticker_sentences)
