import sys

def main():
    """Main entry point for uvx packaging"""
    print("DEBUG: debug_server.py entering main section for FastAPI...", file=sys.stderr, flush=True)
    try:
        # mcp.run() # Commented out original MCP run
        print("DEBUG: Attempting to start uvicorn server...", file=sys.stderr, flush=True)
        from server import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        print("DEBUG: uvicorn.run() completed (should not happen if server runs indefinitely).", file=sys.stderr, flush=True)
    except Exception as e_run:
        print(f"DEBUG: ERROR during uvicorn.run(): {e_run}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise
    except BaseException as be_run: # Catching BaseException like KeyboardInterrupt
        print(f"DEBUG: BASE EXCEPTION during uvicorn.run() (e.g., KeyboardInterrupt): {be_run}", file=sys.stderr, flush=True)
        # traceback.print_exc(file=sys.stderr) # Optional: might be too verbose for Ctrl+C
        # raise # Re-raise if you want the process to exit with an error code from the BaseException
    finally:
        print("DEBUG: debug_server.py finished.", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()