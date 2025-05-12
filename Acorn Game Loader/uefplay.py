import sounddevice as sd
import numpy as np
import gzip
import struct
import argparse
import io
import time
import os
from bisect import bisect_left

# === UEF Chunk handling ===
SUPPORTED_CHUNKS = {
    0x0100: 'Implicit start/stop bit tape data block',
    0x0104: 'Defined tape format data block',
    0x0110: 'Carrier tone',
    0x0111: 'Carrier tone with dummy byte',
    0x0112: 'Integer gap',
    0x0114: 'Security cycles (approximate)',
    0x0116: 'Floating point gap (approximate)'
}

# Control file paths
current_block_file = os.path.join(os.getenv("TEMP"), "current_block.txt")
total_blocks_file = os.path.join(os.getenv("TEMP"), "total_blocks.txt")
next_block_file = os.path.join(os.getenv("TEMP"), "next_block.txt")

# Constants
BAUD = 1200
CARRIER_FREQ = BAUD * 2  # 2400Hz
SAMPLE_RATE = 44100
SAMPLES_PER_BIT = int(SAMPLE_RATE / BAUD)
SAMPLES_PER_CARRIER_CYCLE = int(SAMPLE_RATE / CARRIER_FREQ)

# === UEF Helpers ===
def is_data_block(chunk_id):
    return chunk_id in (0x0100, 0x0104)

def load_uef_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(12)
            if header.startswith(b'UEF File!'):
                f.seek(0)
                return f
            f.seek(0)
        with gzip.open(filepath, 'rb') as f:
            header = f.read(12)
            if header.startswith(b'UEF File!'):
                f.seek(0)
                return gzip.open(filepath, 'rb')
    except:
        pass
    raise ValueError("Not a valid UEF file")

class UEFChunk:
    __slots__ = ['chunk_id', 'data', 'is_data_block']
    def __init__(self, chunk_id, data):
        self.chunk_id = chunk_id
        self.data = data
        self.is_data_block = is_data_block(chunk_id)

def parse_uef(fileobj):
    chunks = []
    fileobj.read(12)  # Skip header
    while True:
        header = fileobj.read(6)
        if len(header) < 6: break
        chunk_id, length = struct.unpack('<HI', header)
        data = fileobj.read(length)
        chunks.append(UEFChunk(chunk_id, data))
    return chunks

# === Audio Generation ===
def generate_carrier_tone(cycles, invert=False):
    total_samples = cycles * SAMPLES_PER_CARRIER_CYCLE
    t = np.arange(total_samples)
    wave = np.sign(np.sin(2 * np.pi * CARRIER_FREQ * t / SAMPLE_RATE))
    if invert:
        wave = -wave
    return 0.5 * wave.astype(np.float32)

def generate_silence(duration_sec):
    return np.zeros(int(SAMPLE_RATE * duration_sec), dtype=np.float32)

def encode_byte(byte):
    samples = []
    # Start bit (low = 1200Hz)
    samples.append(generate_fixed_tone(BAUD, SAMPLES_PER_BIT, low=True))
    for i in range(8):
        bit = (byte >> i) & 1
        samples.append(generate_fixed_tone(BAUD, SAMPLES_PER_BIT, low=(bit==0)))
    # Stop bit (high = 2400Hz)
    samples.append(generate_fixed_tone(BAUD, SAMPLES_PER_BIT, low=False))
    return np.concatenate(samples)

def generate_fixed_tone(baud, samples_per_bit, low=True):
    freq = baud if low else baud * 2
    t = np.arange(samples_per_bit)
    wave = np.sign(np.sin(2 * np.pi * freq * t / SAMPLE_RATE))
    return 0.5 * wave.astype(np.float32)

def generate_chunk_audio(chunk):
    if chunk.chunk_id == 0x0110:  # Carrier tone
        cycles = struct.unpack('<H', chunk.data[:2])[0]
        return generate_carrier_tone(cycles)
    elif chunk.chunk_id == 0x0100:  # Data block
        samples = [encode_byte(b) for b in chunk.data]
        return np.concatenate(samples) if samples else np.zeros(0, dtype=np.float32)
    elif chunk.chunk_id == 0x0112:  # Integer gap
        pause_ms = struct.unpack('<H', chunk.data[:2])[0]
        return generate_silence(pause_ms / 1000.0)
    elif chunk.chunk_id == 0x0111:  # Carrier with dummy byte
        pre_cycles, post_cycles = struct.unpack('<HH', chunk.data[:4])
        pre = generate_carrier_tone(pre_cycles)
        byte = encode_byte(0xAA)
        post = generate_carrier_tone(post_cycles)
        return np.concatenate([pre, byte, post])
    elif chunk.chunk_id == 0x0114:  # Security cycles (approx)
        cycles = int.from_bytes(chunk.data[:3], 'little')
        return generate_carrier_tone(cycles)
    elif chunk.chunk_id == 0x0116:  # Floating gap
        f = struct.unpack('<f', chunk.data[:4])[0]
        return generate_silence(f)
    return np.zeros(0, dtype=np.float32)

# === Playback Control ===
def write_block_info(current_block, total_blocks):
    try:
        with open(current_block_file, 'w') as f:
            f.write(str(current_block))
        with open(total_blocks_file, 'w') as f:
            f.write(str(total_blocks))
        with open(next_block_file, 'w') as f:
            next_block = min(current_block + 1, total_blocks - 1)
            f.write(str(next_block))
    except:
        pass

def play_audio(chunks, control_file):
    data_blocks = [i for i, chunk in enumerate(chunks) if chunk.is_data_block]
    total_data_blocks = len(data_blocks)
    write_block_info(0, total_data_blocks)

    stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=1024)
    stream.start()

    current_chunk = 0
    play_pos = 0
    current_data_block_idx = 0
    paused = False

    while current_chunk < len(chunks):
        if os.path.exists(control_file):
            with open(control_file, 'r') as f:
                cmd = f.read().strip().lower()
            try:
                os.remove(control_file)
            except:
                pass

            if cmd == "pause":
                paused = True
            elif cmd == "resume":
                paused = False
            elif cmd == "stop":
                break
            elif cmd.startswith("rewind"):
                if current_data_block_idx > 0:
                    current_data_block_idx -= 1
                    current_chunk = data_blocks[current_data_block_idx]
                    play_pos = 0
                    write_block_info(current_data_block_idx, total_data_blocks)
                    continue
            elif cmd.startswith("fastforward"):
                if current_data_block_idx < total_data_blocks - 1:
                    current_data_block_idx += 1
                    current_chunk = data_blocks[current_data_block_idx]
                    play_pos = 0
                    write_block_info(current_data_block_idx, total_data_blocks)
                    continue
            elif cmd.startswith("jump:"):
                try:
                    target_block = int(cmd.split(":")[1])
                    if 0 <= target_block < total_data_blocks:
                        current_data_block_idx = target_block
                        current_chunk = data_blocks[current_data_block_idx]
                        play_pos = 0
                        write_block_info(current_data_block_idx, total_data_blocks)
                        continue
                except:
                    pass

        if paused:
            time.sleep(0.1)
            continue

        chunk = chunks[current_chunk]
        audio = generate_chunk_audio(chunk)
        audio_len = len(audio)

        while play_pos < audio_len:
            end_pos = min(play_pos + 1024, audio_len)
            stream.write(audio[play_pos:end_pos])
            play_pos = end_pos

            if chunk.is_data_block and play_pos == audio_len:
                new_idx = bisect_left(data_blocks, current_chunk)
                if new_idx != current_data_block_idx:
                    current_data_block_idx = new_idx
                    write_block_info(current_data_block_idx, total_data_blocks)

            if paused or os.path.exists(control_file):
                break

        current_chunk += 1
        play_pos = 0

    stream.stop()
    stream.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UEF Player with Zero-Based Data Block Navigation")
    parser.add_argument("uef_file", help="UEF file to play")
    parser.add_argument("--control", default=os.path.join(os.getenv('TEMP'), 'uef_control.txt'),
                        help="Control file path")
    args = parser.parse_args()

    try:
        start_time = time.time()
        fileobj = load_uef_file(args.uef_file)
        chunks = parse_uef(fileobj)
        fileobj.close()

        data_block_count = sum(1 for c in chunks if c.is_data_block)
        print(f"Loaded {len(chunks)} chunks ({data_block_count} data blocks) in {time.time()-start_time:.2f}s")
        print("Data blocks are numbered 0 to", data_block_count - 1)
        print("Starting playback...")

        play_audio(chunks, args.control)
    except Exception as e:
        print(f"Error: {e}")
