"""Example usage of rapfiles."""

import asyncio
import tempfile
import os

try:
    from rapfiles import read_file, write_file

    async def main():
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            test_file = f.name
            f.write("Hello, RAP!")

        try:
            # Read file asynchronously
            print(f"Reading {test_file}...")
            content = await read_file(test_file)
            print(f"Content: {content}")

            # Write file asynchronously
            print(f"\nWriting to {test_file}...")
            await write_file(test_file, "Hello from RAP filesystem I/O!")

            # Read again to verify
            print("Reading again...")
            content = await read_file(test_file)
            print(f"New content: {content}")

        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.unlink(test_file)
                print(f"\nCleaned up {test_file}")

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError:
    print("Error: rapfiles not installed. Install with: pip install -e .")
