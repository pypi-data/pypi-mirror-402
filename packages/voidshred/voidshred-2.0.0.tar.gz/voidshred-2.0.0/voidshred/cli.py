import os
import sys
import argparse
import secrets

# shred levels: passes per level
PASS_MAP = {1: 3, 2: 7, 3: 15, 4: 25, 5: 35}

def brutal_overwrite(path, passes):
    """Overwrite file with random bytes multiple times."""
    try:
        size = os.path.getsize(path)
        with open(path, "r+b", buffering=0) as f:
            for _ in range(passes):
                f.seek(0)
                written = 0
                while written < size:
                    chunk = secrets.token_bytes(min(4096, size - written))
                    f.write(chunk)
                    written += len(chunk)
                f.flush()
                os.fsync(f.fileno())
    except Exception as e:
        print(f"Error overwriting {path}: {e}")

def crypto_junk_pass(path):
    """Optional extra pass with ephemeral crypto."""
    try:
        size = os.path.getsize(path)
        ephemeral_key = secrets.token_bytes(64)
        with open(path, "r+b", buffering=0) as f:
            written = 0
            while written < size:
                f.write(secrets.token_bytes(min(4096, size - written)))
                written += 4096
            f.flush()
            os.fsync(f.fileno())
        del ephemeral_key
    except Exception as e:
        print(f"Error in crypto pass for {path}: {e}")

def voidshred(path, level):
    """Shred file or folder recursively."""
    path = os.path.abspath(path)

    if os.path.isfile(path):
        brutal_overwrite(path, PASS_MAP[level])
        if level >= 3:
            crypto_junk_pass(path)
        brutal_overwrite(path, 3)
        try:
            os.remove(path)
            print(f"Shredded file: {path}")
        except Exception as e:
            print(f"Failed to remove file {path}: {e}")

    elif os.path.isdir(path):
        # Recursively shred folder contents
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                voidshred(file_path, level)
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.rmdir(dir_path)
                    print(f"Removed folder: {dir_path}")
                except Exception as e:
                    print(f"Failed to remove folder {dir_path}: {e}")
        try:
            os.rmdir(path)
            print(f"Shredded folder: {path}")
        except Exception as e:
            print(f"Failed to remove folder {path}: {e}")

    else:
        print(f"Path not found: {path}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Secure file/folder shredder")
    parser.add_argument("target", help="Path to file or folder to shred")
    parser.add_argument("-l", "--level", type=int, choices=[1,2,3,4,5], default=3,
                        help="Shred level (1-5)")
    args = parser.parse_args()
    voidshred(args.target, args.level)

if __name__ == "__main__":
    main()
