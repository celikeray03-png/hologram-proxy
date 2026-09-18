@app.route('/convert-upload', methods=['POST'])
def convert_and_upload():
    device_ip = request.form.get('device_ip')
    uploaded_file = request.files.get('file')

    if not device_ip or not uploaded_file:
        return "<h2>Hata: Eksik Parametre!</h2><a href='javascript:history.back()'>Geri Dön</a>", 400

    filename = uploaded_file.filename
    input_path = f"temp_{filename}"
    output_filename = os.path.splitext(filename)[0] + ".mjpeg"
    output_path = f"temp_{output_filename}"

    try:
        uploaded_file.save(input_path)

        # Build komutu ile indirilen ham ffmpeg çalıştırıcısı
        ffmpeg_bin = os.path.join(os.getcwd(), "ffmpeg")
        if os.path.exists(ffmpeg_bin):
            os.chmod(ffmpeg_bin, 0o755)

        ffmpeg_cmd = [
            ffmpeg_bin if os.path.exists(ffmpeg_bin) else "ffmpeg", "-y",
            "-i", input_path,
            "-vf", "scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2",
            "-q:v", "5",
            "-r", "25",
            "-pix_fmt", "yuvj420p",
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True, timeout=40)

        esp32_url = f"http://{device_ip}/upload"
        with open(output_path, "rb") as f:
            files = {'upload': (output_filename, f, 'application/octet-stream')}
            response = requests.post(esp32_url, files=files, timeout=40)

        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

        return f"<h2>Dönüştürme ve Yükleme Başarılı!</h2><p>{output_filename} SD karta yüklendi.</p><a href='http://{device_ip}/media'>Geri Dön</a>"

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        return f"<h2>Hata Oluştu!</h2><p>{str(e)}</p><a href='http://{device_ip}/media'>Geri Dön</a>", 500
