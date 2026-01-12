#
# pip3 install python-wordpress-xmlrpc google-auth google-auth-oauthlib google-api-python-client python-dotenv requests schedule feedparser
# .env files
"""
MEDIUM_RSS_URL=https://medium.com/feed/@yourusername
WORDPRESS_URL=https://your-wordpress-site.com/xmlrpc.php
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_PASSWORD=your_wordpress_password
BLOGSPOT_BLOG_ID=your_blogspot_blog_id
GOOGLE_CREDENTIALS_FILE=/path/to/your/client_secret.json
"""

import os, json, logging, time, schedule, hashlib, pickle, requests, feedparser
from datetime import datetime, timedelta
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts, EditPost
from wordpress_xmlrpc.methods.media import UploadFile
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
from io import BytesIO

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging
log_file = os.path.join(script_dir, 'medium_transfer.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(os.path.join(script_dir, '.env'))

# Cache file path
CACHE_FILE = os.path.join(script_dir, 'posted_ids.json')

# OAuth 2.0 authentication function for Blogger
def get_blogger_credentials():
    creds = None
    pickle_file = os.path.join(script_dir, 'token.pickle')
    google_credentials_file = os.path.join(script_dir, os.getenv('GOOGLE_CREDENTIALS_FILE'))
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                google_credentials_file,
                scopes=['https://www.googleapis.com/auth/blogger'])
            creds = flow.run_local_server(port=0)
        with open(pickle_file, 'wb') as token:
            pickle.dump(creds, token)
    return creds

# Load posted IDs
def load_posted_ids():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            return {k: set(v) for k, v in data.items()}
    return {'wordpress': set(), 'blogspot': set()}

# Save posted IDs
def save_posted_ids(posted_ids):
    with open(CACHE_FILE, 'w') as f:
        json.dump({k: list(v) for k, v in posted_ids.items()}, f)

# WordPress posting function
def post_to_wordpress(wp_client, title, content, image_url, original_id):
    # Check if the post already exists
    existing_posts = wp_client.call(GetPosts({'meta_key': 'original_id', 'meta_value': original_id}))

    if existing_posts:
        # Update existing post
        post = existing_posts[0]
        post.title = title
        post.content = content
    else:
        # Create new post
        post = WordPressPost()
        post.title = title
        post.content = content
        post.post_status = 'publish'

    # Set custom field for original_id
    post.custom_fields = []
    post.custom_fields.append({
        'key': 'original_id',
        'value': original_id
    })

    # Upload image
    if image_url:
        img_data = requests.get(image_url).content
        filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        data = {
            'name': filename,
            'type': 'image/jpeg',
            'bits': BytesIO(img_data)
        }
        response = wp_client.call(UploadFile(data))
        attachment_id = response['id']
        post.thumbnail = attachment_id

    if existing_posts:
        # Update existing post
        post_id = wp_client.call(EditPost(post.id, post))
        logging.info(f"Updated WordPress post: {title} (ID: {post.id})")
    else:
        # Create new post
        post_id = wp_client.call(NewPost(post))
        logging.info(f"Created new WordPress post: {title} (ID: {post_id})")

    return post_id

# Blogspot posting function
def post_to_blogspot(service, blog_id, title, content, image_url, original_id):
    try:
        # Fetch all posts
        posts = service.posts().list(blogId=blog_id).execute()

        existing_post = None
        for post in posts.get('items', []):
            if f'original_id_{original_id}' in post.get('labels', []):
                existing_post = post
                break

        if existing_post:
            # Update existing post
            if image_url:
                content = f'<img src="{image_url}" /><br/>{content}'

            body = {
                'title': title,
                'content': content,
                'labels': existing_post.get('labels', [])
            }

            updated_post = service.posts().update(
                blogId=blog_id,
                postId=existing_post['id'],
                body=body
            ).execute()
            logging.info(f"Updated Blogspot post: {title} (ID: {updated_post['id']})")
            return updated_post['id']
        else:
            # Create new post
            if image_url:
                content = f'<img src="{image_url}" /><br/>{content}'

            body = {
                "kind": "blogger#post",
                "title": title,
                "content": content,
                "labels": [f"original_id_{original_id}"]
            }

            new_post = service.posts().insert(blogId=blog_id, body=body).execute()
            logging.info(f"Created new Blogspot post: {title} (ID: {new_post['id']})")
            return new_post['id']

    except Exception as e:
        logging.error(f"Error posting to Blogspot: {e}")
        return None

# Function to fetch new content
def fetch_new_content():
    # RSS feed URL
    rss_url = os.getenv('MEDIUM_RSS_URL')

    # Parse the RSS feed
    feed = feedparser.parse(rss_url)

    # Get the current time
    now = datetime.now()

    # List to store new posts
    new_posts = []

    for entry in feed.entries:
        # Parse the published date
        published = datetime(*entry.published_parsed[:6])

        # Check if the post is newer than 24 hours
        if now - published < timedelta(hours=24):
            # Generate a unique ID for the post
            unique_id = hashlib.md5(entry.link.encode()).hexdigest()

            # Extract the image URL if available
            image_url = None
            if 'media_content' in entry:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image'):
                        image_url = media.get('url')
                        break

            # Create a post dictionary
            post = {
                'id': unique_id,
                'title': entry.title,
                'content': entry.summary,
                'image_url': image_url,
                'link': entry.link,
                'published': published.isoformat()
            }

            new_posts.append(post)

    return new_posts

# Main function to process new posts
def process_new_posts():
    # Load configuration
    wp_url = os.getenv('WORDPRESS_URL')
    wp_username = os.getenv('WORDPRESS_USERNAME')
    wp_password = os.getenv('WORDPRESS_PASSWORD')
    blogspot_blog_id = os.getenv('BLOGSPOT_BLOG_ID')

    # Initialize clients
    wp_client = Client(wp_url, wp_username, wp_password)
    blogger_creds = get_blogger_credentials()
    blogger_service = build('blogger', 'v3', credentials=blogger_creds)

    # Load posted IDs
    posted_ids = load_posted_ids()

    # Fetch new content
    new_posts = fetch_new_content()

    for post in new_posts:
        wp_post_id = post_to_wordpress(wp_client, post['title'], post['content'], post['image_url'], post['id'])
        if wp_post_id:
            posted_ids['wordpress'].add(post['id'])

        blogspot_post_id = post_to_blogspot(blogger_service, blogspot_blog_id, post['title'], post['content'], post['image_url'], post['id'])
        if blogspot_post_id:
            posted_ids['blogspot'].add(post['id'])

    # Save posted IDs
    save_posted_ids(posted_ids)

    logging.info("Completed processing new posts")

if __name__ == '__main__':
    logging.info("Starting media transfer script")

    # process_new_posts()

    # Schedule the job to run every 15 minutes
    schedule.every(15).minutes.do(process_new_posts)
    while True:
        schedule.run_pending()
        time.sleep(1)
