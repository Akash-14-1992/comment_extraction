# import instaloader
import streamlit as st
import pandas as pd
import re
import torch
from transformers import pipeline
from yt_dlp import YoutubeDL
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

# Cached functions
@st.cache_resource
def load_sentiment_analyzer():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment", device=-1)

@st.cache_data
def load_excel(file):
    return pd.read_excel(file, header=2)

@st.cache_data
def youtube_url_to_df(Youtube_URL: str) -> pd.DataFrame:
    try:
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments_from_url(Youtube_URL, sort_by=SORT_BY_POPULAR)

        all_comments_dict = {
            'cid': [],
            'text': [],
            'time': [],
            'author': [],
            'channel': [],
            'votes': [],
            'replies': [],
            'photo': [],
            'heart': [],
            'reply': [],
            'time_parsed': []
        }

        for comment in comments:
            for key in all_comments_dict.keys():
                all_comments_dict[key].append(comment.get(key, ""))

        comments_df = pd.DataFrame(all_comments_dict)
        return comments_df

    except Exception as error:
        st.error(f"Error fetching comments for URL {Youtube_URL}: {error}")
        return pd.DataFrame()

def analyze_comments(df: pd.DataFrame, sentiment_analyzer):
    positive_count = []
    negative_count = []

    for comment in df['text']:
        try:
            sentiment = analyze_sentiment(comment, sentiment_analyzer)
            if sentiment in [4, 5]:
                positive_count.append(1)
                negative_count.append(0)
            elif sentiment in [1, 2]:
                positive_count.append(0)
                negative_count.append(1)
            else:
                positive_count.append(0)
                negative_count.append(0)
        except Exception:
            positive_count.append(0)
            negative_count.append(0)

    df["Positive YouTube Count"] = positive_count
    df["Negative YouTube Count"] = negative_count
    return df

def analyze_sentiment(text, sentiment_analyzer):
    max_length = sentiment_analyzer.tokenizer.model_max_length
    tokens = sentiment_analyzer.tokenizer.tokenize(text)
    if len(tokens) > max_length - 2:
        tokens = tokens[:(max_length - 2)]
    truncated_text = sentiment_analyzer.tokenizer.convert_tokens_to_string(tokens)
    result = sentiment_analyzer(truncated_text)
    return int(result[0]['label'].split()[0])

def extract_instagram_shortcode(url):
    try:
        match = re.search(r"instagram\.com/(?:reel|p|tv)/([^/]+)/", url)
        return match.group(1) if match else None
    except Exception as e:
        st.error(f"Error extracting shortcode: {e}")
        return None
    
    

def fetch_instagram_data(shortcode):
    try:
        L = instaloader.Instaloader(max_connection_attempts=1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        likes = post.likes
        comments_count = post.comments
        views = post.video_view_count if post.is_video else 0
        views_1 = post.video_play_count if post.is_video else 0
        total_engagement = likes + comments_count + views_1

        return {
            "Total Reach": post.owner_profile.followers,
            "Total Engagement + Views": total_engagement,
            "Total Likes": likes,
            "Total Comments": comments_count,
        }
    except Exception as e:
        st.error(f"Error fetching data for shortcode {shortcode}: {e}")
        return {
            "Total Reach": "",
            "Total Engagement + Views": "",
            "Total Likes": "",
            "Total Comments": "",
        }    

# Setup Remote WebDriver (BrowserStack Example)
def setup_driver():
    USERNAME = "akashgaikwad_TxQjpS"
    ACCESS_KEY = "5VySDyFwyxZ4U53mxCYx"
    REMOTE_URL = f"https://{USERNAME}:{ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"

    capabilities = {
        'browser': 'chrome',
        'browser_version': 'latest',
        'os': 'Windows',
        'os_version': '10',
        'name': 'My Streamlit App Test',
        'build': 'Streamlit Selenium Build 1',
    }

    driver = webdriver.Remote(
        command_executor=REMOTE_URL,
        desired_capabilities=capabilities
    )
    return driver

def scrape_instagram_comments(driver, shortcode):
    """Scrape comments from an Instagram post using Selenium."""
    url = f"https://www.instagram.com/p/{shortcode}/"
    driver.get(url)
    time.sleep(3)

    results = []

    while True:
        try:
            load_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View more comments')]"))
            )
            load_more_button.click()
            time.sleep(2)
        except TimeoutException:
            break

    comment_elements = driver.find_elements(By.XPATH, "//ul[contains(@class, '_a9ym')]//li")
    for comment in comment_elements:
        try:
            comment_text_element = comment.find_element(By.XPATH, ".//span")
            comment_text = comment_text_element.text
            if comment_text:
                results.append(comment_text)
        except Exception:
            continue

    return results


def analyze_instagram_comments(shortcode, sentiment_analyzer):
    """Analyze sentiments of Instagram comments."""
    driver = setup_driver()
    try:
        comments = scrape_instagram_comments(driver, shortcode)
        df = pd.DataFrame({'text': comments})
        df = analyze_comments(df, sentiment_analyzer)
        positive_count = df["Positive YouTube Count"].sum()
        negative_count = df["Negative YouTube Count"].sum()
        return positive_count, negative_count
    finally:
        driver.quit()

def fetch_instagram_data_with_sentiment(shortcode, sentiment_analyzer):
    """Fetch Instagram data along with sentiment analysis for comments."""
    engagement_data = fetch_instagram_data(shortcode)
    positive_count, negative_count = analyze_instagram_comments(shortcode, sentiment_analyzer)
    engagement_data["Total Positive Instagram Comments"] = positive_count
    engagement_data["Total Negative Instagram Comments"] = negative_count
    return engagement_data

def fetch_youtube_data(url):
    try:
        ydl_opts = {"quiet": True, "no_warnings": True, "simulate": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        total_engagement = info['like_count'] + info['comment_count'] + info['view_count']

        return {
            "Total Reach": info['view_count'],
            "Total Engagement + Views": total_engagement,
            "Total Likes": info['like_count'],
            "Total Comments": info['comment_count'],
        }
    except Exception as e:
        st.error(f"Error fetching YouTube data for URL {url}: {e}")
        return {
            "Total Reach": "",
            "Total Engagement + Views": "",
            "Total Likes": "",
            "Total Comments": "",
        }

def main():
    st.title("Social Media Engagement Tracker")
    st.markdown("Upload an Excel file with social media links to fetch real-time engagement metrics.")

    sentiment_analyzer = load_sentiment_analyzer()

    uploaded_file = st.file_uploader("Upload your Excel File", type="xlsx")

    if uploaded_file:
        df = load_excel(uploaded_file)
        st.success("File uploaded successfully!")
        st.write("**Uploaded Data:**")
        st.dataframe(df)

        if "Platform/ Go Live Link" not in df.columns:
            st.error("The uploaded Excel file must have a 'Platform/ Go Live Link' column.")
            return

        if st.button("Fetch Engagement Data"):
            with st.spinner("Fetching engagement data..."):
                results = []

                for _, row in df.iterrows():
                    link = row.get("Platform/ Go Live Link", "")
                    influencer_name = row.get("Influencer Name", "")

                    if isinstance(link, str) and link:
                        if "instagram.com" in link:
                            shortcode = extract_instagram_shortcode(link)
                            engagement_data = fetch_instagram_data_with_sentiment(shortcode, sentiment_analyzer) if shortcode else {}
                        elif "youtube.com" in link or "youtu.be" in link:
                            engagement_data = fetch_youtube_data(link)
                            comments_df = youtube_url_to_df(link)
                            if not comments_df.empty:
                                comments_df = analyze_comments(comments_df, sentiment_analyzer)
                                positive_comments = comments_df["Positive YouTube Count"].sum()
                                negative_comments = comments_df["Negative YouTube Count"].sum()
                                engagement_data["Total Positive YouTube Comments"] = positive_comments
                                engagement_data["Total Negative YouTube Comments"] = negative_comments
                            else:
                                engagement_data["Total Positive YouTube Comments"] = 0
                                engagement_data["Total Negative YouTube Comments"] = 0
                        else:
                            engagement_data = {}
                    else:
                        engagement_data = {}

                    results.append({
                        "Influencer Name": influencer_name,
                        "Platform/ Go Live Link": link,
                        **engagement_data
                    })

                result_df = pd.DataFrame(results)
                st.write("**Engagement Data:**")
                st.dataframe(result_df)
                
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name="engagement_data.csv",
                    mime="text/csv")

if __name__ == "__main__":
    main()
