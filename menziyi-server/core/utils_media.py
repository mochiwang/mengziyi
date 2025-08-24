import os, subprocess, json

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def transcode_to_wav16k_mono(src_path, dst_path):
    cmd = ["ffmpeg","-y","-i",src_path,"-ac","1","-ar","16000","-c:a","pcm_s16le",dst_path]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def probe_duration(path):
    cmd = ["ffprobe","-v","error","-show_entries","format=duration",
           "-of","default=noprint_wrappers=1:nokey=1", path]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    try: return float(out)
    except: return None

def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f: f.write(text)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
