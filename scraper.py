import os
import re
import cv2
from bs4 import BeautifulSoup
import cloudscraper

url = os.environ.get('TARGET_URL')
work_dir = os.environ.get('WORK_DIR')
desc_dir = os.environ.get('DESC_DIR')
epoch = os.environ.get('EPOCH_TIME')

# Menggunakan cloudscraper untuk bypass proteksi Cloudflare/Anti-bot
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True,
    }
)

try:
  print(f'M mengakses URL via Cloudflare bypass: {url}')
  resp = scraper.get(url, timeout=30)
  
  if 'text/html' not in resp.headers.get('Content-Type', '').lower():
    # Jika URL langsung mengarah ke file media (misal langsung link .gif atau .mp4)
    media_url = url
  else:
    soup = BeautifulSoup(resp.text, 'html.parser')
    media_url = None
    thumbnail_url = None

    # Cari dari tag video
    video_tag = soup.find('video')
    if video_tag:
      if video_tag.get('src'):
        media_url = video_tag.get('src')
      elif video_tag.find('source'):
        media_url = video_tag.find('source').get('src')
      if video_tag.get('poster'):
        thumbnail_url = video_tag.get('poster')

    # Cari dari meta Open Graph
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

    # Cari via regex di seluruh teks HTML jika belum ketemu
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

  # Unduh file media menggunakan scraper yang sama (agar lolos proteksi CDN jika medianya juga diproteksi)
  media_res = scraper.get(media_url, stream=True, timeout=30)
  content_type = media_res.headers.get('Content-Type', '').lower()

  if 'text/html' in content_type:
    raise Exception(
        'Gagal mengunduh: Target masih mengembalikan halaman HTML meskipun sudah di-bypass.'
    )

  ext = 'mp4'
  if '.gif' in media_url.lower() or '.gif' in url.lower():
    ext = 'gif'
  elif '.webm' in media_url.lower():
    ext = 'webm'

  filename = f'id-time-{epoch}.{ext}'
  filepath = os.path.join(work_dir, filename)

  with open(filepath, 'wb') as f:
    for chunk in media_res.iter_content(chunk_size=8192):
      f.write(chunk)

  # Ekstrak frame pertama untuk preview JPG ke folder desc
  if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
    if ext in ['gif', 'mp4', 'webm']:
      cap = cv2.VideoCapture(filepath)
      success, frame = cap.read()
      cap.release()
      if success and frame is not None:
        cv2.imwrite(os.path.join(desc_dir, f'id-time-{epoch}.jpg'), frame)
        print('Berhasil mengambil frame preview!')
      else:
        print('Peringatan: Gagal ekstrak frame video dengan OpenCV.')
    elif thumbnail_url:
      thumb_res = scraper.get(thumbnail_url)
      with open(os.path.join(desc_dir, f'id-time-{epoch}.jpg'), 'wb') as tf:
        tf.write(thumb_res.content)
  else:
    raise Exception('File media yang diunduh terlalu kecil atau kosong.')

  print('Berhasil mengunduh media via Cloudflare Bypass!')
except Exception as e:
  print(f'Gagal memproses via Cloudscraper: {e}')
