# 🔍 API Endpoint Discovery Scraper

A comprehensive tool for discovering API endpoints from web applications through automated analysis of HTML, JavaScript, network requests, and documentation.

## ✨ Features

- **Multi-Method Discovery**: Analyzes HTML forms, JavaScript code, network requests, and API documentation
- **Static & Dynamic Scraping**: Supports both simple HTTP requests and full browser automation with Playwright
- **Multiple Output Formats**: Generate reports in JSON, CSV, HTML, and Markdown formats
- **Intelligent Classification**: Automatically categorizes endpoints as REST, GraphQL, WebSocket, or other types
- **Confidence Scoring**: Each discovered endpoint includes a confidence score based on detection method
- **Rate Limiting & Ethics**: Built-in respect for robots.txt and configurable rate limiting
- **Batch Processing**: Scan multiple URLs with parallel processing capabilities
- **Rich CLI Interface**: Beautiful command-line interface with progress bars and colored output

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/example/api-endpoint-scraper.git
cd api-endpoint-scraper
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers (for dynamic scraping):**
```bash
playwright install
```

### Basic Usage

**Scan a single URL:**
```bash
python cli.py scan https://example.com/app
```

**Use dynamic scraping for JavaScript-heavy sites:**
```bash
python cli.py scan https://spa-app.com --dynamic
```

**Generate reports in all formats:**
```bash
python cli.py scan https://api.example.com --all-formats
```

**Scan with authentication (login required):**
```bash
python cli.py scan https://app.example.com --dynamic --username "user@example.com" --password "mypassword"
```

**Batch scan multiple URLs:**
```bash
echo "https://api1.example.com
https://api2.example.com
https://api3.example.com" > urls.txt

python cli.py batch urls.txt --output-dir ./reports
```

## 📖 Detailed Usage

### Command Line Interface

The scraper provides several commands:

#### `scan` - Scan a single URL
```bash
python cli.py scan [OPTIONS] URL

Options:
  -o, --output PATH           Output file path
  -f, --format [json|csv|html|markdown]  Output format
  -d, --dynamic              Use dynamic scraping (Playwright)
  -t, --timeout INTEGER      Request timeout in seconds
  -r, --rate-limit FLOAT     Rate limit (seconds between requests)
  -u, --user-agent TEXT      Custom User-Agent string
  --min-confidence FLOAT     Minimum confidence threshold (0.0-1.0)
  --all-formats              Generate reports in all formats
  -U, --username TEXT        Username for authentication
  -P, --password TEXT        Password for authentication
  --login-url TEXT           Custom login URL (auto-detected if not provided)
```

#### `batch` - Scan multiple URLs
```bash
python cli.py batch [OPTIONS] URLS_FILE

Options:
  -o, --output-dir PATH      Output directory for reports
  -f, --format [json|csv|html|markdown]  Output format
  -d, --dynamic              Use dynamic scraping
  -p, --parallel INTEGER     Number of parallel scans (default: 5)
  --delay FLOAT              Delay between scans in seconds
```

#### `config` - Manage configuration
```bash
python cli.py config [OPTIONS]

Options:
  -k, --key TEXT             Configuration key to get/set
  -v, --value TEXT           Value to set
  -l, --list-all             List all configuration values
  --reset                    Reset to default configuration
```

#### `test` - Test scraper functionality
```bash
python cli.py test [OPTIONS] URL

Options:
  -o, --output PATH          Output file for test report
```

### Configuration

The scraper uses a YAML configuration file (`config/default.yaml`) that can be customized:

```yaml
scraping:
  timeout: 30
  rate_limit: 1.0
  user_agent: "API-Endpoint-Scraper/1.0"
  respect_robots_txt: true
  max_concurrent: 10

extraction:
  patterns:
    rest_api: ["api/v\\d+/", "/api/", "rest/"]
    graphql: ["graphql", "graph", "gql"]
    websocket: ["ws://", "wss://", "socket.io"]
  javascript_analysis: true
  network_monitoring: true

output:
  format: "json"
  include_metadata: true
  min_confidence: 0.5
  deduplicate: true
```

### Authentication

The scraper supports form-based authentication to access protected API endpoints:

**Basic Authentication:**
```bash
python cli.py scan https://app.example.com --dynamic --username "user@example.com" --password "mypassword"
```

**With Custom Login URL:**
```bash
python cli.py scan https://app.example.com --dynamic -U "user" -P "pass" --login-url "https://app.example.com/signin"
```

**Authentication Features:**
- Automatic login URL detection (tries common paths like `/login`, `/signin`, `/auth`)
- Support for various form field names (username, email, password, passwd)
- Success/failure detection based on page content and URL changes
- Cookie preservation for authenticated requests
- Works with complex forms and CSRF tokens

**Requirements for Authentication:**
- Must use `--dynamic` flag (requires Playwright)
- Valid credentials for the target site
- Site must use standard HTML form authentication

### Environment Variables

- `SCRAPER_CONFIG_PATH`: Path to custom configuration file
- `SCRAPER_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SCRAPER_OUTPUT_DIR`: Default output directory

## 🔧 How It Works

### Detection Methods

1. **JavaScript Analysis**: Parses JavaScript code to find:
   - `fetch()` calls
   - XMLHttpRequest usage
   - jQuery AJAX calls
   - Axios requests
   - GraphQL queries

2. **HTML Analysis**: Examines HTML content for:
   - Form actions
   - Link destinations
   - API-related URLs

3. **Network Monitoring**: Captures network requests during page load:
   - XHR/Fetch requests
   - API calls
   - Resource requests

4. **Documentation Parsing**: Extracts endpoints from:
   - OpenAPI/Swagger specifications
   - API documentation pages

### Endpoint Classification

Endpoints are automatically classified as:
- **REST**: Traditional REST API endpoints
- **GraphQL**: GraphQL endpoints and schemas
- **WebSocket**: Real-time communication endpoints
- **Other**: Unclassified or custom endpoints

### Confidence Scoring

Each endpoint receives a confidence score based on:
- **Network Request** (0.9): Observed in actual network traffic
- **Documentation** (0.9): Found in official API documentation
- **JavaScript Call** (0.8): Discovered in JavaScript code
- **HTML Form** (0.7): Found in HTML form actions
- **Pattern Match** (0.6): Matches common API patterns

## 📊 Output Formats

### JSON Report
```json
{
  "summary": {
    "target_url": "https://example.com",
    "total_endpoints": 15,
    "scan_duration_seconds": 12.34
  },
  "statistics": {
    "by_type": {"rest": 10, "graphql": 3, "websocket": 2},
    "by_method": {"GET": 8, "POST": 5, "PUT": 2},
    "average_confidence": 0.78
  },
  "endpoints": [
    {
      "url": "https://api.example.com/v1/users",
      "method": "GET",
      "type": "rest",
      "confidence": 0.9,
      "source": "network"
    }
  ]
}
```

### HTML Report
Beautiful, interactive HTML reports with:
- Summary statistics
- Endpoint tables with filtering
- Confidence indicators
- Method badges
- Responsive design

### CSV Export
Tabular format suitable for:
- Spreadsheet analysis
- Database import
- Further processing

### Markdown Report
Human-readable format perfect for:
- Documentation
- GitHub issues
- Team sharing

## 🛡️ Ethical Usage

This tool is designed for legitimate security testing and API documentation purposes. Please ensure you:

- **Have permission** to scan the target websites
- **Respect robots.txt** (enabled by default)
- **Use appropriate rate limiting** to avoid overwhelming servers
- **Comply with terms of service** of target websites
- **Follow responsible disclosure** for any security findings

## 🔒 Security Considerations

- JavaScript execution is sandboxed when possible
- No credentials are stored or transmitted
- Rate limiting prevents aggressive scanning
- SSL certificate verification is enabled by default
- User-Agent identification for transparency

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test the scraper on a specific URL:
```bash
python cli.py test https://httpbin.org/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output
- [Click](https://click.palletsprojects.com/) for command-line interface

## 📞 Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/example/api-endpoint-scraper/issues)
- 📖 Documentation: [Wiki](https://github.com/example/api-endpoint-scraper/wiki)

---

**⚠️ Disclaimer**: This tool is for educational and authorized testing purposes only. Users are responsible for ensuring they have proper authorization before scanning any websites. 