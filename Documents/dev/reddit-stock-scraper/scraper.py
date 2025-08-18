from constants import STOCK_KEYWORDS, TARGET_SUBREDDITS, TICKERS_MAP
from dotenv import load_dotenv
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import praw
import re
import string

# Retrieves Reddit API
load_dotenv()
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Cleans new lines, links and other generated characters
def pre_clean_text(text):
    text = text.replace('\n', ' ').replace('\xa0', ' ')
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+|\S+\.com\b', '', text)
    # Minimize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Cleans sentence more fully of any non alpha characters
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

# Retrieves all sentences with relevant stock mentions
def get_ticker_sentences(texts, tickers, max_sentence_length=30, window=5):
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
                            end = min(len(words), index + window + 1)
                            ticker_context = " ".join(words[start:end])
                            ticker_sentences.append(get_clean_sentence(ticker_context))
    return ticker_sentences

# Retrieves score sentiments for all mentioned stocks
def get_score_sentiment(ticker_sentences, tickers_map):
    analyzer = SentimentIntensityAnalyzer()
    # Maps names to tickers
    ticker_names_map = {v.upper(): k for k, v in tickers_map.items()}
    # Creates dictionary to store sentiment scores
    stock_sentiments = {ticker: [] for ticker in tickers_map}

    # Retrieve sentiment scores
    for sentence in ticker_sentences:
        sentence_string = " ".join(sentence)
        sentiment_score = analyzer.polarity_scores(sentence_string)["compound"]

        # Find relevant stock of sentence
        for word in sentence_string.upper().split():
            if word in tickers_map:
                stock_sentiments[word].append(sentiment_score)
            elif word in ticker_names_map:
                stock_sentiments[ticker_names_map[word]].append(sentiment_score)

    # Retrieve sentiment score for each targeted stock
    for ticker, scores in stock_sentiments.items():
        if scores:
            average_score = sum(scores) / len(scores)
            print(f"{ticker} ({tickers_map[ticker]}): {average_score:.3f}")
        else:
            print(f"{ticker} ({tickers_map[ticker]}): No data found")

subreddit_texts = collect_texts(TARGET_SUBREDDITS, STOCK_KEYWORDS)
ticker_sentences = get_ticker_sentences(subreddit_texts, STOCK_KEYWORDS)
get_score_sentiment(ticker_sentences, TICKERS_MAP)
