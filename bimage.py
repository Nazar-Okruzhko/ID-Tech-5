import sys
import os
import struct
from pathlib import Path

def decompress_dxt1(data, width, height):
    """Decompress DXT1/BC1 format"""
    pixels = bytearray(width * height * 4)
    
    block_width = (width + 3) // 4
    block_height = (height + 3) // 4
    
    for by in range(block_height):
        for bx in range(block_width):
            block_offset = (by * block_width + bx) * 8
            if block_offset + 8 > len(data):
                continue
                
            c0 = struct.unpack('<H', data[block_offset:block_offset+2])[0]
            c1 = struct.unpack('<H', data[block_offset+2:block_offset+4])[0]
            indices = struct.unpack('<I', data[block_offset+4:block_offset+8])[0]
            
            # Convert RGB565 to RGB888
            colors = []
            for c in [c0, c1]:
                r = ((c >> 11) & 0x1F) * 255 // 31
                g = ((c >> 5) & 0x3F) * 255 // 63
                b = (c & 0x1F) * 255 // 31
                colors.append((r, g, b, 255))
            
            # Interpolate colors
            if c0 > c1:
                colors.append((
                    (2 * colors[0][0] + colors[1][0]) // 3,
                    (2 * colors[0][1] + colors[1][1]) // 3,
                    (2 * colors[0][2] + colors[1][2]) // 3,
                    255
                ))
                colors.append((
                    (colors[0][0] + 2 * colors[1][0]) // 3,
                    (colors[0][1] + 2 * colors[1][1]) // 3,
                    (colors[0][2] + 2 * colors[1][2]) // 3,
                    255
                ))
            else:
                colors.append((
                    (colors[0][0] + colors[1][0]) // 2,
                    (colors[0][1] + colors[1][1]) // 2,
                    (colors[0][2] + colors[1][2]) // 2,
                    255
                ))
                colors.append((0, 0, 0, 0))
            
            # Write pixels
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px
                    y = by * 4 + py
                    if x < width and y < height:
                        index = (indices >> ((py * 4 + px) * 2)) & 0x3
                        pixel_offset = (y * width + x) * 4
                        pixels[pixel_offset:pixel_offset+4] = colors[index]
    
    return bytes(pixels)

def decompress_dxt5(data, width, height):
    """Decompress DXT5/BC3 format"""
    pixels = bytearray(width * height * 4)
    
    block_width = (width + 3) // 4
    block_height = (height + 3) // 4
    
    for by in range(block_height):
        for bx in range(block_width):
            block_offset = (by * block_width + bx) * 16
            if block_offset + 16 > len(data):
                continue
            
            # Alpha block
            a0 = data[block_offset]
            a1 = data[block_offset + 1]
            alpha_indices = struct.unpack('<Q', data[block_offset:block_offset+8])[0] >> 16
            
            alphas = [a0, a1]
            if a0 > a1:
                for i in range(1, 7):
                    alphas.append(((7 - i) * a0 + i * a1) // 7)
            else:
                for i in range(1, 5):
                    alphas.append(((5 - i) * a0 + i * a1) // 5)
                alphas.extend([0, 255])
            
            # Color block
            c0 = struct.unpack('<H', data[block_offset+8:block_offset+10])[0]
            c1 = struct.unpack('<H', data[block_offset+10:block_offset+12])[0]
            indices = struct.unpack('<I', data[block_offset+12:block_offset+16])[0]
            
            colors = []
            for c in [c0, c1]:
                r = ((c >> 11) & 0x1F) * 255 // 31
                g = ((c >> 5) & 0x3F) * 255 // 63
                b = (c & 0x1F) * 255 // 31
                colors.append((r, g, b))
            
            colors.append((
                (2 * colors[0][0] + colors[1][0]) // 3,
                (2 * colors[0][1] + colors[1][1]) // 3,
                (2 * colors[0][2] + colors[1][2]) // 3
            ))
            colors.append((
                (colors[0][0] + 2 * colors[1][0]) // 3,
                (colors[0][1] + 2 * colors[1][1]) // 3,
                (colors[0][2] + 2 * colors[1][2]) // 3
            ))
            
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px
                    y = by * 4 + py
                    if x < width and y < height:
                        color_idx = (indices >> ((py * 4 + px) * 2)) & 0x3
                        alpha_idx = (alpha_indices >> ((py * 4 + px) * 3)) & 0x7
                        
                        pixel_offset = (y * width + x) * 4
                        pixels[pixel_offset:pixel_offset+3] = colors[color_idx]
                        pixels[pixel_offset+3] = alphas[alpha_idx]
    
    return bytes(pixels)

def write_png(filename, width, height, rgba_data):
    """Write PNG file manually"""
    import zlib
    
    def pack_be(fmt, *args):
        return struct.pack('>' + fmt, *args)
    
    # PNG signature
    png_data = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr = pack_be('IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png_data += pack_be('I', 13) + b'IHDR' + ihdr
    png_data += pack_be('I', zlib.crc32(b'IHDR' + ihdr) & 0xffffffff)
    
    # IDAT chunk
    raw = b''
    for y in range(height):
        raw += b'\x00'  # Filter type
        raw += rgba_data[y * width * 4:(y + 1) * width * 4]
    
    compressed = zlib.compress(raw, 9)
    png_data += pack_be('I', len(compressed)) + b'IDAT' + compressed
    png_data += pack_be('I', zlib.crc32(b'IDAT' + compressed) & 0xffffffff)
    
    # IEND chunk
    png_data += pack_be('I', 0) + b'IEND'
    png_data += pack_be('I', zlib.crc32(b'IEND') & 0xffffffff)
    
    with open(filename, 'wb') as f:
        f.write(png_data)

def convert_bimage(input_path):
    """Convert BIMAGE to PNG"""
    try:
        with open(input_path, 'rb') as f:
            # Read width (0x0E, big-endian int16)
            f.seek(0x0E)
            width = struct.unpack('>H', f.read(2))[0]
            
            # Read height (0x12, big-endian int16)
            f.seek(0x12)
            height = struct.unpack('>H', f.read(2))[0]
            
            # Read format (0x23)
            f.seek(0x23)
            fmt = f.read(1)[0]
            
            # Read image data (from 0x48)
            f.seek(0x48)
            image_data = f.read()
        
        print(f"Processing: {os.path.basename(input_path)}")
        print(f"Dimensions: {width}x{height}")
        
        # Decompress based on format
        if fmt == 0x0B:
            print("Format: BC3/DXT5")
            rgba = decompress_dxt5(image_data, width, height)
        elif fmt == 0x0A:
            print("Format: BC1/DXT1")
            rgba = decompress_dxt1(image_data, width, height)
        else:
            print(f"Unknown format: 0x{fmt:02X}")
            return False
        
        # Generate output filename
        output_path = str(Path(input_path).with_suffix('.png'))
        
        # Write PNG
        write_png(output_path, width, height, rgba)
        print(f"Saved: {os.path.basename(output_path)}\n")
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {e}\n")
        return False

def main():
    print("=" * 50)
    print("BIMAGE to PNG Converter")
    print("=" * 50 + "\n")
    
    if len(sys.argv) < 2:
        print("No files provided. Drag and drop .bimage files onto this script.")
        input("Press Enter to exit...")
        return
    
    files = sys.argv[1:]
    success_count = 0
    
    for file_path in files:
        if os.path.isfile(file_path):
            if convert_bimage(file_path):
                success_count += 1
    
    print("=" * 50)
    print(f"Completed: {success_count}/{len(files)} files converted successfully")
    print("=" * 50)

if __name__ == "__main__":
    main()
