import requests
import threading
import random
import time
from queue import Queue
import urllib.parse
import argparse
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='BruteMe - A powerful brute force request tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  bruteme.py -r request.txt -w wordlist.txt
  bruteme.py -r request.txt -w wordlist.txt --threads 20
  bruteme.py -r request.txt -w wordlist.txt --base-url http://example.com
''')
    
    parser.add_argument('-r', '--request', required=True, help='Path to the request file')
    parser.add_argument('-w', '--wordlist', required=True, help='Path to the wordlist file')
    parser.add_argument('--base-url', help='Base URL (optional, will try to extract from request)')
    parser.add_argument('--threads', type=int, default=50, help='Number of threads (default: 50)')
    
    return parser.parse_args()

# Generate random IP for X-Forwarded-For
def random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

# Load request template from Burp file and extract fields
def load_request_template(file_path, base_url=None):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    method, url, headers, body = None, None, {}, []
    fields = []
    is_body = False
    
    # Try to extract base URL from Origin or Host header if not provided
    if not base_url:
        for line in lines:
            line = line.strip()
            if line.startswith("Origin:"):
                base_url = line.split(": ")[1]
                break
            elif line.startswith("Host:"):
                base_url = "http://" + line.split(": ")[1]
                break
    
    for line in lines:
        line = line.strip()
        if not line:
            is_body = True
            continue
        
        if not is_body:
            if line.startswith("GET") or line.startswith("POST"):
                parts = line.split()
                method, url = parts[0], parts[1]
                if not url.startswith("http"):
                    url = base_url.rstrip("/") + url
            elif ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value
        else:
            body.append(line)
            for param in line.split("&"):
                if "=" in param:
                    fields.append(param.split("=")[0])
    
    return method, url, headers, "\n".join(body), list(set(fields))

# Function to perform brute force
def brute_force(url, method, headers, body, field, wordlist_chunk, results_queue):
    session = requests.Session()

    def send_request(method, url, headers, data):
        req = requests.Request(method, url, headers=headers, data=data)
        prepared = session.prepare_request(req)
        response = session.send(prepared, timeout=5, allow_redirects=False)
        return response

    for word in wordlist_chunk:
        mod_headers = headers.copy()
        mod_headers["X-Forwarded-For"] = random_ip()
        mod_headers["Referer"] = url

        try:
            body_params = dict(param.split("=", 1) for param in body.split("&") if "=" in param)
            if field not in body_params:
                print(f"[ERROR] Field '{field}' not found in request body.")
                return

            body_params[field] = word
            mod_body = "&".join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in body_params.items()])

        except ValueError as e:
            print(f"[ERROR] Failed to parse request body: {e}")
            return

        try:
            response = send_request(method, url, mod_headers, mod_body)
            results_queue.put((url, word, response.status_code, len(response.text), response.text))
        
        except requests.RequestException as e:
            continue

# Intelligent result filtering
def analyze_results(results):
    # Group responses by status code
    status_groups = {}
    for url, word, status, length, body in results:
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append((url, word, status, length, body))
    
    minority_results = []
    
    # For each status code, find minority cases
    for status, responses in status_groups.items():
        # Group by length within this status code
        length_groups = {}
        for response in responses:
            length = response[3]  # length is at index 3
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(response)
        
        # Find minority cases for this status code
        if len(length_groups) > 1:  # Only if there are multiple lengths
            majority_length = max(length_groups.items(), key=lambda x: len(x[1]))[0]
            for length, responses in length_groups.items():
                if length != majority_length:
                    minority_results.extend(responses)
    
    return minority_results

# Main function
def main():
    args = parse_arguments()
    
    try:
        method, url, headers, body, fields = load_request_template(args.request, args.base_url)
    except Exception as e:
        print(f"[ERROR] Failed to load request file: {e}")
        sys.exit(1)
    
    if not fields:
        print("[ERROR] No fields found in request body.")
        sys.exit(1)
    
    print("\nAvailable fields for brute force:")
    for idx, field in enumerate(fields):
        print(f"[{idx + 1}] {field}")
    
    field_choice = int(input("Select a field number: ")) - 1
    if field_choice < 0 or field_choice >= len(fields):
        print("[ERROR] Invalid choice.")
        sys.exit(1)
    field = fields[field_choice]
    
    try:
        with open(args.wordlist, 'r', encoding='utf-8') as f:
            wordlist = [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"[ERROR] Failed to load wordlist: {e}")
        sys.exit(1)
    
    # Split wordlist into chunks for each thread
    chunk_size = len(wordlist) // args.threads
    wordlist_chunks = [wordlist[i:i + chunk_size] for i in range(0, len(wordlist), chunk_size)]
    
    results_queue = Queue()
    threads = []
    
    print(f"\nStarting brute force with {args.threads} threads...")
    
    # Start threading with different chunks
    for chunk in wordlist_chunks:
        t = threading.Thread(target=brute_force, args=(url, method, headers, body, field, chunk, results_queue))
        t.start()
        threads.append(t)
    
    # Progress bar
    total_words = len(wordlist)
    processed_words = 0
    while any(t.is_alive() for t in threads):
        # Update progress based on queue size
        current_size = results_queue.qsize()
        if current_size > processed_words:
            processed_words = current_size
            progress = (processed_words / total_words) * 100
            print(f"\rProgress: [{int(progress/2)*'='}>{int((100-progress)/2)*' '}] {processed_words}/{total_words} ({progress:.1f}%)", end='')
        time.sleep(0.1)
    
    print("\n")  # New line after progress bar
    
    for t in threads:
        t.join()
    
    # Process results
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    minority_results = analyze_results(results)
    
    print("\n[+] Minority cases by status code:")
    current_status = None
    for url, word, status, length, body in minority_results:
        if current_status != status:
            current_status = status
            print(f"\nStatus Code: {status}")
            print("-" * 50)
        print(f"Word: {word}")
        print(f"Length: {length}")
        print("Response Body:")
        print(body)
        print("-" * 50)

if __name__ == "__main__":
    main()
