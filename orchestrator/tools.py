from langchain_core.tools import tool

@tool
def write_file_tool(file_path: str, content: str) -> str:
    """Writes the specified content to a file at the given file_path.
    Use this tool to save code, reports, or results to the filesystem.
    """
    import os
    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote file to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def read_file_tool(file_path: str) -> str:
    """Reads the contents of a file at the given file_path.
    Use this tool to view code, reports, or results from the filesystem.
    """
    import os
    try:
        if not os.path.exists(file_path):
            return f"Error: File does not exist at {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def fetch_webpage_tool(url: str) -> str:
    """Fetches the content of a web page at the given URL and returns it as plain text.
    Use this tool to read detailed article content after finding links in search results.
    """
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        # Return first 3000 characters to avoid context overflow
        if len(text) > 3000:
            return text[:3000] + "\n... [Content truncated to 3000 characters] ..."
        return text
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"

@tool
def query_knowledge_base(query: str) -> str:
    """Queries the local knowledge base using semantic vector search.
    Use this tool to find information from local company documents, guides, policies, or project files.
    """
    import os
    from langchain_community.vectorstores import Chroma
    from langchain_ollama import OllamaEmbeddings
    
    CHROMA_DB_DIR = "./chroma_db"
    EMBEDDING_MODEL = "nomic-embed-text"
    
    if not os.path.exists(CHROMA_DB_DIR):
        return "Error: Local knowledge base vector database does not exist. Please index documents first."
        
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        db = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        results = db.similarity_search(query, k=3)
        
        if not results:
            return "No matching information found in the local knowledge base."
            
        combined_text = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page")
            source_info = f"{source} (Page {page})" if page else source
            combined_text.append(f"--- Document Chunk {i+1} (Source: {source_info}) ---\n{doc.page_content}")
            
        return "\n\n".join(combined_text)
    except Exception as e:
        return f"Error querying local knowledge base: {str(e)}"

@tool
def list_directory_tool(directory_path: str) -> str:
    """Recursively lists all files in a directory tree.
    Use this tool to discover files to audit for security vulnerabilities.
    Returns a tree listing of all files with their sizes.
    """
    import os
    try:
        if not os.path.exists(directory_path):
            return f"Error: Directory does not exist at {directory_path}"
        if not os.path.isdir(directory_path):
            return f"Error: {directory_path} is not a directory"

        file_list = []
        for root, dirs, files in os.walk(directory_path):
            # Skip hidden dirs and common non-source dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', '.env')]
            level = root.replace(directory_path, '').count(os.sep)
            indent = '  ' * level
            folder_name = os.path.basename(root)
            file_list.append(f"{indent}{folder_name}/")
            sub_indent = '  ' * (level + 1)
            for file in sorted(files):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                except OSError:
                    size_str = "unknown size"
                file_list.append(f"{sub_indent}{file} ({size_str})")

        result = "\n".join(file_list[:200])  # Cap at 200 entries
        if len(file_list) > 200:
            result += f"\n... and {len(file_list) - 200} more files"
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool
def scan_dependencies_tool(file_path: str) -> str:
    """Scans a dependency file (requirements.txt, package.json, pyproject.toml)
    for known vulnerable or risky package patterns.
    Returns a list of findings with severity ratings.
    """
    import os
    import re
    try:
        if not os.path.exists(file_path):
            return f"Error: File does not exist at {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        filename = os.path.basename(file_path).lower()
        findings = []

        # Known risky patterns
        risky_patterns = {
            "pyyaml": ("MEDIUM", "PyYAML < 5.1 has yaml.load() arbitrary code execution (CVE-2017-18342). Ensure safe_load() is used."),
            "requests": ("LOW", "Older requests versions have SSL verification issues. Ensure >= 2.20.0."),
            "flask": ("MEDIUM", "Flask debug mode in production exposes Werkzeug debugger (RCE). Check debug=False in prod."),
            "django": ("MEDIUM", "Older Django versions have multiple CVEs. Ensure latest LTS version."),
            "jinja2": ("MEDIUM", "Jinja2 < 2.11.3 has sandbox escape vulnerabilities. Ensure autoescape=True."),
            "paramiko": ("HIGH", "Paramiko < 2.10.1 has authentication bypass (CVE-2023-48795). Update immediately."),
            "pillow": ("MEDIUM", "Pillow has frequent CVEs for image parsing. Keep updated."),
            "urllib3": ("MEDIUM", "urllib3 < 2.0.6 has request smuggling issues (CVE-2023-45803)."),
            "cryptography": ("HIGH", "Older cryptography versions have multiple CVEs. Ensure >= 41.0.0."),
            "sqlalchemy": ("MEDIUM", "Check for raw SQL usage patterns that bypass ORM protections."),
            "pickle": ("CRITICAL", "pickle/cPickle deserialization is inherently unsafe. Never unpickle untrusted data."),
            "subprocess": ("HIGH", "subprocess with shell=True is vulnerable to command injection."),
            "eval": ("CRITICAL", "eval()/exec() on user input allows arbitrary code execution."),
            "lodash": ("HIGH", "lodash < 4.17.21 has prototype pollution (CVE-2021-23337)."),
            "express": ("MEDIUM", "Ensure express >= 4.17.3 for security patches."),
            "jsonwebtoken": ("HIGH", "jsonwebtoken < 9.0.0 has algorithm confusion attack (CVE-2022-23529)."),
        }

        if filename in ("requirements.txt", "pyproject.toml", "setup.py", "pipfile"):
            for pkg, (severity, desc) in risky_patterns.items():
                if pkg.lower() in content.lower():
                    # Try to extract version
                    version_match = re.search(rf'{pkg}[=<>~!]*\s*([\d.]+)', content, re.IGNORECASE)
                    version_info = f" (pinned: {version_match.group(1)})" if version_match else " (version not pinned - RISK)"
                    findings.append(f"[{severity}] {pkg}{version_info}: {desc}")

            # Check for unpinned dependencies
            if filename == "requirements.txt":
                lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith('#')]
                unpinned = [l for l in lines if '==' not in l and '>=' not in l]
                if unpinned:
                    findings.append(f"[MEDIUM] {len(unpinned)} unpinned dependencies found: {', '.join(unpinned[:5])}{'...' if len(unpinned) > 5 else ''}. Pin versions for reproducibility and security.")

        elif filename == "package.json":
            import json
            try:
                pkg_data = json.loads(content)
                all_deps = {}
                all_deps.update(pkg_data.get("dependencies", {}))
                all_deps.update(pkg_data.get("devDependencies", {}))
                for pkg, (severity, desc) in risky_patterns.items():
                    if pkg.lower() in [k.lower() for k in all_deps.keys()]:
                        version = all_deps.get(pkg, "unknown")
                        findings.append(f"[{severity}] {pkg} ({version}): {desc}")
            except json.JSONDecodeError:
                findings.append("[INFO] Could not parse package.json as valid JSON.")

        if not findings:
            return f"No known vulnerability patterns detected in {file_path}. Note: This is a pattern-based scan, not a full CVE database check. Consider running `pip-audit` or `npm audit` for comprehensive scanning."

        header = f"Dependency Security Scan: {file_path}\n{'=' * 50}\n"
        return header + "\n".join(findings)
    except Exception as e:
        return f"Error scanning dependencies: {str(e)}"


@tool
def fetch_github_repo_tool(repo_url: str) -> str:
    """Fetches key files from a GitHub repository for security analysis.
    Accepts URLs like https://github.com/user/repo.
    Returns the repo structure and contents of key security-relevant files.
    """
    import re
    import json
    try:
        import requests
    except ImportError:
        return "Error: requests library not available."

    try:
        # Extract owner/repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/\s?#]+)', repo_url)
        if not match:
            return f"Error: Could not parse GitHub repo URL: {repo_url}"

        owner, repo = match.group(1), match.group(2).rstrip('.git')
        api_base = f"https://api.github.com/repos/{owner}/{repo}"

        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AUnitedAI-SecurityAudit"}

        # Get repo info
        repo_resp = requests.get(api_base, headers=headers, timeout=10)
        if repo_resp.status_code == 404:
            return f"Error: Repository {owner}/{repo} not found or is private."
        repo_resp.raise_for_status()
        repo_info = repo_resp.json()

        result = [f"Repository: {repo_info.get('full_name', 'Unknown')}"]
        result.append(f"Description: {repo_info.get('description', 'N/A')}")
        result.append(f"Language: {repo_info.get('language', 'N/A')}")
        result.append(f"Stars: {repo_info.get('stargazers_count', 0)}")
        result.append("")

        # Get file tree
        tree_resp = requests.get(f"{api_base}/git/trees/HEAD?recursive=1", headers=headers, timeout=10)
        if tree_resp.status_code == 200:
            tree = tree_resp.json().get("tree", [])
            files = [f["path"] for f in tree if f["type"] == "blob"]
            result.append(f"Files ({len(files)} total):")
            for f in files[:100]:
                result.append(f"  {f}")
            if len(files) > 100:
                result.append(f"  ... and {len(files) - 100} more files")
            result.append("")

        # Fetch security-relevant files
        security_files = [
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".env", ".env.example", "requirements.txt", "package.json",
            "pyproject.toml", "setup.py", "Pipfile", ".github/workflows",
            "nginx.conf", "config.yml", "config.yaml", ".dockerignore",
            ".gitignore", "Makefile",
        ]

        for sec_file in security_files:
            matching = [f for f in files if f.endswith(sec_file) or f == sec_file] if 'files' in dir() else []
            for match_file in matching[:3]:
                file_resp = requests.get(
                    f"{api_base}/contents/{match_file}",
                    headers={**headers, "Accept": "application/vnd.github.v3.raw"},
                    timeout=10
                )
                if file_resp.status_code == 200:
                    content = file_resp.text[:2000]
                    result.append(f"--- {match_file} ---")
                    result.append(content)
                    if len(file_resp.text) > 2000:
                        result.append("... [truncated]")
                    result.append("")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching GitHub repo: {str(e)}"


# ── Validation Utilities (from YUNA Firewall) ─────────────────────────────────

def is_valid_ip(ip: str) -> bool:
    """Validate an IPv4 address."""
    import re
    pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, ip))


def is_valid_domain(domain: str) -> bool:
    """Validate a domain name."""
    import re
    pattern = r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$"
    return bool(re.match(pattern, domain))


# ── YUNA-Derived Security Tools ────────────────────────────────────────────────

@tool
def geoip_lookup_tool(ip_address: str) -> str:
    """Looks up the geographic location of an IP address.
    Returns country, city, ISP, and risk assessment.
    Use this to determine where network traffic originates from.
    """
    if not is_valid_ip(ip_address):
        return f"Error: Invalid IP address format: {ip_address}"

    try:
        import requests
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "fail":
            return f"GeoIP lookup failed: {data.get('message', 'Unknown error')}"

        country = data.get("country", "Unknown")
        city = data.get("city", "Unknown")
        region = data.get("regionName", "Unknown")
        isp = data.get("isp", "Unknown")
        org = data.get("org", "Unknown")
        as_number = data.get("as", "Unknown")
        lat = data.get("lat", "N/A")
        lon = data.get("lon", "N/A")

        # Risk assessment based on country
        high_risk_countries = ["North Korea", "Iran"]
        medium_risk_countries = ["China", "Russia"]
        risk_level = "HIGH" if country in high_risk_countries else \
                     "MEDIUM" if country in medium_risk_countries else "LOW"

        result = f"""GeoIP Report for {ip_address}
{'=' * 40}
Country:  {country}
Region:   {region}
City:     {city}
ISP:      {isp}
Org:      {org}
AS:       {as_number}
Location: {lat}, {lon}
Risk Level: {risk_level}"""

        if risk_level in ("HIGH", "MEDIUM"):
            result += f"\n⚠️ WARNING: IP originates from {risk_level}-risk country ({country})"

        return result
    except Exception as e:
        return f"GeoIP lookup error: {str(e)}"


@tool
def threat_intel_lookup_tool(ip_address: str) -> str:
    """Checks if an IP address is a known threat using pattern-based analysis.
    Returns threat status, risk indicators, and recommendations.
    Use this to assess whether an IP has suspicious characteristics.
    """
    if not is_valid_ip(ip_address):
        return f"Error: Invalid IP address format: {ip_address}"

    findings = []
    risk_score = 0

    # Check against known malicious IP ranges (pattern-based)
    suspicious_ranges = {
        "198.51.100.": ("HIGH", "Known test/documentation range — often spoofed in attacks"),
        "203.0.113.": ("MEDIUM", "Documentation range — should not appear in production traffic"),
        "192.0.2.": ("MEDIUM", "TEST-NET-1 range — should not appear in production"),
        "100.64.": ("LOW", "Carrier-grade NAT range — may indicate shared infrastructure"),
        "0.": ("CRITICAL", "Invalid source IP — likely spoofed"),
    }

    for prefix, (severity, description) in suspicious_ranges.items():
        if ip_address.startswith(prefix):
            findings.append(f"[{severity}] {description}")
            risk_score += {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25}[severity]

    # Check for private/reserved ranges appearing where they shouldn't
    private_ranges = ["10.", "172.16.", "172.17.", "172.18.", "172.19.",
                      "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                      "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                      "172.30.", "172.31.", "192.168."]
    for prefix in private_ranges:
        if ip_address.startswith(prefix):
            findings.append("[INFO] Private/RFC1918 IP address — internal network")
            break

    # Check if loopback
    if ip_address.startswith("127."):
        findings.append("[INFO] Loopback address — local traffic only")

    # Port scan indicator heuristic (based on IP pattern)
    octets = ip_address.split(".")
    if len(octets) == 4:
        try:
            last_octet = int(octets[3])
            if last_octet == 0 or last_octet == 255:
                findings.append("[MEDIUM] Network/broadcast address — may indicate scanning activity")
                risk_score += 30
        except ValueError:
            pass

    # GeoIP-based risk (try to look up)
    try:
        import requests
        geo_resp = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=3)
        if geo_resp.status_code == 200:
            geo_data = geo_resp.json()
            country = geo_data.get("country", "Unknown")
            if country in ["North Korea", "Iran"]:
                findings.append(f"[HIGH] IP from high-risk country: {country}")
                risk_score += 60
            elif country in ["China", "Russia"]:
                findings.append(f"[MEDIUM] IP from elevated-risk country: {country}")
                risk_score += 30
    except Exception:
        findings.append("[INFO] Could not perform GeoIP lookup for risk assessment")

    # Build result
    risk_level = "CRITICAL" if risk_score >= 100 else \
                 "HIGH" if risk_score >= 75 else \
                 "MEDIUM" if risk_score >= 40 else \
                 "LOW" if risk_score > 0 else "CLEAN"

    result = f"""Threat Intelligence Report for {ip_address}
{'=' * 50}
Overall Risk Score: {risk_score}/100
Risk Level: {risk_level}
Findings: {len(findings)}
"""

    if findings:
        result += "\nDetailed Findings:\n"
        for f in findings:
            result += f"  • {f}\n"
    else:
        result += "\n✅ No known threat indicators found for this IP.\n"

    result += f"\nRecommendation: "
    if risk_level in ("CRITICAL", "HIGH"):
        result += "BLOCK this IP immediately and investigate related traffic."
    elif risk_level == "MEDIUM":
        result += "Monitor this IP closely and review associated connections."
    else:
        result += "No immediate action required. Continue standard monitoring."

    return result


@tool
def neural_threat_score_tool(packet_rate: float, packet_size_kb: float,
                             connection_duration_hours: float, port_number: int) -> str:
    """Scores network traffic patterns using a neural network threat model.
    Returns a threat score between 0.0 (safe) and 1.0 (definite threat).

    Args:
        packet_rate: Packets per second (e.g., 50.0)
        packet_size_kb: Average packet size in KB (e.g., 1.5)
        connection_duration_hours: How long the connection has been active in hours (e.g., 0.5)
        port_number: Destination port number (e.g., 443)
    """
    import os
    try:
        from .neural_network import NeuralNetwork
    except ImportError:
        try:
            from orchestrator.neural_network import NeuralNetwork
        except ImportError:
            return "Error: Neural network module not available."

    nn = NeuralNetwork()

    # Try to load a pre-trained model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "neural_model.json")
    if os.path.exists(model_path):
        nn.load_model(model_path)

    # Normalize inputs (same as YUNA's extract_features)
    normalized_input = [
        min(packet_rate / 100.0, 1.0),        # Normalize packet rate
        min(packet_size_kb / 1024.0, 1.0),     # Normalize packet size
        min(connection_duration_hours, 1.0),    # Normalize duration
        port_number / 65535.0                   # Normalize port
    ]

    try:
        nn.forward_propagate(normalized_input)
        score = nn.get_threat_score()
        is_threat = nn.is_threat()
    except Exception as e:
        return f"Neural network scoring error: {str(e)}"

    # Interpret the score
    if score >= 0.9:
        level = "CRITICAL"
        interpretation = "Extremely suspicious traffic pattern — likely an active attack"
    elif score >= 0.7:
        level = "HIGH"
        interpretation = "High probability of malicious activity"
    elif score >= 0.5:
        level = "MEDIUM"
        interpretation = "Moderate suspicion — warrants investigation"
    elif score >= 0.3:
        level = "LOW"
        interpretation = "Slightly elevated activity — probably benign"
    else:
        level = "SAFE"
        interpretation = "Normal traffic pattern — no threat detected"

    # Add context about the specific patterns
    warnings = []
    high_risk_ports = {21, 22, 23, 25, 53, 3389, 4444, 5555, 8080}
    if port_number in high_risk_ports:
        warnings.append(f"Port {port_number} is commonly targeted in attacks")
    if packet_rate > 100:
        warnings.append(f"Packet rate ({packet_rate}/s) exceeds normal threshold")
    if packet_size_kb > 512:
        warnings.append(f"Large packet size ({packet_size_kb} KB) may indicate data exfiltration")
    if connection_duration_hours > 24:
        warnings.append(f"Very long connection ({connection_duration_hours}h) may indicate C2 beacon")

    result = f"""Neural Threat Score Report
{'=' * 40}
Threat Score: {score:.4f} / 1.0
Threat Level: {level}
Is Threat:    {'YES ⚠️' if is_threat else 'NO ✅'}

Input Parameters:
  Packet Rate:     {packet_rate} packets/sec
  Packet Size:     {packet_size_kb} KB
  Duration:        {connection_duration_hours} hours
  Dest Port:       {port_number}

Interpretation: {interpretation}
"""

    if warnings:
        result += "\nAdditional Warnings:\n"
        for w in warnings:
            result += f"  ⚠️ {w}\n"

    return result


@tool
def domain_category_tool(domain: str) -> str:
    """Categorizes a domain and provides a security risk assessment.
    Returns the domain's category, DNS information, and risk indicators.
    Use this to classify domains found during security analysis.
    """
    if not is_valid_domain(domain):
        return f"Error: Invalid domain format: {domain}"

    import socket
    findings = []
    risk_score = 0

    # Resolve domain IPs
    resolved_ips = []
    try:
        for info in socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM):
            ip = info[4][0]
            if ip not in resolved_ips:
                resolved_ips.append(ip)
    except socket.gaierror:
        findings.append("[INFO] Domain could not be resolved — may be inactive or blocked")
    except Exception as e:
        findings.append(f"[INFO] DNS resolution error: {str(e)}")

    # Check against known suspicious TLDs
    suspicious_tlds = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".buzz",
                       ".click", ".link", ".work", ".date", ".racing", ".download"]
    for tld in suspicious_tlds:
        if domain.endswith(tld):
            findings.append(f"[MEDIUM] Suspicious TLD ({tld}) — commonly used in phishing/malware")
            risk_score += 40
            break

    # Check for common phishing patterns
    phishing_keywords = ["login", "secure", "account", "verify", "update",
                         "confirm", "banking", "paypal", "amazon", "apple",
                         "microsoft", "google", "signin", "password"]
    domain_lower = domain.lower()
    for keyword in phishing_keywords:
        if keyword in domain_lower and not domain_lower.endswith(f".{keyword}.com"):
            findings.append(f"[MEDIUM] Domain contains phishing keyword: '{keyword}'")
            risk_score += 30
            break

    # Check for excessive subdomains (common in phishing)
    subdomain_count = domain.count('.') - 1
    if subdomain_count > 3:
        findings.append(f"[MEDIUM] Excessive subdomains ({subdomain_count}) — common in phishing URLs")
        risk_score += 25

    # Check domain length (very long domains are suspicious)
    if len(domain) > 50:
        findings.append(f"[LOW] Unusually long domain ({len(domain)} chars) — may be auto-generated")
        risk_score += 15

    # Known safe categories (hardcoded sample)
    known_categories = {
        "sports": ["espn.com", "nfl.com", "nba.com"],
        "news": ["cnn.com", "bbc.com", "nytimes.com", "reuters.com"],
        "technology": ["techcrunch.com", "wired.com", "github.com", "stackoverflow.com"],
        "education": ["coursera.org", "edx.org", "khanacademy.org", "mit.edu"],
        "search": ["google.com", "bing.com", "duckduckgo.com"],
        "social_media": ["facebook.com", "twitter.com", "linkedin.com", "instagram.com"],
        "email": ["gmail.com", "outlook.com", "yahoo.com"],
        "cloud": ["aws.amazon.com", "azure.microsoft.com", "cloud.google.com"],
    }

    detected_category = "unknown"
    for category, domains in known_categories.items():
        if domain in domains or any(domain.endswith(f".{d}") for d in domains):
            detected_category = category
            break

    # Build result
    risk_level = "HIGH" if risk_score >= 60 else \
                 "MEDIUM" if risk_score >= 30 else \
                 "LOW" if risk_score > 0 else "SAFE"

    result = f"""Domain Analysis Report: {domain}
{'=' * 50}
Category:    {detected_category}
Risk Level:  {risk_level}
Risk Score:  {risk_score}/100
Resolved IPs: {', '.join(resolved_ips) if resolved_ips else 'None'}
"""

    if findings:
        result += "\nSecurity Findings:\n"
        for f in findings:
            result += f"  • {f}\n"
    else:
        result += "\n✅ No suspicious indicators found for this domain.\n"

    return result

