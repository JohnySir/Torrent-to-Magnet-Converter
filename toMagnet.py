import os
import sys
import hashlib
import urllib.parse
import shlex  #<-- New library for parsing the input string

# We use a try-except block to guide the user if the library is missing.
try:
    import bencodepy
except ImportError:
    print("❌ Required library 'bencodepy' not found.")
    print("   Please install it by running: pip install bencodepy")
    input("\nPress Enter to exit.")
    exit()

def create_magnet(torrent_path):
    """
    Creates a magnet link from a .torrent file using a manual parsing method.
    """
    try:
        with open(torrent_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
        info_dict = torrent_data[b'info']
        info_bencoded = bencodepy.encode(info_dict)
        info_hash = hashlib.sha1(info_bencoded).hexdigest()
        magnet_link = f'magnet:?xt=urn:btih:{info_hash}'
        if b'name' in info_dict:
            display_name = info_dict[b'name'].decode('utf-8', 'ignore')
            magnet_link += f'&dn={urllib.parse.quote(display_name)}'
        trackers = set()
        if b'announce' in torrent_data:
            trackers.add(torrent_data[b'announce'].decode('utf-8', 'ignore'))
        if b'announce-list' in torrent_data:
            for tier in torrent_data[b'announce-list']:
                for tracker in tier:
                    trackers.add(tracker.decode('utf-8', 'ignore'))
        for tracker_url in sorted(list(trackers)):
             magnet_link += f'&tr={urllib.parse.quote(tracker_url)}'
        return magnet_link
    except Exception as e:
        print(f"  ⚠️  Could not process {os.path.basename(torrent_path)}: {e}")
        return None

def process_files(file_paths):
    """Processes a list of individual .torrent file paths."""
    magnet_links = []
    first_file_dir = None
    print("\n🔍 Processing provided .torrent files...")

    for file_path in file_paths:
        # The paths might have extra quotes from dragging, so we strip them.
        clean_path = file_path.strip('"')
        if os.path.isfile(clean_path) and clean_path.lower().endswith(".torrent"):
            if first_file_dir is None:
                first_file_dir = os.path.dirname(clean_path)
            
            magnet_link = create_magnet(clean_path)
            if magnet_link:
                magnet_links.append(magnet_link)
                print(f"  ✅ Converted: {os.path.basename(clean_path)}")
        else:
            print(f"  ⚠️  Skipping invalid entry: {file_path}")

    if not magnet_links:
        print("\nNo valid .torrent files were provided or converted.")
        return

    output_file_path = os.path.join(first_file_dir, "magnet.txt")
    save_magnets_to_file(magnet_links, output_file_path)

def process_folder(folder_path):
    """Scans a folder and its subfolders for .torrent files."""
    clean_path = folder_path.strip('"')
    if not os.path.isdir(clean_path):
        print(f"❌ Error: The path '{clean_path}' is not a valid directory.")
        return

    magnet_links = []
    print(f"\n🔍 Scanning '{clean_path}' and subfolders...")
    for root, dirs, files in os.walk(clean_path):
        for filename in files:
            if filename.lower().endswith(".torrent"):
                file_path = os.path.join(root, filename)
                magnet_link = create_magnet(file_path)
                if magnet_link:
                    magnet_links.append(magnet_link)
                    print(f"  ✅ Converted: {filename}")
    
    if not magnet_links:
        print("\nNo .torrent files were found or converted in the folder.")
        return
        
    output_file_path = os.path.join(clean_path, "magnet.txt")
    save_magnets_to_file(magnet_links, output_file_path)

def save_magnets_to_file(links, path):
    """Saves a list of magnet links to a specified file path."""
    try:
        with open(path, "w", encoding='utf-8') as f:
            f.write("\n".join(links))
            f.write("\n")
        print(f"\n✨ Success! {len(links)} magnet links have been saved to:")
        print(f"   {path}")
    except IOError as e:
        print(f"\n❌ Error writing to file: {e}")

if __name__ == "__main__":
    print("📍 --- Torrent to Magnet Converter by Johny --- 📍")
    user_input = input("Drag .torrent files into this window and press Enter:\n(or just press Enter to go into folderMode)\n> ")

    if user_input.strip():
        # User provided file paths. Use shlex to parse them correctly.
        try:
            files_to_process = shlex.split(user_input)
            process_files(files_to_process)
        except ValueError as e:
            print(f"\n❌ Error parsing the input: {e}")
            print("   Please ensure file paths are separated by spaces.")
    else:
        # User pressed Enter, so we fall back to folder mode.
        print("\n💡 No files dragged. Switched to folder scan mode.")
        folder = input("Enter the full path to the folder to scan:\n> ")
        if folder.strip():
            process_folder(folder)
        else:
            print("No folder provided. Exiting.")

    input("\nPress Enter to exit.")
