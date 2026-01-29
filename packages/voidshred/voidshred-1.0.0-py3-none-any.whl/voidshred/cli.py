import os
import sys
import argparse
import secrets

# shred levels: passes per level
PASS_MAP = {1: 3, 2: 7, 3: 15, 4: 25, 5: 35}

def brutal_overwrite(path, passes):
    size = os.path.getsize(path)
    with open(path, "r+b", buffering=0) as f:
        for _ in range(passes):
            f.seek(0)
            written = 0
            while written < size:
                chunk = secrets.token_bytes(4096)
                f.write(chunk)
                written += len(chunk)
            f.flush()
            os.fsync(f.fileno())

def crypto_junk_pass(path):
    size = os.path.getsize(path)
    ephemeral_key = secrets.token_bytes(64)
    with open(path, "r+b", buffering=0) as f:
        written = 0
        while written < size:
            f.write(secrets.token_bytes(4096))
            written += 4096
        f.flush()
        os.fsync(f.fileno())
    del ephemeral_key

def voidshred(path, level):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print(f"file not found: {path}")
        sys.exit(1)

    brutal_overwrite(path, PASS_MAP[level])
    if level >= 3:
        crypto_junk_pass(path)
    brutal_overwrite(path, 3)
    os.remove(path)
    print(f"{path} shredded successfully")

def main():
    parser = argparse.ArgumentParser(description="Secure file shredder")
    parser.add_argument("file", help="Path to file to shred")
    parser.add_argument("-l", "--level", type=int, choices=[1,2,3,4,5], default=3, help="Shred level (1-5)")
    args = parser.parse_args()
    voidshred(args.file, args.level)

if __name__ == "__main__":
    main()
