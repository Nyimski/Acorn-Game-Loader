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
def generate_tone(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return 0.5 * np.sign(np.sin(2 * np.pi * frequency * t)).astype(np.float32)

def generate_chunk_audio(chunk, sample_rate=44100):
    baud = 1200
    if chunk.chunk_id == 0x0110:  # Carrier tone
        cycles = struct.unpack('<H', chunk.data[:2])[0]
        return generate_tone(baud*2, cycles/baud, sample_rate)
    elif chunk.chunk_id == 0x0100:  # Data block
        samples = []
        for byte in chunk.data:
            samples.append(encode_byte(byte, baud, sample_rate))
        return np.concatenate(samples) if samples else np.zeros(0, dtype=np.float32)
    elif chunk.chunk_id == 0x0112:  # Integer gap
        pause_ms = struct.unpack('<H', chunk.data[:2])[0]
        return np.zeros(int(sample_rate * pause_ms / 1000.0), dtype=np.float32)
    elif chunk.chunk_id == 0x0111:  # Carrier with dummy byte
        pre_cycles, post_cycles = struct.unpack('<HH', chunk.data[:4])
        pre = generate_tone(baud*2, pre_cycles/baud, sample_rate)
        byte = encode_byte(0xAA, baud, sample_rate)
        post = generate_tone(baud*2, post_cycles/baud, sample_rate)
        return np.concatenate([pre, byte, post])
    elif chunk.chunk_id == 0x0114:  # Security cycles
        cycles = int.from_bytes(chunk.data[:3], 'little')
        return generate_tone(baud*2, cycles/baud, sample_rate)
    elif chunk.chunk_id == 0x0116:  # Floating point gap
        f = struct.unpack('<f', chunk.data[:4])[0]
        return np.zeros(int(sample_rate * f), dtype=np.float32)
    return np.zeros(0, dtype=np.float32)

def encode_byte(byte, baud=1200, sample_rate=44100):
    samples = [generate_tone(baud, 1/baud, sample_rate)]  # Start bit
    for i in range(8):
        bit = (byte >> i) & 1
        samples.append(generate_tone(baud*(2 if bit else 1), 1/baud, sample_rate))
    samples.append(generate_tone(baud*2, 1/baud, sample_rate))  # Stop bit
    return np.concatenate(samples)

# === Playback Control ===
def write_block_info(current_block, total_blocks):
    try:
        with open(current_block_file, 'w') as f:
            f.write(str(current_block))
        with open(total_blocks_file, 'w') as f:
            f.write(str(total_blocks))
        with open(next_block_file, 'w') as f:
            f.write(str(min(current_block + 1, total_blocks - 1)))
    except:
        pass

def find_nearest_data_block(data_blocks, current_chunk, direction):
    """Find the nearest data block in the specified direction (1=forward, -1=backward)"""
    idx = bisect_left(data_blocks, current_chunk)
    
    if direction > 0:  # Forward
        if idx < len(data_blocks) and data_blocks[idx] == current_chunk:
            return data_blocks[idx + 1] if idx + 1 < len(data_blocks) else data_blocks[-1]
        return data_blocks[idx] if idx < len(data_blocks) else data_blocks[-1]
    else:  # Backward
        return data_blocks[idx - 1] if idx > 0 else data_blocks[0]

def play_audio(chunks, control_file, sample_rate=44100):
    # First identify all data blocks and their positions
    data_blocks = [i for i, chunk in enumerate(chunks) if chunk.is_data_block]
    total_data_blocks = len(data_blocks)
    write_block_info(0, total_data_blocks)

    # Playback with lazy generation
    stream = sd.OutputStream(samplerate=sample_rate, channels=1, blocksize=1024)
    stream.start()
    
    current_chunk = 0
    play_pos = 0
    current_data_block_idx = 0  # Index in data_blocks list
    paused = False
    
    while current_chunk < len(chunks):
        # Handle control commands
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
                # Rewind to previous data block
                if current_data_block_idx > 0:
                    current_data_block_idx -= 1
                    current_chunk = data_blocks[current_data_block_idx]
                    play_pos = 0
                    write_block_info(current_data_block_idx, total_data_blocks)
                    continue
            elif cmd.startswith("fastforward"):
                # Fast forward to next data block
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

        # Generate and play current chunk
        chunk = chunks[current_chunk]
        audio = generate_chunk_audio(chunk, sample_rate)
        audio_len = len(audio)
        
        while play_pos < audio_len:
            end_pos = min(play_pos + 1024, audio_len)
            stream.write(audio[play_pos:end_pos])
            play_pos = end_pos
            
            # Update data block index if we're entering a new data block
            if chunk.is_data_block and play_pos == audio_len:
                # Find our position in the data_blocks list
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
    parser = argparse.ArgumentParser(description="UEF Player with Data Block Navigation")
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
        print("Starting playback...")
        
        play_audio(chunks, args.control)
    except Exception as e:
        print(f"Error: {e}")