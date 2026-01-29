import os
import sys
import argparse
import mimetypes
import pyperclip


IGNORE_DIRS = {'.git', 'venv', '.venv', '__pycache__', 'node_modules', '.idea', '.vscode'}

def is_binary(file_path):
    """
    Check if a file is binary.
    Uses mimetypes as a first pass, then checks for null bytes in the first 1024 bytes.
    """
    # Guess based on extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and not mime_type.startswith('text'):
        pass

    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            return False
    except Exception:
        return True

def get_file_content(file_path, root_dir):
    """Read text file content and format it with a header."""
    try:
        rel_path = os.path.relpath(file_path, root_dir)
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            return f"\n\n### FILE: {rel_path}\n```\n{content}\n```"
    except Exception as e:
        return f"\n\n### FILE: {rel_path} (Skipped: {e})"

def main():
    parser = argparse.ArgumentParser(description="Parse directory, flatten text files, and copy to clipboard.")
    parser.add_argument("directory", nargs="?", default=".", help="Root directory to parse (default: current directory)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Enable recursive scanning (default: off)")
    parser.add_argument("--max-len", type=int, default=100000, help="Maximum text length before truncation (default: 100000)")
    
    args = parser.parse_args()
    
    root_dir = os.path.abspath(args.directory)
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        sys.exit(1)
        
    accumulated_text = ""
    file_count = 0
    truncated = False
    
    scan_type = "Recursive scan" if args.recursive else "Flat scan"
    print(f"{scan_type} of '{root_dir}'...")

    # Collect all files first to sort them (ensure deterministic output)
    files_to_process = []
    
    if args.recursive:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Modify dirnames in-place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            
            for f in filenames:
                files_to_process.append(os.path.join(dirpath, f))
    else:
        # Non-recursive: just list files in root_dir
        for item in os.listdir(root_dir):
            full_path = os.path.join(root_dir, item)
            if os.path.isfile(full_path):
                files_to_process.append(full_path)
            
    files_to_process.sort()

    for full_path in files_to_process:
        if is_binary(full_path):
            continue
            
        text_chunk = get_file_content(full_path, root_dir)
        
        if len(accumulated_text) + len(text_chunk) > args.max_len:
            remaining_space = args.max_len - len(accumulated_text)
            if remaining_space > 0:
                accumulated_text += text_chunk[:remaining_space]
            
            accumulated_text += "\n\n\n[... CONTENT TRUNCATED: MAX LENGTH EXCEEDED. MORE FILES EXIST ...]"
            print(f"Warning: Content exceeded {args.max_len} characters. Truncated output.")
            truncated = True
            break
        
        accumulated_text += text_chunk
        file_count += 1

    if not accumulated_text:
        print("No text files found or all were filtered.")
        return

    try:
        pyperclip.copy(accumulated_text)
        status = "Copied (Truncated)" if truncated else "Copied"
        print(f"{status}! {len(accumulated_text)} characters from {file_count} files are in your clipboard.")
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        # Fallback: could write to a temp file or just print suggestion
        print("Could not access clipboard. Please ensure you have a clipboard manager (like xclip or xsel on Linux).")

if __name__ == "__main__":
    main()
