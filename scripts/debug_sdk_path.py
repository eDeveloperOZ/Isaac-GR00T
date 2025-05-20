import os
import sys

def list_directory(path, indent=0):
    """Recursively list directory contents."""
    try:
        print(" " * indent + path)
        if os.path.isdir(path):
            for item in os.listdir(path):
                list_directory(os.path.join(path, item), indent + 2)
    except Exception as e:
        print(" " * indent + f"Error accessing {path}: {str(e)}")

if __name__ == "__main__":
    print("Python sys.path:")
    for p in sys.path:
        print(f"  {p}")
    
    print("\nListing contents of /workspace:")
    list_directory("/workspace")
    
    print("\nListing contents of /workspace/Feetech-Servo-SDK:")
    list_directory("/workspace/Feetech-Servo-SDK")