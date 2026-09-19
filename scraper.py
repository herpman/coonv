import os
import re
import cv2
from bs4 import BeautifulSoup
import requests

url = os.environ.get('TARGET_URL')
work_dir = os.environ.get('WORK_DIR')
desc_dir = os.environ.get('DESC_DIR')
epoch = os.environ.get('EPOCH_TIME')

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;'
        'q=0.9,image/webp,*/*;q=0.8'
    ),
}

try:
  resp = requests.get(url, headers=headers, timeout=20)
  soup = BeautifulSoup(resp.text, 'html.parser')

  media_url = None
  thumbnail_url = None

  video_tag = soup.find('video')
  if video_tag:
    if video_tag.get('src'):
      media_url = video_tag.get('src')
    elif video_tag.find('source'):
      media_url = video_tag.find('source').get('src')
    if video_tag.get('poster'):
      thumbnail_url = video_tag.get('poster')

  if not media_url:
    og_vid = soup.find('meta', property='og:video') or soup.find(
        'meta', property='og:video:secure_url'
    )
    if og_vid:
      media_url = og_vid.get('content')

  if not thumbnail_url:
    og_img = soup.find('meta', property='og:image')
    if og_img:
      thumbnail_url = og_img.get('content')

  if not media_url:
    matches = re.findall(r'https?://[^\s\"\'<>]+?\.(?:mp4|gif|webm|mov)', resp.text)
    valid_matches = [
        m
        for m in matches
        if not any(
            bad in m.lower() for bad in ['logo', 'icon', 'avatar', 'thumb']
        )
    ]
    if valid_matches:
      media_url = valid_matches[0]

  if not media_url:
    media_url = url

  print(f'Target Media ditemukan: {media_url}')

  media_res = requests.get(media_url, headers=headers, timeout=30)
  ext = 'mp4'
  if '.gif' in media_url.lower() or '.gif' in url.lower():
    ext = 'gif'
  elif '.webm' in media_url.lower():
    ext = 'webm'

  filename = f'id-time-{epoch}.{ext}'
  filepath = os.path.join(work_dir, filename)
  with open(filepath, 'wb') as f:
    f.write(media_res.content)

  if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
    if ext in ['gif', 'mp4', 'webm']:
      cap = cv2.VideoCapture(filepath)
      success, frame = cap.read()
      cap.release()
      if success:
        cv2.imwrite(os.path.join(desc_dir, f'id-time-{epoch}.jpg'), frame)
    elif thumbnail_url:
      thumb_res = requests.get(thumbnail_url, headers=headers)
      with open(os.path.join(desc_dir, f'id-time-{epoch}.jpg'), 'wb') as tf:
        tf.write(thumb_res.content)

  print('Berhasil mengunduh media via BeautifulSoup!')
except Exception as e:
  print(f'Gagal memproses via BeautifulSoup: {e}')
