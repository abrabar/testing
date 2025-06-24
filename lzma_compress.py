import os
import subprocess
import time
from pathlib import Path
import shutil
import tempfile
import psutil

# Configuration
EXE_DIR = r"C:\Users\Bar\Downloads\compression"
OUT_DIR = r"C:\Users\Bar\Downloads\compression_out_lzma"
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"  # Change if needed
ARCHIVE_PATH = r"C:\Users\Bar\Downloads\compression_out_lzma\combined_individual_lzma.7z"


def monitor_process(proc):
    p = psutil.Process(proc.pid)
    peak_mem = 0
    cpu_percent = []

    while proc.poll() is None:
        try:
            mem = p.memory_info().rss / (1024 * 1024)  # MB
            peak_mem = max(peak_mem, mem)
            cpu_percent.append(p.cpu_percent(interval=0.1))
        except psutil.NoSuchProcess:
            break

    avg_cpu = sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0
    return avg_cpu, peak_mem


def compress_individual():
    print("[*] Compressing each file individually (LZMA)...")
    os.makedirs(OUT_DIR, exist_ok=True)
    temp_dir = Path(OUT_DIR) / "individual"
    temp_dir.mkdir(exist_ok=True)

    start = time.time()
    cpu_total, mem_peak = 0, 0

    for exe in Path(EXE_DIR).glob("*.exe"):
        out_file = temp_dir / f"{exe.stem}.7z"
        proc = subprocess.Popen([SEVEN_ZIP, "a", "-t7z", "-m0=lzma2", "-mx=9", str(out_file), str(exe)])
        cpu, mem = monitor_process(proc)
        proc.wait()
        cpu_total += cpu
        mem_peak = max(mem_peak, mem)

    combined = Path(OUT_DIR) / "combined_individual_lzma.7z"
    with open(combined, "wb") as out_f:
        for part in temp_dir.glob("*.7z"):
            out_f.write(part.read_bytes())

    duration = time.time() - start
    print(f"[+] Individual compression done in {duration:.2f}s | Peak RAM: {mem_peak:.1f} MB")


def compress_combined():
    print("[*] Concatenating all files then compressing (LZMA)...")
    combined_file = Path(OUT_DIR) / "all_combined.bin"
    with open(combined_file, "wb") as out_f:
        for exe in Path(EXE_DIR).glob("*.exe"):
            out_f.write(exe.read_bytes())

    start = time.time()
    proc = subprocess.Popen([SEVEN_ZIP, "a", "-t7z", "-m0=lzma2", "-mx=9", str(combined_file.with_suffix(".7z")), str(combined_file)])
    cpu, mem = monitor_process(proc)
    proc.wait()
    duration = time.time() - start

    print(f"[+] Combined compression done in {duration:.2f}s | Peak RAM: {mem:.1f} MB")


def decompress_lzma():
    temp_dir = tempfile.mkdtemp(prefix="lzma_decompress_")
    print(f"[*] Decompressing LZMA archive to: {temp_dir}")

    start = time.time()
    proc = subprocess.Popen([SEVEN_ZIP, "x", ARCHIVE_PATH, f"-o{temp_dir}", "-y"])
    cpu, mem = monitor_process(proc)
    proc.wait()
    duration = time.time() - start

    print(f"[+] Decompression done in {duration:.2f}s | Peak RAM: {mem:.1f} MB")

    # Optional cleanup
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    compress_individual()
    compress_combined()
    print("[+] LZMA compression complete.")
    decompress_lzma()
    print("[+] LZMA decompression complete.")