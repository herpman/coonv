import os
import re
import cv2
import requests
from playwright.sync_api import sync_playwright

url = os.environ.get('TARGET_URL')
work_dir = os.environ.get('WORK_DIR')
desc_dir = os.environ.get('DESC_DIR')
epoch = os.environ.get('EPOCH_TIME')

media_url = None
thumbnail_url = None

print(f'Membuka browser otomatis untuk melewati proteksi: {url}')

with sync_playwright() as p:
  # Jalankan browser dalam mode headless (tanpa GUI) dengan argumen anti-deteksi bot
  browser = p.chromium.launch(
      headless=True,
      args=[
          '--disable-blink-features=AutomationControlled',
          '--no-sandbox',
          '--disable-setuid-sandbox',
      ],
  )
  context = browser.new_context(
      user_agent=(
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/122.0.0.0 Safari/537.36'
      ),
      viewport={'width': 1280, 'height': 800},
  )
  page = context.new_page()

  try:
    # Buka halaman dan tunggu sampai jaringan tenang (Cloudflare selesai verifikasi)
    page.goto(url, timeout=60000, wait_until='networkidle')
    
    # Beri sedikit waktu tambahan jika ada skrip redirect/load media dinamis
    page.wait_for_timeout(5000)

    html_content = page.content()

    # 1. Cari dari tag <video> atau <source> di DOM yang sudah dirender browser
    video_element = page.query_selector('video')
    if video_element:
      media_url = video_element.get_attribute('src')
      if not media_url:
        source_element = video_element.query_selector('source')
        if source_element:
          media_url = source_element.get_attribute('src')
      thumbnail_url = video_element.get_attribute('poster')

    # 2. Jika belum ketemu, cari via Meta Open Graph
    if not media_url:
      og_vid = page.query_selector('meta[property="og:video"]') or page.query_selector(
          'meta[property="og:video:secure_url"]'
      )
      if og_vid:
        media_url = og_vid.get_attribute('content')

    if not thumbnail_url:
      og_img = page.query_selector('meta[property="og:image"]')
      if og_img:
        thumbnail_url = og_img.get_attribute('content')

    # 3. Jika masih belum ketemu, scan regex dari HTML string
    if not media_url:
      matches = re.findall(r'https?://[^\s\"\'<>]+?\.(?:mp4|gif|webm|mov)', html_content)
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

    # Tangkap cookies dari sesi browser aktif agar unduhan media mendapat izin akses yang sama
    cookies = context.cookies()
    session_cookies = {c['name']: c['value'] for c in cookies}
    
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
        'Referer': url,
    }

    # Unduh file media menggunakan requests dengan membawa cookies sesi browser
    media_res = requests.get(media_url, headers=headers, cookies=session_cookies, stream=True, timeout=60)
    
    if 'text/html' in media_res.headers.get('Content-Type', '').lower():
      raise Exception(
          'Gagal mengunduh: Link yang diekstrak masih mengarah ke halaman HTML.'
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

    # Ekstrak frame pertama / thumbnail
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
        thumb_res = requests.get(thumbnail_url, headers=headers, cookies=session_cookies)
        with open(os.path.join(desc_dir, f'id-time-{epoch}.jpg'), 'wb') as tf:
          tf.write(thumb_res.content)
    else:
      raise Exception('File media yang diunduh terlalu kecil atau kosong.')

    print('Berhasil mengunduh media via Playwright Browser!')

  except Exception as e:
    print(f'Gagal memproses via Playwright: {e}')
  finally:
    browser.close()
