# Wolfenstein-Resources
<img width="859" height="735" alt="Screenshot (670) - Copy" src="https://github.com/user-attachments/assets/db96f949-7442-4ee4-af86-b05fd8881c06" />

A legendary collection python script to extract all of the assets from WTNO/WTOB, including 3D models, textures, sounds, scripts and even declaration files, Assets are stored in proprietary formats like bmd6model, bmodel, bimage, idxma, decl. Turns out the Decompression method was Deflate RFC 1951 [RAW]. Supports loading for both .index and .resources files, tested with WTNO and WTOB, extracted all the resources from there already!


# Usage & Workaraounds
<img width="801" height="492" alt="Screenshot (663) - Copy" src="https://github.com/user-attachments/assets/c034b969-6c02-489f-9881-687e743d848f" />

Drag and drop any of the chunk#.resources files form WTNO/WTOB the script will extract all of the resources into corresponding directory and show statistis in the end


# .BMD6MODEL/.BMODEL
<img width="1000" height="580" alt="Screenshot(970) thumb png cb41accf00e143ff30abc988ab1d209b" src="https://github.com/user-attachments/assets/e68677ae-0350-43e8-b75e-0aa105d31e4f" />

Drag and drop your .bmd6model files into the tool and it will convert it into multiple OBJ parts, game-ready.

# .BIMAGE
<img width="1000" height="91" alt="loading_icon_anim thumb png ce61f5d58bf00701d86f8bc2d2e673b4" src="https://github.com/user-attachments/assets/275f22ad-250a-4bb8-90d2-872b4eaf27ae" />

Drag and drop your bimage files into the script and it will convert it into PNG files.

# STREAMED.RESOURCES
<img width="1000" height="656" alt="Screenshot(965) thumb png c09c1d8af0948c551ca36af743253048" src="https://github.com/user-attachments/assets/3a4f81a8-cad6-47b5-815c-a2c95bc3e381" />

Drag and drop .index files into the script, it will automatically parse streamed.resources and extract sounds.

# VIRTUALTEXTURES
<img width="1920" height="1080" alt="Screenshot (974)" src="https://github.com/user-attachments/assets/aa6b0779-1fd3-4417-b534-f1c86f65d724" />

The vtex method works flawlessly extracts massive Virtualtextures but requires Windows 7 Virtual Machine, with disabled ASLR (MoveImages=0), VCRuntime library and Hundreds of Terabytes of space for Level architecture textures.
