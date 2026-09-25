import sys
import traceback

print("=" * 60)
print("STARTING DIAGNOSTIC RUNNER")
print("=" * 60)
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("-" * 60)

try:
    print("Attempting to execute main.py directly...\n")
    
    # Read and execute main.py in the main module scope
    with open("main.py", "r", encoding="utf-8") as f:
        code = compile(f.read(), "main.py", "exec")
        exec(code, {"__name__": "__main__"})

except Exception as e:
    print("\n" + "!" * 60)
    print("CRASH DETECTED! HERE IS THE EXACT ERROR:")
    print("!" * 60 + "\n")
    
    # Print the full error stack trace to terminal
    traceback.print_exc()
    
    # Also save the error to error_log.txt
    with open("error_log.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
        
    print("\n" + "=" * 60)
    print("Error saved to 'error_log.txt' in your project folder.")
    print("=" * 60)

input("\nPress ENTER to exit...")