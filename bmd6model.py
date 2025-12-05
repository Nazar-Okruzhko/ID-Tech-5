import struct
import sys
import os
import math

# ============= CONFIGURATION =============
# These are adjustable parameters for file structure
HEADER_SIZE = 64
BUFFER_MARKER = b'\x00\x00\x00\x01\x00\x00'
SKIP_TO_VERTEX_COUNT = 0  # Bytes to skip after buffer marker to reach vertex count
SKIP_TO_FACE_COUNT = 2    # Bytes to skip after vertex count to reach face count
SKIP_TO_FIRST_VERTEX = 24 # Bytes to skip after face count to reach first vertex
VERTEX_STRIDE = 32        # Total bytes per vertex entry (12 for XYZ + 8 for UV + 12 padding)

# ============= USER OPTIONS =============
# Transform options applied to each extracted model
ROTATE_X_MINUS_90 = True   # Rotate model -90 degrees on X axis
FLIP_UV_MAPS = True        # Flip UV coordinates (1.0 - V)
FLIP_FACE_ORIENTATION = True  # Reverse face winding order
SHADE_SMOOTH = True        # Generate smooth vertex normals (like Blender's Shade Smooth)
# ==========================================

def read_int16_be(data, offset):
    """Read big-endian 16-bit integer"""
    return struct.unpack('>H', data[offset:offset+2])[0]

def read_float_be(data, offset):
    """Read big-endian 32-bit float"""
    return struct.unpack('>f', data[offset:offset+4])[0]

def rotate_x_minus_90(vertices):
    """Rotate vertices -90 degrees around X axis"""
    rotated = []
    for x, y, z in vertices:
        # Rotation matrix for -90 degrees around X axis
        # [1,  0,  0]   [x]
        # [0,  0,  1] * [y]
        # [0, -1,  0]   [z]
        new_x = x
        new_y = z
        new_z = -y
        rotated.append((new_x, new_y, new_z))
    return rotated

def flip_uvs(uvs):
    """Flip UV coordinates (invert V)"""
    return [(u, 1.0 - v) for u, v in uvs]

def flip_faces(faces):
    """Reverse face winding order"""
    return [(f[0], f[2], f[1]) for f in faces]

def calculate_vertex_normals(vertices, faces):
    """Calculate smooth vertex normals (like Blender's Shade Smooth)"""
    # Initialize normal accumulator for each vertex
    normals = [[0.0, 0.0, 0.0] for _ in vertices]
    
    # For each face, calculate face normal and add to vertex normals
    for face in faces:
        # Get the three vertices of the triangle
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        # Calculate two edge vectors
        edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        
        # Calculate face normal using cross product
        nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
        ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
        nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]
        
        # Add this face normal to all three vertices
        for idx in face:
            normals[idx][0] += nx
            normals[idx][1] += ny
            normals[idx][2] += nz
    
    # Normalize all vertex normals
    normalized_normals = []
    for normal in normals:
        length = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
        if length > 0.0:
            normalized_normals.append((
                normal[0] / length,
                normal[1] / length,
                normal[2] / length
            ))
        else:
            normalized_normals.append((0.0, 0.0, 1.0))  # Default normal
    
    return normalized_normals

def apply_transforms(model_data):
    """Apply user-configured transforms to model data"""
    if ROTATE_X_MINUS_90:
        print("[TRANSFORM] Applying X-axis -90° rotation...")
        model_data['vertices'] = rotate_x_minus_90(model_data['vertices'])
    
    if FLIP_UV_MAPS:
        print("[TRANSFORM] Flipping UV maps...")
        model_data['uvs'] = flip_uvs(model_data['uvs'])
    
    if FLIP_FACE_ORIENTATION:
        print("[TRANSFORM] Flipping face orientation...")
        model_data['faces'] = flip_faces(model_data['faces'])
    
    if SHADE_SMOOTH:
        print("[TRANSFORM] Calculating smooth vertex normals...")
        model_data['normals'] = calculate_vertex_normals(model_data['vertices'], model_data['faces'])
    else:
        model_data['normals'] = None
    
    return model_data
    """Read big-endian 16-bit integer"""
    return struct.unpack('>H', data[offset:offset+2])[0]

def read_float_be(data, offset):
    """Read big-endian 32-bit float"""
    return struct.unpack('>f', data[offset:offset+4])[0]

def find_buffer_marker(data, start_offset=0):
    """Find the buffer marker in the data"""
    index = data.find(BUFFER_MARKER, start_offset)
    return index

def extract_model(data, start_search_offset, part_number=1):
    """Extract model data from .bmd6model file data"""
    
    print(f"\n{'='*60}")
    print(f"Extracting Part {part_number}")
    print(f"{'='*60}\n")
    
    # Find buffer marker from the given offset
    marker_offset = find_buffer_marker(data, start_search_offset)
    if marker_offset == -1:
        print(f"[INFO] No more buffer markers found (searched from offset 0x{start_search_offset:X})")
        return None, -1
    
    print(f"[INFO] Buffer marker found at offset: 0x{marker_offset:X} ({marker_offset})")
    
    # Move past the marker
    offset = marker_offset + len(BUFFER_MARKER)
    
    # Skip to vertex count
    offset += SKIP_TO_VERTEX_COUNT
    vertex_count = read_int16_be(data, offset)
    print(f"[INFO] Vertex count offset: 0x{offset:X} ({offset})")
    print(f"[INFO] Vertex count: {vertex_count}")
    offset += 2
    
    # Skip to face count
    offset += SKIP_TO_FACE_COUNT
    face_count = read_int16_be(data, offset)
    print(f"[INFO] Face count offset: 0x{offset:X} ({offset})")
    print(f"[INFO] Face count: {face_count}")
    offset += 2
    
    # Skip to first vertex
    offset += SKIP_TO_FIRST_VERTEX
    vertex_data_start = offset
    print(f"[INFO] First vertex offset: 0x{offset:X} ({offset})")
    
    # Extract vertices AND UVs together (interleaved data)
    vertices = []
    uvs = []
    print(f"\n[DEBUG] First 5 vertices and UV coords (interleaved):")
    for i in range(vertex_count):
        # Read XYZ (3 floats = 12 bytes)
        x = read_float_be(data, offset)
        y = read_float_be(data, offset + 4)
        z = read_float_be(data, offset + 8)
        vertices.append((x, y, z))
        
        # Read UV (2 floats = 8 bytes) - immediately after XYZ
        u = read_float_be(data, offset + 12)
        v = read_float_be(data, offset + 16)
        uvs.append((u, v))
        
        if i < 5:
            print(f"  Entry{i+1} at 0x{offset:X}:")
            print(f"    Vertex: ({x:.6f}, {y:.6f}, {z:.6f})")
            print(f"    UV: ({u:.6f}, {v:.6f})")
        
        # Move to next entry using full stride
        offset += VERTEX_STRIDE
    
    print(f"[INFO] Extracted {len(vertices)} vertices")
    print(f"[INFO] Extracted {len(uvs)} UV coordinates")
    
    # Extract faces (indices)
    # Faces are stored as shorts (int16)
    face_data_start = offset
    print(f"[INFO] Face data offset: 0x{offset:X} ({offset})")
    
    faces = []
    print(f"\n[DEBUG] First 5 faces (as triangles):")
    
    # Assuming triangles (3 indices per face)
    for i in range(face_count):
        idx1 = read_int16_be(data, offset)
        idx2 = read_int16_be(data, offset + 2)
        idx3 = read_int16_be(data, offset + 4)
        faces.append((idx1, idx2, idx3))
        
        if i < 5:
            print(f"  F{i+1}: ({idx1}, {idx2}, {idx3}) at offset 0x{offset:X}")
        
        offset += 6  # 3 shorts = 6 bytes
    
    print(f"[INFO] Extracted {len(faces)} faces")
    
    # Calculate next search offset (after current model data)
    next_search_offset = offset
    
    return {
        'vertices': vertices,
        'uvs': uvs,
        'faces': faces,
        'vertex_count': vertex_count,
        'face_count': face_count
    }, next_search_offset

def write_obj(model_data, output_file):
    """Write model data to .obj file"""
    
    print(f"\n[INFO] Writing to {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write(f"# Extracted from .bmd6model\n")
        f.write(f"# Vertices: {model_data['vertex_count']}\n")
        f.write(f"# Faces: {model_data['face_count']}\n")
        
        if SHADE_SMOOTH:
            f.write(f"# Smooth shading: ON\n")
        
        f.write("\n")
        
        # Write vertices
        for v in model_data['vertices']:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        
        # Write vertex normals if smooth shading is enabled
        if model_data.get('normals'):
            f.write("\n")
            for n in model_data['normals']:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
        
        # Write UV coordinates
        f.write("\n")
        for uv in model_data['uvs']:
            f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")
        
        f.write("\n")
        
        # Write faces with normals if available
        if model_data.get('normals'):
            # Format: f v/vt/vn v/vt/vn v/vt/vn
            for face in model_data['faces']:
                f.write(f"f {face[0]+1}/{face[0]+1}/{face[0]+1} "
                       f"{face[1]+1}/{face[1]+1}/{face[1]+1} "
                       f"{face[2]+1}/{face[2]+1}/{face[2]+1}\n")
        else:
            # Format: f v/vt v/vt v/vt (no normals)
            for face in model_data['faces']:
                f.write(f"f {face[0]+1}/{face[0]+1} {face[1]+1}/{face[1]+1} {face[2]+1}/{face[2]+1}\n")
    
    print(f"[SUCCESS] OBJ file written successfully!")

def main():
    print("\n" + "="*60)
    print("BMD6Model to OBJ Converter")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n[USAGE] Drag and drop a .bmd6model file onto this script")
        print("        or run: python script.py <input_file.bmd6model>")
        input("\nPress Enter to exit...")
        return
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        input("\nPress Enter to exit...")
        return
    
    # Get model name (filename without extension)
    model_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output folder with model name
    output_folder = os.path.join(os.path.dirname(input_file), model_name)
    os.makedirs(output_folder, exist_ok=True)
    print(f"\n[INFO] Output folder: {output_folder}")
    
    # Read entire file once
    with open(input_file, 'rb') as f:
        file_data = f.read()
    
    print(f"[INFO] File size: {len(file_data)} bytes")
    
    # Display transform options
    print(f"\n[TRANSFORM OPTIONS]")
    print(f"  Rotate X -90°: {ROTATE_X_MINUS_90}")
    print(f"  Flip UV Maps: {FLIP_UV_MAPS}")
    print(f"  Flip Face Orientation: {FLIP_FACE_ORIENTATION}")
    print(f"  Shade Smooth: {SHADE_SMOOTH}")
    
    # Extract all models in the file
    part_number = 1
    search_offset = HEADER_SIZE  # Start after header
    total_extracted = 0
    
    while True:
        # Extract model data
        model_data, next_offset = extract_model(file_data, search_offset, part_number)
        
        if model_data is None:
            # No more models found
            break
        
        # Apply transforms
        model_data = apply_transforms(model_data)
        
        # Generate output filename
        output_file = os.path.join(output_folder, f"{model_name}_part{part_number}.obj")
        
        # Write OBJ file
        write_obj(model_data, output_file)
        
        total_extracted += 1
        part_number += 1
        search_offset = next_offset  # Continue searching from where we left off
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Total models extracted: {total_extracted}")
    print(f"Output folder: {output_folder}")
    print(f"{'='*60}\n")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
