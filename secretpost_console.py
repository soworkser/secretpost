"""
SecretPost — Console Version
Works on macOS, Windows, Linux
"""

import sys
import getpass
from crypto_core import encrypt, decrypt, validate_code

BANNER = r"""
 ____                     _   ____           _
/ ___|  ___  ___ _ __ ___| |_|  _ \ ___  ___| |_
\___ \ / _ \/ __| '__/ _ \ __| |_) / _ \/ __| __|
 ___) |  __/ (__| | |  __/ |_|  __/ (_) \__ \ |_
|____/ \___|\___|_|  \___|\__|_|   \___/|___/\__|

  AES-256-GCM  |  end-to-end encrypted messaging
"""

LINE = "─" * 52


def prompt_code() -> str:
    while True:
        code = getpass.getpass("  🔑  Secret key (10 digits, hidden): ").strip()
        if validate_code(code):
            return code
        print("  ✖   Must be exactly 10 digits. Try again.")


def mode_encrypt():
    print(f"\n  {LINE}")
    print("  MODE: ENCRYPT")
    print(f"  {LINE}")

    code = prompt_code()

    print("\n  Enter your message (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            lines.pop()
            break
        lines.append(line)
    plaintext = "\n".join(lines).strip()

    if not plaintext:
        print("  ✖   Empty message. Aborted.")
        return

    print("\n  ⏳  Encrypting…")
    try:
        result = encrypt(plaintext, code)
    except Exception as e:
        print(f"  ✖   Error: {e}")
        return

    print(f"\n  {LINE}")
    print("  ✔   ENCRYPTED MESSAGE (copy everything below):")
    print(f"  {LINE}")
    print(f"\n{result}\n")
    print(f"  {LINE}")
    print("  Send the encrypted text via email. The recipient")
    print("  needs the same 10-digit key to decrypt it.")


def mode_decrypt():
    print(f"\n  {LINE}")
    print("  MODE: DECRYPT")
    print(f"  {LINE}")

    code = prompt_code()

    print("\n  Paste the encrypted message (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            lines.pop()
            break
        lines.append(line)
    ciphertext = "\n".join(lines).strip()

    if not ciphertext:
        print("  ✖   Nothing pasted. Aborted.")
        return

    print("\n  ⏳  Decrypting…")
    try:
        result = decrypt(ciphertext, code)
    except ValueError as e:
        print(f"\n  ✖   {e}")
        return

    print(f"\n  {LINE}")
    print("  ✔   DECRYPTED MESSAGE:")
    print(f"  {LINE}\n")
    print(result)
    print(f"\n  {LINE}")


def main():
    print(BANNER)

    while True:
        print(f"  {LINE}")
        print("  [1]  Encrypt a message")
        print("  [2]  Decrypt a message")
        print("  [0]  Exit")
        print(f"  {LINE}")

        choice = input("  Choose: ").strip()

        if choice == "1":
            mode_encrypt()
        elif choice == "2":
            mode_decrypt()
        elif choice == "0":
            print("\n  Goodbye.\n")
            sys.exit(0)
        else:
            print("  ✖   Invalid choice.")

        print()


if __name__ == "__main__":
    main()
