# 🔥 WEB KILLER v2.1

**WEB KILLER** is an advanced web flooding tool designed for penetration testing and network stress testing. It supports multiple attack types including HTTP flooding, Slowloris attacks, and SYN flooding with configurable threading and proxy support.

> ⚠️ **Disclaimer**: This tool is intended for authorized security testing only. Unauthorized use against systems you do not own or have explicit permission to test is illegal. Use responsibly.

## Features

- **Multiple Attack Types**
  - 🌐 HTTP Flooding (GET/POST/PUT/PATCH)
  - 🐢 Slowloris attacks (resource exhaustion)
  - 📡 SYN flooding (connection-based)
  - 🎲 Mixed mode (randomized attack combinations)

- **Advanced Configuration**
  - Configurable thread count for concurrent requests
  - Custom delay control between requests
  - POST data support with custom headers
  - Cookie handling
  - Custom HTTP headers
  - User-Agent randomization

- **Proxy Support**
  - Load proxies from external file
  - Automatic proxy rotation
  - Both HTTP and HTTPS proxy support

- **Detailed Statistics**
  - Real-time request monitoring
  - Success/failure rate tracking
  - HTTP status code distribution
  - Requests per second (RPS) calculation
  - Connection statistics

- **User Experience**
  - Colorized console output
  - Verbose logging mode
  - Interactive help system
  - Duration-based attack limiting
  - Graceful shutdown with Ctrl+C

## Requirements

- Python 3.x
- `requests` library
- `urllib3` library

