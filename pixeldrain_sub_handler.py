import os
import zipfile
import requests

task_str = os.environ.get('TASK_STRING')
work_dir = os.environ.get('WORK_DIR')

# Format string: pixeldrain-sub__FILEID__SUBPATH
parts = task_str.split('__')
file_id = parts[1]
sub_file = parts[2]

api_url = f'https://pixeldrain.com/api/file/{file_id}'
headers = {'User-Agent': 'Mozilla/5.0'}

try:
  print(f'Downloading archive to extract file: {sub_file}')
  res = requests.get(api_url, headers=headers, stream=True, timeout=120)

  temp_arc = os.path.join(work_dir, 'temp_archive')
  with open(temp_arc, 'wb') as f:
    for chunk in res.iter_content(chunk_size=8192):
      f.write(chunk)

  # Deteksi apakah zip atau format lain, lalu ekstrak
  if zipfile.is_zipfile(temp_arc):
    with zipfile.ZipFile(temp_arc, 'r') as zf:
      zf.extract(sub_file, path=work_dir)
      extracted_path = os.path.join(work_dir, sub_file)
      target_path = os.path.join(work_dir, os.path.basename(sub_file))
      if extracted_path != target_path and os.path.exists(extracted_path):
        import shutil

        shutil.move(extracted_path, target_path)
  else:
    # Jika format lain (rar/7z), gunakan 7z
    os.system(f'7z x "{temp_arc}" -o"{work_dir}" -y "{sub_file}"')

  if os.path.exists(temp_arc):
    os.remove(temp_arc)
  print(f'Successfully extracted: {sub_file}')
except Exception as e:
  print(f'Error extracting sub-file: {e}')
