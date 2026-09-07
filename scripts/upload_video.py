import datetime
import os
import re
import unicodedata

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


def _build_status_body():
    privacy_status = os.environ.get("YT_PRIVACY_STATUS", "unlisted")
    if privacy_status == "scheduled":
        delay_hours = float(os.environ.get("YT_PUBLISH_DELAY_HOURS", "3"))
        publish_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=delay_hours)
        return {
            "privacyStatus": "private",
            "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "selfDeclaredMadeForKids": False,
        }
    return {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": False,
    }


def _sanitize_tags(tags: list[str]) -> list[str]:
    cleaned = []
    for tag in tags:
        tag = unicodedata.normalize("NFKD", str(tag))
        tag = re.sub(r'[^\x00-\x7F]', '', tag)
        tag = re.sub(r'[<>&"\'\`\#]', '', tag).strip()
        if tag and len(tag) <= 100:
            cleaned.append(tag)
    return cleaned


def upload_short(video_path: str, title: str, description: str, tags: list[str]) -> str:
    youtube = _get_authenticated_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": _sanitize_tags(tags),
            "categoryId": os.environ.get("YT_CATEGORY_ID", "25"),
        },
        "status": _build_status_body(),
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
    if "publishAt" in body["status"]:
        print(f"Scheduled to go public at: {body['status']['publishAt']}")
    return video_id


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python upload_video.py /path/to/video.mp4")
        sys.exit(1)
    upload_short(sys.argv[1], "Test upload", "Test description.", ["test"])
