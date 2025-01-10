import instaloader
import streamlit as st
import pandas as pd
import re
from yt_dlp import YoutubeDL

import streamlit as st
import pandas as pd
from pandas.core.frame import DataFrame
from youtube_comment_downloader import *
import io



def load_excel(file):

    return pd.read_excel(file, header=2)


def extract_instagram_shortcode(url):

    try:

        match = re.search(r"instagram\.com/(?:reel|p|tv)/([^/]+)/", url)
        shortcode = match.group(1) if match else None
        st.write(f"Extracted shortcode: {shortcode}")  # Debug line
        return shortcode

    except Exception as e:
        st.error(f"Error extracting shortcode: {e}")
        return None
    
def fetch_instagram_data(shortcode):

    try:

        L = instaloader.Instaloader(max_connection_attempts=1)
        
        
        # L.login('8806088337', 'Akash@14')
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        likes = post.likes
        print("likes of reel:",likes)
        comments_count = post.comments
        print("comments_count of reel:",comments_count)
        
        # for comment in post.get_comments():
        #     print(f"Comment: {comment.text}")
            
            
        # views = post.video_view_count if post.is_video else 0
        views_1 = post.video_play_count if post.is_video else 0
        # print("views of reel:",views)
        print("views_1 of reel:",views_1)
        # st.write(f"Views of Instagram post: {views}")
        
        # st.write(f"Likes: {likes}")
        # st.write(f"Comments Count: {comments_count}")
        
 

        total_view_count =  views_1
        
        print("total_engagement:",total_view_count)



        return {

            "Total Reach": post.owner_profile.followers,

            "Total Views": total_view_count,

            "Total Likes": likes,

            "Total Comments": comments_count,

        }

    except Exception as e:
        st.error(f"Error fetching data for shortcode {shortcode}: {e}")
        return {

            "Total Reach": "",
            "Total Views": "",
            "Total Likes": "",
            "Total Comments": "",

        }



def fetch_youtube_data(url):

    try:

        ydl_opts = {

            "quiet": True,

            "no_warnings": True,

            "simulate": True,

        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)


        total_engagement = info['view_count']



        return {

            "Total Reach": info['view_count'],
            "Total Views": total_engagement,
            "Total Likes": info['like_count'],
            "Total Comments": info['comment_count'],

        }

    except Exception as e:

        st.error(f"Error fetching YouTube data for URL {url}: {e}")

        return {

            "Total Reach": "",
            "Total Views": "",
            "Total Likes": "",
            "Total Comments": "",

        }
        
def main():

    st.title("📊 Social Media Engagement Tracker")

    st.markdown("Upload an Excel file with social media links to fetch real-time engagement metrics.")



    st.sidebar.header("Instructions")

    st.sidebar.info("1. Ensure the file has a column named 'Platform/ Go Live Link'.\n"

                    "2. Upload the file and press 'Fetch Data'.\n"

                    "3. Download results as a CSV file.")



    uploaded_file = st.file_uploader("Upload your Excel File", type="xlsx")

    if uploaded_file:

        df = load_excel(uploaded_file)

        st.success("File uploaded successfully!")

        st.write("**Uploaded Data:**")

        st.dataframe(df)



        if "Platform/ Go Live Link" not in df.columns:

            st.error("The uploaded Excel file must have a 'Platform/ Go Live Link' column.")

            return



        if st.button("🔄 Fetch Engagement Data"):

            with st.spinner("Fetching engagement data..."):

                results = []
                total_reach_instagram = 0
                total_engagement_instagram = 0
                total_likes_instagram = 0
                total_comments_instagram = 0



                total_reach_youtube = 0
                total_engagement_youtube = 0
                total_likes_youtube = 0
                total_comments_youtube = 0



                for _, row in df.iterrows():

                    link = row.get("Platform/ Go Live Link", "")
                    influencer_name = row.get("Influencer Name", "")

                    if isinstance(link, str) and link:
                        if "instagram.com" in link:
                            shortcode = extract_instagram_shortcode(link)
                            if shortcode:
                                engagement_data = fetch_instagram_data(shortcode)                           
                                total_reach_instagram += engagement_data["Total Reach"] if isinstance(engagement_data["Total Reach"], int) else 0
                                total_engagement_instagram += engagement_data["Total Views"] if isinstance(engagement_data["Total Views"], int) else 0
                                total_likes_instagram += engagement_data["Total Likes"] if isinstance(engagement_data["Total Likes"], int) else 0
                                total_comments_instagram += engagement_data["Total Comments"] if isinstance(engagement_data["Total Comments"], int) else 0
                                print("++++++")
                                print("Engae:",engagement_data)
                            else:

                                engagement_data = {

                                    "Total followers": "",

                                    "Total Views": "",

                                    "Total Likes": "",

                                    "Total Comments": "",

                                }

                        elif "youtube.com" in link or "youtu.be" in link:

                            engagement_data = fetch_youtube_data(link)

                            total_reach_youtube += engagement_data["Total Reach"] if isinstance(engagement_data["Total Reach"], int) else 0

                            total_engagement_youtube += engagement_data["Total Views"] if isinstance(engagement_data["Total Views"], int) else 0

                            total_likes_youtube += engagement_data["Total Likes"] if isinstance(engagement_data["Total Likes"], int) else 0

                            total_comments_youtube += engagement_data["Total Comments"] if isinstance(engagement_data["Total Comments"], int) else 0

                        else:

                            engagement_data = {

                                "Total Reach": "",

                                "Total Views": "",

                                "Total Likes": "",

                                "Total Comments": "",

                            }

                    else:

                        engagement_data = {

                            "Total Reach": "",

                            "Total Views": "",

                            "Total Likes": "",

                            "Total Comments": "",

                        }



                    # Calculate Engagement Rate and add to the results

                    if engagement_data["Total Reach"] != "" and engagement_data["Total Reach"] > 0:

                        engagement_rate = (engagement_data["Total Views"] / engagement_data["Total Reach"]) * 100

                    else:

                        engagement_rate = ""



                    # Add the influencer name and engagement data to the results
                    
                    

                    results.append({

                        "Influencer Name": influencer_name,

                        "Platform/ Go Live Link": link,

                        **engagement_data,

                        # "Engagement Rate": engagement_rate

                    })



                result_df = pd.DataFrame(results)

                st.success("Engagement data fetched successfully!")

                st.write("**Engagement Data:**")

                st.dataframe(result_df)



                totals = {

                    "Influencer Name": "Totals",

                    "Platform/ Go Live Link": "Totals",

                    "Total Reach": total_reach_instagram + total_reach_youtube,

                    "Total Views": total_engagement_instagram + total_engagement_youtube,

                    "Total Likes": total_likes_instagram + total_likes_youtube,

                    "Total Comments": total_comments_instagram + total_comments_youtube,

                    "Engagement Rate": "",

                }



                # Convert totals dictionary to a DataFrame and concatenate

                totals_df = pd.DataFrame([totals])

                result_df = pd.concat([result_df, totals_df], ignore_index=True)



                # Generate CSV for download

                csv = result_df.to_csv(index=False)

                st.download_button(

                    label="📥 Download Data as CSV",

                    data=csv,

                    file_name="engagement_data.csv",

                    mime="text/csv",

                )



if __name__ == "__main__":

    main()



            