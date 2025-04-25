import runpod
import subprocess
import os
import json

def handler(event):
    """
    This generator processes incoming requests to your Serverless endpoint and
    streams the output of the requested bash command back to the caller.
    Each yielded dictionary is delivered to the client in real-time when the
    endpoint is configured for streaming.
    """

    print("Worker Start")
    input_data = event.get("input", {})

    # Get the command to execute
    command = input_data.get("command")

    if not command:
        # Immediately stream an error message if no command was supplied
        yield {
            "error": "No command provided in the input",
            "exit_code": 1
        }
        return

    print(f"Executing command: {command}")

    try:
        # Start the subprocess and stream combined stdout & stderr
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout for ordering
            text=True,
            bufsize=1                 # Line-buffered
        )

        # Yield output in real-time
        for line in iter(process.stdout.readline, ""):
            yield {"output": line.rstrip("\n")}

        # Wait for the process to finish and capture its exit code
        process.wait()
        yield {"exit_code": process.returncode}

    except Exception as e:
        yield {
            "error": str(e),
            "exit_code": 1
        }

# Start the Serverless function when the script is run
if __name__ == '__main__':
    runpod.serverless.start({
        'handler': handler,
        'return_aggregate_stream': True  # Enable streaming results back to the caller
    })