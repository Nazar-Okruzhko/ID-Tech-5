import struct
import os
import sys

# Configuration flags (set to 1 to enable extraction)
MAIN_SOUND = 1
ENG_SOUND = 1
FRA_SOUND = 0
ITA_SOUND = 0
SPA_SOUND = 0

# File paths
ARCHIVE_FILE = "bsnd.bms"  # Main archive file
STREAMED_RESOURCES = "streamed.resources"
ENG_STREAMED = "english.streamed"
FRA_STREAMED = "french.streamed"
ITA_STREAMED = "italian.streamed"
SPA_STREAMED = "spanish.streamed"

def read_string(f, length):
    """Read a string of specified length from file"""
    return f.read(length).decode('utf-8', errors='ignore').rstrip('\x00')

def read_long_le(f):
    """Read a 4-byte little-endian long"""
    return struct.unpack('<I', f.read(4))[0]

def read_long_be(f):
    """Read a 4-byte big-endian long"""
    return struct.unpack('>I', f.read(4))[0]

def extract_sound(source_file, output_name, offset, size):
    """Extract sound data from source file"""
    try:
        with open(source_file, 'rb') as src:
            src.seek(offset)
            data = src.read(size)
            
            os.makedirs(os.path.dirname(output_name) if os.path.dirname(output_name) else '.', exist_ok=True)
            with open(output_name, 'wb') as out:
                out.write(data)
            print(f"Extracted: {output_name} ({size} bytes)")
    except FileNotFoundError:
        print(f"Warning: Source file '{source_file}' not found, skipping {output_name}")
    except Exception as e:
        print(f"Error extracting {output_name}: {e}")

def main():
    if len(sys.argv) > 1:
        archive_file = sys.argv[1]
    else:
        archive_file = ARCHIVE_FILE
    
    if not os.path.exists(archive_file):
        print(f"Error: Archive file '{archive_file}' not found!")
        return
    
    print(f"Processing archive: {archive_file}")
    
    with open(archive_file, 'rb') as f:
        # Go to offset 0x24 (36 bytes)
        f.seek(0x24)
        
        # Read number of files (big-endian)
        files = read_long_be(f)
        unk = read_long_be(f)
        
        print(f"Number of files: {files}")
        
        tmp = files - 1
        
        for i in range(files):
            # Switch to little-endian for filenames
            fnsize1 = read_long_le(f)
            fn1 = read_string(f, fnsize1)
            
            fnsize2 = read_long_le(f)
            fn2 = read_string(f, fnsize2)
            
            namesize = read_long_le(f)
            name = read_string(f, namesize)
            
            # Switch back to big-endian for data
            offset = read_long_be(f)
            size = read_long_be(f)
            zsize = read_long_be(f)
            unksize = read_long_be(f)
            
            # Replace .wav with .ogg
            fn2 = fn2.replace('.wav', '.ogg')
            
            if unksize == 1:
                # Save current position and advance
                pos = f.tell()
                pos += 0x10
                f.seek(pos)
                
                offset = read_long_be(f)
                size = read_long_be(f)
                
                if MAIN_SOUND == 1:
                    extract_sound(STREAMED_RESOURCES, fn2, offset, size)
            
            elif unksize == 4:
                # English sound
                pos = f.tell()
                pos += 0x10
                f.seek(pos)
                offset = read_long_be(f)
                size = read_long_be(f)
                if ENG_SOUND == 1:
                    extract_sound(ENG_STREAMED, fn2, offset, size)
                
                # French sound
                pos = f.tell()
                pos += 0x10
                f.seek(pos)
                offset = read_long_be(f)
                size = read_long_be(f)
                if FRA_SOUND == 1:
                    extract_sound(FRA_STREAMED, fn2, offset, size)
                
                # Italian sound
                pos = f.tell()
                pos += 0x10
                f.seek(pos)
                offset = read_long_be(f)
                size = read_long_be(f)
                if ITA_SOUND == 1:
                    extract_sound(ITA_STREAMED, fn2, offset, size)
                
                # Spanish sound
                pos = f.tell()
                pos += 0x10
                f.seek(pos)
                offset = read_long_be(f)
                size = read_long_be(f)
                if SPA_SOUND == 1:
                    extract_sound(SPA_STREAMED, fn2, offset, size)
            
            else:
                # Read unknown data
                unksize_bytes = unksize * 0x18
                unkdata = f.read(unksize_bytes)
            
            # Save position and advance
            pos = f.tell()
            pos += 0x5
            f.seek(pos)
            
            # Read file number for next iteration (except last one)
            if i != tmp:
                filenumber = read_long_be(f)
    
    print("\nExtraction complete!")

if __name__ == "__main__":
    main()
