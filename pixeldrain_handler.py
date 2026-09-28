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
  print(f'Downloading full archive to extract single file: {sub_file}')
  res = requests.get(api_url, headers=headers, stream=True, timeout=120)

  temp_arc = os.path.join(work_dir, 'temp_archive.zip')
  with open(temp_arc, 'wb') as f:
    for chunk in res.iter_content(chunk_size=8192):
      f.write(chunk)

  # Ekstrak hanya file yang dimaksud
  if zipfile.is_zipfile(temp_arc):
    with zipfile.ZipFile(temp_arc, 'r') as zf:
      # Ekstrak file spesifik ke work_dir
      zf.extract(sub_file, path=work_dir)

      # Pindahkan file hasil ekstrak ke akar work_dir jika berada di dalam subfolder
      extracted_path = os.path.join(work_dir, sub_file)
      if extracted_path != os.path.join(work_dir, os.path.basename(sub_file)):
        import shutil

        target_path = os.path.join(work_dir, os.path.basename(sub_file))
        shutil.move(extracted_path, target_path)

  os.remove(temp_arc)
  print(f'Successfully extracted parallel task file: {sub_file}')
except Exception as e:
  print(f'Error in sub_handler: {e}')
