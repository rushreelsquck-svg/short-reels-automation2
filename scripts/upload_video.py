"""
upload_video.py
Uploads the finished MP4 to YouTube as a Short using a stored refresh token
(no browser/interactive login needed — this is what lets it run unattended
inside GitHub Actions).
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_authenticated_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload_short(video_path: str, title: str, description: str, tags: list[str]) -> str:
    youtube = _get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": os.environ.get("YT_CATEGORY_ID", "25"),  # 25 = News & Politics
        },
        "status": {
            "privacyStatus": os.environ.get("YT_PRIVACY_STATUS", "unlisted"),
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python upload_video.py /path/to/video.mp4")
        sys.exit(1)

    upload_short(
        video_path=sys.argv[1],
        title="Test upload from trend-shorts-bot",
        description="This is a test upload. Safe to delete.",
        tags=["test"],
    )
