# BruteMe 🛠️

**BruteMe** is a powerful, flexible, and extendable brute-force tool built for security testing of web applications. It leverages user-supplied HTTP request templates (e.g. exported from Burp Suite) and performs multi-threaded brute-force attacks on specified parameters, such as login forms or any other injectable input field.

---

## 🚀 Features

- 🔍 **Smart Field Detection**  
  Automatically parses the HTTP request body and detects parameters that can be fuzzed or brute-forced (e.g. `username`, `email`, `password`, etc.). You don't need to hardcode anything—just choose which field to test!

- ⚙️ **Custom Request Templates**  
  Simply export your request from Burp Suite or a similar tool. This gives full control over headers, methods (GET/POST), and body.

- ⚡ **Multi-threaded Execution**  
  Built-in support for multi-threaded execution to speed up large wordlist processing.

- 🧠 **Minority Response Filtering**  
  Automatically highlights responses that deviate from the majority (status code or length), helping you find valid logins or unusual behavior easily.

- 🧺 **Fuzzing Support**  
  While BruteMe is built mainly for login brute-forcing, the design makes it ideal for fuzzing arbitrary parameters, such as:
  - Searching for hidden admin pages via query parameters.
  - Fuzzing email/password recovery fields.
  - Testing any field for logic bugs or weak input validation.

---

## 📦 Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/bruteme.git
   cd bruteme
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Usage

```bash
python bruteme.py -r request.txt -w wordlist.txt
```

Optional flags:

- `--threads <number>`: Set number of threads (default: 50)
- `--base-url <url>`: Manually set base URL (if not found in headers)

### 📂 Example Burp-style Request (request.txt)
```
POST /login HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

username=admin&password=FUZZ
```
BruteMe will analyze this request and detect `username` and `password` as fuzzable fields.

---

## 📅 Future Plans
- [ ] Support for GET parameter fuzzing
- [ ] Dictionary rotation across multiple fields
- [ ] Integration with proxy tools (like Burp Collaborator)
- [ ] Better response visualization (e.g. HTML diffing, color-coding)

---

## 🚫 Disclaimer
This tool is intended for **educational and authorized security testing** purposes only. Unauthorized use against systems you do not own or have explicit permission to test is strictly prohibited.

