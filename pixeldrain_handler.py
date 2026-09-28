import os
import zipfile
import requests

url = os.environ.get('TARGET_URL')
work_dir = os.environ.get('WORK_DIR')
epoch = os.environ.get('EPOCH_TIME')

file_id = url.split('/u/')[-1].split('?')[0]
api_download_url = f'https://pixeldrain.com/api/file/{file_id}'
info_url = f'https://pixeldrain.com/api/file/{file_id}/info'

headers = {'User-Agent': 'Mozilla/5.0'}
file_name = f'file-{epoch}'
ext = 'mp4'

try:
  meta_res = requests.get(info_url, headers=headers, timeout=15)
  if meta_res.status_code == 200:
    data = meta_res.json()
    if 'name' in data:
      file_name = data['name']
      if '.' in file_name:
        ext = file_name.split('.')[-1].lower()

  print(f'Downloading Pixeldrain file: {file_name} (Ext: {ext})')
  res = requests.get(api_download_url, headers=headers, stream=True, timeout=60)

  archive_path = os.path.join(work_dir, file_name)
  with open(archive_path, 'wb') as f:
    for chunk in res.iter_content(chunk_size=8192):
      f.write(chunk)

  # Jika berupa file arsip, ekstrak otomatis ke work_dir
  if ext in ['zip', 'rar', '7z', 'tar', 'gz', 'tgz']:
    print(f'Extracting archive format {ext}...')
    if ext == 'zip':
      with zipfile.ZipFile(archive_path, 'r') as zf:
        zf.extractall(work_dir)
      os.remove(archive_path)
    else:
      os.system(f'7z x "{archive_path}" -o"{work_dir}" -y')
      os.remove(archive_path)
  print('Pixeldrain processing complete!')
except Exception as e:
  print(f'Error processing Pixeldrain: {e}')
