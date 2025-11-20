import praw
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def get_reddit_sentiment(ticker):
    reddit = praw.Reddit(client_id='YOUR_ID', client_secret='YOUR_SECRET', user_agent='DCF_App')
    sia = SentimentIntensityAnalyzer()
    
    posts = reddit.subreddit('stocks+investing+wallstreetbets').search(ticker, limit=50)
    scores = []
    
    for post in posts:
        # Combine title and top comment
        text = post.title + " " + (post.selftext[:200] if post.selftext else "")
        score = sia.polarity_scores(text)['compound']
        scores.append(score)
        
    avg_score = sum(scores) / len(scores) if scores else 0
    return avg_score # Returns float between -1 (Negative) and 1 (Positive)