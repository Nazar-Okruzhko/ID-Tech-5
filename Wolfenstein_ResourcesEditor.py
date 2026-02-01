#!/usr/bin/env python3
"""
Wolfenstein Resources Editor
Recreated Python implementation for editing .resources and .index files
"""

import os
import sys
import struct
import zlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil

class ResourcesEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Resources editor")
        self.root.geometry("1200x600")
        self.root.resizable(True, True)
        
        # Data storage
        self.index_path = None
        self.resources_path = None
        self.files_data = []
        self.current_selection = None
        self.all_files_list = []  # For filtering
        
        # Setup UI
        self.setup_ui()
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Setup drag and drop
        self.setup_drag_drop()
        
    def setup_ui(self):
        # Top buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="Load file", command=self.load_file, 
                 width=15, relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Export all", command=self.export_all,
                 width=15, relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_label = tk.Label(button_frame, text="No file loaded", 
                                     anchor=tk.W, fg='#666')
        self.status_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Main container with PanedWindow for resizable panels
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - file list
        left_frame = tk.Frame(paned, relief=tk.SUNKEN, bd=1, bg='white')
        paned.add(left_frame, width=600)
        
        # Search box
        search_frame = tk.Frame(left_frame, bg='white')
        search_frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(search_frame, text="Search:", bg='white').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_files)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # File listbox with scrollbar
        list_frame = tk.Frame(left_frame, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                       font=('Consolas', 9), 
                                       selectmode=tk.BROWSE,  # BROWSE mode for auto-selection
                                       exportselection=False,  # Keep selection when clicking elsewhere
                                       bg='white')
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Add key bindings for better navigation
        self.file_listbox.bind('<Up>', self.on_arrow_key)
        self.file_listbox.bind('<Down>', self.on_arrow_key)
        self.file_listbox.bind('<Return>', self.on_file_select)
        
        scrollbar.config(command=self.file_listbox.yview)
        
        # Right panel - file details
        right_frame = tk.Frame(paned, relief=tk.SUNKEN, bd=1)
        paned.add(right_frame, width=600)
        
        # Details section
        details_container = tk.Frame(right_frame)
        details_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.details_frame = tk.Frame(details_container)
        self.details_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        
        self.detail_labels = {}
        detail_fields = [
            ("Desc1AsType", "desc1_type"),
            ("Desc2AsUnk1", "desc2_unk"),
            ("FullName", "fullname"),
            ("Name", "name"),
            ("Offset", "offset"),
            ("Size", "size"),
            ("ZSize", "zsize"),
            ("Size unk", "size_unk"),
            ("Index", "index")
        ]
        
        for i, (label, key) in enumerate(detail_fields):
            lbl = tk.Label(self.details_frame, text=label, anchor=tk.W, 
                          font=('Arial', 9))
            lbl.grid(row=i, column=0, sticky=tk.W, pady=3, padx=(0, 10))
            
            # Use Entry widget with readonly state to allow text selection
            value_entry = tk.Entry(self.details_frame, 
                                  font=('Consolas', 9), 
                                  relief=tk.SUNKEN, 
                                  bd=1,
                                  state='readonly',
                                  readonlybackground='white',
                                  fg='black')
            value_entry.grid(row=i, column=1, sticky=tk.EW, pady=3)
            self.detail_labels[key] = value_entry
        
        self.details_frame.columnconfigure(1, weight=1)
        
        # Action buttons
        button_container = tk.Frame(right_frame)
        button_container.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_container, text="Export Decompressed",
                 command=self.export_decompressed, width=30,
                 relief=tk.RAISED, bd=2).pack(fill=tk.X, pady=3)
        
        tk.Button(button_container, text="Export Compressed",
                 command=self.export_compressed, width=30,
                 relief=tk.RAISED, bd=2).pack(fill=tk.X, pady=3)
        
        tk.Button(button_container, text="Import Compressed",
                 command=self.import_compressed, width=30,
                 relief=tk.RAISED, bd=2).pack(fill=tk.X, pady=3)
        
        tk.Button(button_container, text="Import Decompressed",
                 command=self.import_uncompressed, width=30,
                 relief=tk.RAISED, bd=2).pack(fill=tk.X, pady=3)
        
        # Legend at bottom
        legend_frame = tk.Frame(right_frame)
        legend_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(legend_frame, text="●", fg='black',
                font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        tk.Label(legend_frame, text="Uncompressed  ",
                font=('Arial', 9)).pack(side=tk.LEFT)
        
        tk.Label(legend_frame, text="●", fg='red',
                font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        tk.Label(legend_frame, text="Compressed",
                font=('Arial', 9)).pack(side=tk.LEFT)
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality for .resources files"""
        try:
            # Try using tkinterdnd2 if available
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop_file)
        except ImportError:
            # Fallback: enable basic file path handling via window
            # This works on Windows with some limitations
            try:
                self.root.tk.eval('''
                    proc dnd_drop {window files} {
                        set files [string map {\\{ "" \\} ""} $files]
                        event generate $window <<Drop>> -data $files
                    }
                ''')
                self.root.bind('<<Drop>>', self.on_drop_file)
            except:
                # Drag and drop not available, will rely on Load file button
                pass
    
    def on_drop_file(self, event):
        """Handle dropped .resources files"""
        try:
            # Extract file path from event
            if hasattr(event, 'data'):
                files = event.data
            else:
                files = event
            
            # Handle different formats
            if isinstance(files, str):
                # Clean up the path
                files = files.strip('{}').strip()
                file_path = files.split()[0] if ' ' in files else files
            else:
                file_path = str(files)
            
            # Load if it's a .resources file
            if file_path.lower().endswith('.resources') and os.path.isfile(file_path):
                self.load_resources_file(file_path)
            else:
                messagebox.showwarning("Invalid File", 
                    "Please drop a .resources file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dropped file:\n{str(e)}")
    
    def load_file(self):
        """Open file dialog to load .resources file"""
        file_path = filedialog.askopenfilename(
            title="Select .resources file",
            filetypes=[("Resources files", "*.resources"), ("All files", "*.*")]
        )
        if file_path:
            self.load_resources_file(file_path)
    
    def load_resources_file(self, resources_path):
        """Load and parse .resources and .index files"""
        try:
            self.resources_path = Path(resources_path)
            self.index_path = self.resources_path.with_suffix('.index')
            
            if not self.index_path.exists():
                messagebox.showerror("Error", f"Index file not found:\n{self.index_path}")
                return
            
            # Clear existing data
            self.files_data = []
            self.all_files_list = []
            self.file_listbox.delete(0, tk.END)
            self.current_selection = None
            
            # Parse the files
            self.parse_index_and_resources()
            
            # Update UI
            self.root.title(f"Resources editor - {self.resources_path.name}")
            self.status_label.config(text=f"Loaded: {self.resources_path.name} ({len(self.files_data)} files)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def parse_index_and_resources(self):
        """Parse the index and resources files"""
        with open(self.index_path, 'rb') as index_file:
            # Read header
            index_file.seek(0x24)
            num_files = struct.unpack('>I', index_file.read(4))[0]
            unk = struct.unpack('>I', index_file.read(4))[0]
            
            for i in range(num_files):
                try:
                    # Read filename parts (little endian)
                    fn_size1 = struct.unpack('<I', index_file.read(4))[0]
                    fn1 = index_file.read(fn_size1).decode('utf-8', errors='replace')
                    
                    fn_size2 = struct.unpack('<I', index_file.read(4))[0]
                    fn2 = index_file.read(fn_size2).decode('utf-8', errors='replace')
                    
                    namesize = struct.unpack('<I', index_file.read(4))[0]
                    name = index_file.read(namesize).decode('utf-8', errors='replace')
                    
                    # Read file data info (big endian)
                    offset = struct.unpack('>I', index_file.read(4))[0]
                    size = struct.unpack('>I', index_file.read(4))[0]
                    zsize = struct.unpack('>I', index_file.read(4))[0]
                    unksize = struct.unpack('>I', index_file.read(4))[0]
                    
                    # Skip unkdata
                    unksize_calc = unksize * 0x18 + 5
                    index_file.read(int(unksize_calc))
                    
                    # Store file info
                    clean_name = name.strip().replace('\x00', '')
                    if not clean_name:
                        clean_name = f"file_{i:04d}"
                    
                    file_info = {
                        'index': i,
                        'desc1_type': fn1.strip().replace('\x00', ''),
                        'desc2_unk': fn2.strip().replace('\x00', ''),
                        'name': clean_name,
                        'fullname': f"generated/decls/renderparm/{clean_name}",
                        'offset': offset,
                        'size': size,
                        'zsize': zsize,
                        'size_unk': unksize,
                        'is_compressed': size != zsize
                    }
                    
                    self.files_data.append(file_info)
                    self.all_files_list.append((clean_name, file_info['is_compressed']))
                    
                    # Read filenumber for all except last file
                    if i != num_files - 1:
                        index_file.read(4)
                        
                except Exception as e:
                    print(f"Error parsing file {i}: {e}")
                    continue
            
            # Populate listbox
            self.refresh_listbox()
    
    def refresh_listbox(self):
        """Refresh the listbox with current file list"""
        self.file_listbox.delete(0, tk.END)
        for name, is_compressed in self.all_files_list:
            self.file_listbox.insert(tk.END, name)
            if is_compressed:
                self.file_listbox.itemconfig(tk.END, fg='red')
            else:
                self.file_listbox.itemconfig(tk.END, fg='black')
    
    def filter_files(self, *args):
        """Filter file list based on search text"""
        search_text = self.search_var.get().lower()
        
        self.file_listbox.delete(0, tk.END)
        for name, is_compressed in self.all_files_list:
            if search_text in name.lower():
                self.file_listbox.insert(tk.END, name)
                if is_compressed:
                    self.file_listbox.itemconfig(tk.END, fg='red')
                else:
                    self.file_listbox.itemconfig(tk.END, fg='black')
    
    def on_arrow_key(self, event):
        """Handle arrow key navigation"""
        # Let the default behavior happen first, then trigger selection update
        self.root.after(10, lambda: self.on_file_select(None))
        return None  # Allow default behavior
    
    def on_file_select(self, event):
        """Handle file selection in listbox"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        selected_name = self.file_listbox.get(selection[0])
        
        # Find the file info
        for file_info in self.files_data:
            if file_info['name'] == selected_name:
                self.current_selection = file_info
                self.update_details()
                break
    
    def update_details(self):
        """Update the details panel with selected file info"""
        if not self.current_selection:
            return
        
        info = self.current_selection
        
        # Update Entry widgets (need to temporarily enable, update, then disable)
        for key, value in [
            ('desc1_type', info['desc1_type']),
            ('desc2_unk', info['desc2_unk']),
            ('fullname', info['fullname']),
            ('name', info['name']),
            ('offset', f"Hex: 0x{info['offset']:X}"),
            ('size', str(info['size'])),
            ('zsize', str(info['zsize'])),
            ('size_unk', str(info['size_unk'])),
            ('index', str(info['index']))
        ]:
            entry = self.detail_labels[key]
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, value)
            entry.config(state='readonly')
    
    def read_file_data(self, file_info, decompress=True):
        """Read file data from resources file"""
        with open(self.resources_path, 'rb') as f:
            f.seek(file_info['offset'])
            
            if file_info['is_compressed'] and decompress:
                # Read compressed data
                compressed_data = f.read(file_info['zsize'])
                
                # Try to decompress using raw DEFLATE
                try:
                    decompressor = zlib.decompressobj(-15)
                    data = decompressor.decompress(compressed_data)
                    data += decompressor.flush()
                    return data
                except zlib.error:
                    # Try alternative methods
                    try:
                        return zlib.decompress(compressed_data)
                    except:
                        # Try with different wbits
                        for wbits in [15, -zlib.MAX_WBITS]:
                            try:
                                decompressor = zlib.decompressobj(wbits)
                                data = decompressor.decompress(compressed_data)
                                data += decompressor.flush()
                                return data
                            except:
                                continue
                        raise Exception("Failed to decompress data")
            else:
                # Read uncompressed or raw compressed data
                return f.read(file_info['zsize'])
    
    def export_decompressed(self):
        """Export selected file as decompressed"""
        if not self.current_selection:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        try:
            data = self.read_file_data(self.current_selection, decompress=True)
            
            save_path = filedialog.asksaveasfilename(
                title="Save decompressed file",
                initialfile=self.current_selection['name'],
                defaultextension="",
                filetypes=[("All files", "*.*")]
            )
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(data)
                messagebox.showinfo("Success", 
                    f"Exported decompressed file:\n{Path(save_path).name}\n\n"
                    f"Size: {len(data)} bytes")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def export_compressed(self):
        """Export selected file as compressed (raw)"""
        if not self.current_selection:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        try:
            data = self.read_file_data(self.current_selection, decompress=False)
            
            save_path = filedialog.asksaveasfilename(
                title="Save compressed file",
                initialfile=self.current_selection['name'],
                defaultextension="",
                filetypes=[("All files", "*.*")]
            )
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(data)
                messagebox.showinfo("Success",
                    f"Exported compressed file:\n{Path(save_path).name}\n\n"
                    f"Size: {len(data)} bytes")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def export_all(self):
        """Export all files decompressed to a folder"""
        if not self.files_data:
            messagebox.showwarning("Warning", "No files loaded")
            return
        
        try:
            output_dir = Path(self.resources_path).with_suffix('')
            output_dir.mkdir(exist_ok=True)
            
            success_count = 0
            failed_count = 0
            failed_files = []
            
            for file_info in self.files_data:
                try:
                    data = self.read_file_data(file_info, decompress=True)
                    output_path = output_dir / file_info['name']
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'wb') as f:
                        f.write(data)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_files.append(file_info['name'])
            
            msg = f"Exported {success_count} files to:\n{output_dir}\n\n"
            if failed_count > 0:
                msg += f"Failed: {failed_count} files\n"
                if len(failed_files) <= 10:
                    msg += "\nFailed files:\n" + "\n".join(failed_files[:10])
            
            messagebox.showinfo("Export Complete", msg)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export all:\n{str(e)}")
    
    def import_compressed(self):
        """Import a file and store it compressed in .resources"""
        if not self.current_selection:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select file to import (will be compressed)",
            filetypes=[("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Read the new file data
            with open(file_path, 'rb') as f:
                new_data = f.read()
            
            # Ask if the file is already compressed
            already_compressed = messagebox.askyesno(
                "File Status",
                "Is this file already compressed with DEFLATE?\n\n"
                "Yes = File is pre-compressed (use as-is)\n"
                "No = Compress it now"
            )
            
            if already_compressed:
                # Use as-is (already compressed)
                compressed_data = new_data
                # Try to get decompressed size
                try:
                    decompressor = zlib.decompressobj(-15)
                    decompressed = decompressor.decompress(compressed_data)
                    decompressed += decompressor.flush()
                    decompressed_size = len(decompressed)
                except:
                    # Can't decompress - use compressed size as estimate
                    decompressed_size = len(compressed_data)
                    messagebox.showwarning("Warning", 
                        "Could not decompress to verify size. Using compressed size as estimate.")
            else:
                # Compress the uncompressed file
                compress_obj = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
                compressed_data = compress_obj.compress(new_data)
                compressed_data += compress_obj.flush()
                decompressed_size = len(new_data)
            
            compressed_size = len(compressed_data)
            
            # Align to 16-byte boundary
            alignment = 16
            padding_needed = (alignment - (compressed_size % alignment)) % alignment
            padded_data = compressed_data + (b'\x00' * padding_needed)
            final_size = len(padded_data)
            
            # Confirm
            confirm_msg = (
                f"Import as COMPRESSED:\n\n"
                f"Source: {Path(file_path).name}\n"
                f"Decompressed size: {decompressed_size} bytes\n"
                f"Compressed size: {compressed_size} bytes\n"
                f"With padding: {final_size} bytes\n"
                f"Padding added: {padding_needed} bytes\n\n"
                f"Replace: {self.current_selection['name']}\n"
                f"Current compressed size: {self.current_selection['zsize']} bytes\n"
                f"Current decompressed size: {self.current_selection['size']} bytes\n\n"
                f"Size change: {final_size - self.current_selection['zsize']:+d} bytes\n\n"
                f"Backups will be created.\n\n"
                f"Continue?"
            )
            
            if not messagebox.askyesno("Confirm Import Compressed", confirm_msg):
                return
            
            # Update files
            self.update_resources_and_index(
                self.current_selection,
                padded_data,
                decompressed_size,
                final_size
            )
            
            # Reload
            self.load_resources_file(str(self.resources_path))
            
            messagebox.showinfo("Success",
                f"File imported as COMPRESSED!\n\n"
                f"Backups created:\n"
                f"- {self.resources_path.name}.backup\n"
                f"- {self.index_path.name}.backup")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import:\n{str(e)}")
    
    def import_uncompressed(self):
        """Import a file and store it uncompressed in .resources"""
        if not self.current_selection:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select file to import (will be stored uncompressed)",
            filetypes=[("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Read the file data
            with open(file_path, 'rb') as f:
                new_data = f.read()
            
            uncompressed_size = len(new_data)
            
            # Align to 16-byte boundary
            alignment = 16
            padding_needed = (alignment - (uncompressed_size % alignment)) % alignment
            padded_data = new_data + (b'\x00' * padding_needed)
            final_size = len(padded_data)
            
            # Confirm
            confirm_msg = (
                f"Import as UNCOMPRESSED:\n\n"
                f"Source: {Path(file_path).name}\n"
                f"File size: {uncompressed_size} bytes\n"
                f"With padding: {final_size} bytes\n"
                f"Padding added: {padding_needed} bytes\n\n"
                f"Replace: {self.current_selection['name']}\n"
                f"Current compressed size: {self.current_selection['zsize']} bytes\n"
                f"Current decompressed size: {self.current_selection['size']} bytes\n\n"
                f"Size change: {final_size - self.current_selection['zsize']:+d} bytes\n\n"
                f"Note: File will be stored UNCOMPRESSED (size = zsize)\n\n"
                f"Backups will be created.\n\n"
                f"Continue?"
            )
            
            if not messagebox.askyesno("Confirm Import Uncompressed", confirm_msg):
                return
            
            # For uncompressed: size and zsize are the same (both are final_size)
            self.update_resources_and_index(
                self.current_selection,
                padded_data,
                final_size,  # size = final_size (uncompressed)
                final_size   # zsize = final_size (same, meaning uncompressed)
            )
            
            # Reload
            self.load_resources_file(str(self.resources_path))
            
            messagebox.showinfo("Success",
                f"File imported as UNCOMPRESSED!\n\n"
                f"Backups created:\n"
                f"- {self.resources_path.name}.backup\n"
                f"- {self.index_path.name}.backup")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import:\n{str(e)}")
    
    def update_resources_and_index(self, file_info, new_data, decompressed_size, final_zsize):
        """Update both .resources and .index files with new data
        
        Args:
            file_info: Dictionary with current file information
            new_data: The actual bytes to write (already compressed and padded)
            decompressed_size: Uncompressed size for index 'size' field  
            final_zsize: Compressed+padded size for index 'zsize' field (should equal len(new_data))
        """
        # Create backups
        backup_resources = self.resources_path.with_suffix('.resources.backup')
        backup_index = self.index_path.with_suffix('.index.backup')
        
        shutil.copy2(self.resources_path, backup_resources)
        shutil.copy2(self.index_path, backup_index)
        
        try:
            # Read current resources file
            with open(self.resources_path, 'rb') as f:
                resources_data = bytearray(f.read())
            
            # Validate that final_zsize matches actual data length
            if len(new_data) != final_zsize:
                raise ValueError(f"Data length mismatch: got {len(new_data)}, expected {final_zsize}")
            
            old_zsize = file_info['zsize']
            new_zsize = len(new_data)  # This is the padded size
            size_diff = new_zsize - old_zsize
            
            offset = file_info['offset']
            
            print(f"\n=== Import Debug Info ===")
            print(f"File: {file_info['name']}")
            print(f"Index: {file_info['index']}")
            print(f"Offset: 0x{offset:X}")
            print(f"Old size (decompressed): {file_info['size']}")
            print(f"Old zsize (compressed): {old_zsize} (0x{old_zsize:X})")
            print(f"New size (decompressed): {decompressed_size}")
            print(f"New zsize (compressed+padded): {new_zsize} (0x{new_zsize:X})")
            print(f"Size diff: {size_diff:+d} (0x{size_diff:X})")
            print(f"========================\n")
            
            # Create new resources data
            new_resources = bytearray()
            
            # Part 1: Everything before our file
            new_resources.extend(resources_data[:offset])
            
            # Part 2: Our new data (already compressed and padded)
            new_resources.extend(new_data)
            
            # Part 3: Everything after our file
            after_offset = offset + old_zsize
            new_resources.extend(resources_data[after_offset:])
            
            # Write updated resources file
            with open(self.resources_path, 'wb') as f:
                f.write(new_resources)
            
            print(f"Resources file updated: {len(resources_data)} -> {len(new_resources)} bytes")
            
            # Update index file
            # Parameters: decompressed_size goes to 'size', new_zsize goes to 'zsize'
            self.update_index_metadata(file_info, decompressed_size, new_zsize, size_diff)
            
        except Exception as e:
            # Restore backups on error
            print(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()
            if backup_resources.exists():
                shutil.copy2(backup_resources, self.resources_path)
            if backup_index.exists():
                shutil.copy2(backup_index, self.index_path)
            raise Exception(f"Failed to update files: {e}")
    
    def update_index_metadata(self, file_info, new_size, new_zsize, offset_diff):
        """Update the .index file with new metadata"""
        with open(self.index_path, 'rb') as f:
            index_data = bytearray(f.read())
        
        # Parse through index to find positions
        pos = 0x24
        num_files = struct.unpack('>I', index_data[pos:pos+4])[0]
        pos += 8  # Skip num_files and unk fields
        
        for i in range(num_files):
            # Save the starting position of this file entry
            file_entry_start = pos
            
            # Read through the entry structure to find metadata positions
            # Filename part 1 (little endian)
            fn_size1 = struct.unpack('<I', index_data[pos:pos+4])[0]
            pos += 4 + fn_size1
            
            # Filename part 2 (little endian)
            fn_size2 = struct.unpack('<I', index_data[pos:pos+4])[0]
            pos += 4 + fn_size2
            
            # Actual filename (little endian)
            namesize = struct.unpack('<I', index_data[pos:pos+4])[0]
            pos += 4 + namesize
            
            # Now we're at the metadata section (all big endian)
            offset_pos = pos
            size_pos = pos + 4
            zsize_pos = pos + 8
            unksize_pos = pos + 12
            
            # Read current values
            current_offset = struct.unpack('>I', index_data[offset_pos:offset_pos+4])[0]
            current_size = struct.unpack('>I', index_data[size_pos:size_pos+4])[0]
            current_zsize = struct.unpack('>I', index_data[zsize_pos:zsize_pos+4])[0]
            unksize = struct.unpack('>I', index_data[unksize_pos:unksize_pos+4])[0]
            
            if i == file_info['index']:
                # Update THIS file's size and zsize (big endian)
                struct.pack_into('>I', index_data, size_pos, new_size)
                struct.pack_into('>I', index_data, zsize_pos, new_zsize)
                print(f"Updated file {i}: size={new_size}, zsize={new_zsize}")
                
            elif i > file_info['index'] and offset_diff != 0:
                # Update offsets for files AFTER the modified file (big endian)
                new_offset = current_offset + offset_diff
                struct.pack_into('>I', index_data, offset_pos, new_offset)
                print(f"Updated file {i} offset: {current_offset} -> {new_offset}")
            
            # Move past the metadata fields (16 bytes: offset, size, zsize, unksize)
            pos += 16
            
            # Skip the unkdata section
            unksize_calc = int(unksize * 0x18 + 5)
            pos += unksize_calc
            
            # Skip filenumber separator (4 bytes) except for last file
            if i != num_files - 1:
                pos += 4
        
        # Write updated index
        with open(self.index_path, 'wb') as f:
            f.write(index_data)
        
        print(f"Index file updated successfully")

def main():
    """Main entry point"""
    # Try to use TkinterDnD for better drag and drop support
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        # Fall back to regular Tk
        root = tk.Tk()
    
    app = ResourcesEditor(root)
    
    # Handle command line arguments (drag & drop support)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.isfile(file_path) and file_path.lower().endswith('.resources'):
            root.after(100, lambda: app.load_resources_file(file_path))
    
    root.mainloop()

if __name__ == "__main__":
    main()
