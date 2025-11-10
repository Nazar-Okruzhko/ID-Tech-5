import os
import sys
import struct
import zlib
from pathlib import Path

def extract_resources(resources_file_path):
    """Extract .resources file using corresponding .index file"""
    
    # Get the base path without extension
    base_path = Path(resources_file_path)
    index_file_path = base_path.with_suffix('.index')
    output_dir = base_path.with_suffix('')
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print(f"Extracting {resources_file_path}")
    print(f"Using index file: {index_file_path}")
    print(f"Output directory: {output_dir}\n")
    
    try:
        # Open both files
        with open(index_file_path, 'rb') as index_file, \
             open(resources_file_path, 'rb') as resources_file:
            
            # Read header from index file
            index_file.seek(0x24)
            
            # Read number of files (big endian)
            files_data = index_file.read(4)
            if len(files_data) < 4:
                print("Error: Index file too small")
                return
            
            files = struct.unpack('>I', files_data)[0]
            unk = struct.unpack('>I', index_file.read(4))[0]
            
            print(f"Total files to extract: {files}\n")
            
            # Calculate last file index
            tmp = files - 1
            
            # Counters for summary
            uncompressed_count = 0
            compressed_count = 0
            failed_count = 0
            
            for i in range(files):
                # Read filename parts (little endian)
                fn_size1_data = index_file.read(4)
                if len(fn_size1_data) < 4:
                    print(f"Error reading FNsize1 for file {i}")
                    break
                    
                fn_size1 = struct.unpack('<I', fn_size1_data)[0]
                fn1 = index_file.read(fn_size1).decode('utf-8', errors='replace')
                
                fn_size2_data = index_file.read(4)
                if len(fn_size2_data) < 4:
                    print(f"Error reading FNsize2 for file {i}")
                    break
                    
                fn_size2 = struct.unpack('<I', fn_size2_data)[0]
                fn2 = index_file.read(fn_size2).decode('utf-8', errors='replace')
                
                namesize_data = index_file.read(4)
                if len(namesize_data) < 4:
                    print(f"Error reading namesize for file {i}")
                    break
                    
                namesize = struct.unpack('<I', namesize_data)[0]
                name = index_file.read(namesize).decode('utf-8', errors='replace')
                
                # Read file data info (big endian)
                offset_data = index_file.read(4)
                if len(offset_data) < 4:
                    print(f"Error reading offset for file {i}")
                    break
                    
                offset = struct.unpack('>I', offset_data)[0]
                size = struct.unpack('>I', index_file.read(4))[0]
                zsize = struct.unpack('>I', index_file.read(4))[0]
                unksize = struct.unpack('>I', index_file.read(4))[0]
                
                # Calculate and skip unkdata
                unksize_calc = unksize * 0x18 + 5
                index_file.read(int(unksize_calc))
                
                # Clean up filename and create proper directory structure
                clean_name = name.strip().replace('\x00', '')
                if not clean_name:
                    clean_name = f"file_{i:04d}"
                
                # Create full output path with proper directory structure
                output_path = output_dir / clean_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Read the data from resources file
                    resources_file.seek(offset)
                    
                    if size == zsize:
                        # Uncompressed data
                        data = resources_file.read(size)
                        with open(output_path, 'wb') as out_file:
                            out_file.write(data)
                        status = "✓"
                        uncompressed_count += 1
                    else:
                        # Compressed data - use raw DEFLATE (RFC 1951)
                        compressed_data = resources_file.read(zsize)
                        
                        # Try raw DEFLATE decompression (no headers)
                        try:
                            # Use wbits = -15 for raw DEFLATE without headers
                            decompressor = zlib.decompressobj(-15)
                            data = decompressor.decompress(compressed_data)
                            data += decompressor.flush()
                            
                            if len(data) == size:
                                with open(output_path, 'wb') as out_file:
                                    out_file.write(data)
                                status = "✓"
                                compressed_count += 1
                            else:
                                # Size mismatch but we'll use what we got
                                with open(output_path, 'wb') as out_file:
                                    out_file.write(data)
                                status = "⚠"
                                failed_count += 1
                                
                        except zlib.error as e:
                            # Try alternative decompression methods
                            success = False
                            
                            # Method 2: Try with zlib header
                            try:
                                data = zlib.decompress(compressed_data)
                                if len(data) == size or abs(len(data) - size) < 100:
                                    with open(output_path, 'wb') as out_file:
                                        out_file.write(data)
                                    status = "✓"
                                    compressed_count += 1
                                    success = True
                            except:
                                pass
                            
                            if not success:
                                # Method 3: Try different window bits
                                for wbits in [15, -zlib.MAX_WBITS]:
                                    try:
                                        decompressor = zlib.decompressobj(wbits)
                                        data = decompressor.decompress(compressed_data)
                                        data += decompressor.flush()
                                        if len(data) == size or abs(len(data) - size) < 100:
                                            with open(output_path, 'wb') as out_file:
                                                out_file.write(data)
                                            status = "✓"
                                            compressed_count += 1
                                            success = True
                                            break
                                    except:
                                        continue
                            
                            if not success:
                                # All methods failed
                                with open(output_path, 'wb') as out_file:
                                    out_file.write(compressed_data)
                                status = "✗"
                                failed_count += 1
                    
                    # Print progress in the requested format
                    print(f"{status} [{i+1}/{files}]: {clean_name} [EXTRACTED] [{zsize} => {size} bytes]")
                
                except Exception as e:
                    print(f"✗ [{i+1}/{files}]: {clean_name} [ERROR] [Failed to extract]")
                    failed_count += 1
                
                # Read filenumber for all except last file
                if i != tmp:
                    filenumber_data = index_file.read(4)
                    if len(filenumber_data) < 4:
                        print(f"Error reading filenumber after file {i}")
                        break
            
            # Print final summary
            print("\n" + "=" * 70)
            print("EXTRACTED! [{}]".format(uncompressed_count + compressed_count))
            print(f"Successfully decompressed: {compressed_count}")
            print(f"Already decompressed: {uncompressed_count}")
            print(f"Failed to decompress: {failed_count}")
            print("=" * 70)
            print(f"\nExtraction complete! Files saved to: {output_dir}")
            
    except FileNotFoundError:
        print(f"Error: Index file not found: {index_file_path}")
    except Exception as e:
        print(f"Error during extraction: {e}")

def main():
    """Main function with drag and drop support"""
    
    if len(sys.argv) < 2:
        print("Drag and drop .resources files onto this script to extract them.")
        print("Or usage: python script.py file1.resources file2.resources ...")
        input("\nPress Enter to exit...")
        return
    
    for file_path in sys.argv[1:]:
        if os.path.isfile(file_path) and file_path.lower().endswith('.resources'):
            extract_resources(file_path)
            print("\n" + "=" * 70)
        else:
            print(f"Skipping invalid file: {file_path}")
    
    # Keep console open
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
