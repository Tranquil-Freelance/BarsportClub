import subprocess
import time
import requests
import sys
import os

def main():
    # Start server on port 8005
    proc = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', '8005', '--reload'
    ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Wait for server to start
        time.sleep(5)
        # Test route
        resp = requests.get('http://localhost:8005/api/standings')
        if resp.status_code == 200:
            data = resp.json()
            print('SUCCESS: Route /api/standings works')
            # Check xpts not zero
            first = data[0]
            if first.get('xpts', 0.0) != 0.0:
                print(f'✓ Real data: xpts = {first["xpts"]}')
            else:
                print('✗ WARNING: xpts is zero')
        else:
            print(f'FAIL: status {resp.status_code}, {resp.text}')
        # Kill server
        proc.terminate()
        proc.wait()
    except Exception as e:
        print(f'Error: {e}')
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    main()