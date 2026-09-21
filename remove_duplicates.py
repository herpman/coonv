import os

file_path = "yt_urls.txt"

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    seen = set()
    unique_lines = []

    for line in lines:
        cleaned_line = line.strip()
        
        # Lewati baris kosong atau komentar
        if not cleaned_line or cleaned_line.startswith("#"):
            continue
        
        if cleaned_line not in seen:
            seen.add(cleaned_line)
            unique_lines.append(cleaned_line)

    # Tulis ulang file dengan data yang sudah unik
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(unique_lines) + "\n")

    print(f"Berhasil membersihkan duplikat. Sisa link unik: {len(unique_lines)}")
else:
    print(f"File {file_path} tidak ditemukan!")
