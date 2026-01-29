USFX - Ultimate Subdomain Finder X
===================================

A standalone Python CLI tool for discovering subdomains on internal
networks using custom DNS servers. Designed for air-gapped environments
without internet connectivity.


FEATURES
--------

  - Custom DNS Server Support: Specify internal DNS servers
  - Offline-Only Modules: All techniques work without internet
  - 10 Enumeration Modules:
      * DNS Brute Force
      * Zone Transfer (AXFR)
      * DNSSEC Walking (NSEC/NSEC3)
      * DNS Record Mining (MX, NS, TXT, SRV, SOA, CAA)
      * Reverse DNS Sweep
      * CNAME Chain Analysis
      * Subdomain Permutation
      * Recursive Sub-subdomain Enumeration
      * Virtual Host Discovery
      * TLS Certificate SAN Extraction
  - Multiple Output Formats: JSON, CSV, TXT
  - Bundled Wordlists: Small (~500), Medium (~3500), Large (~18000)
  - Progress Tracking: Real-time progress with Rich terminal UI


INSTALLATION
------------

From Source (Development):

    git clone https://github.com/devastator-x/usfx.git
    cd usfx
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    usfx --version

From PyPI (when available):

    pip install usfx

From Built Package:

    pip install dist/usfx-1.1.0-py3-none-any.whl


QUICK START
-----------

Basic Usage:

    usfx corp.local                              # System DNS
    usfx corp.local -d 192.168.1.1               # Internal DNS
    usfx corp.local -d 192.168.1.1 -d 10.0.0.1   # Multiple DNS

Wordlist Options:

    usfx corp.local -d 10.0.0.1 -s small         # ~500 words
    usfx corp.local -d 10.0.0.1 -s medium        # ~3500 words (default)
    usfx corp.local -d 10.0.0.1 -s large         # ~10000 words
    usfx corp.local -d 10.0.0.1 -w /path/to/custom.txt

Output Options:

    usfx corp.local -d 10.0.0.1 -o results.json
    usfx corp.local -d 10.0.0.1 -o results.csv -f csv
    usfx corp.local -d 10.0.0.1 -o results.txt -f txt

Module Selection:

    usfx corp.local -d 10.0.0.1 -m bruteforce,zone,records

    Available modules:
      bruteforce  - DNS brute force with wordlist
      zone        - Zone transfer (AXFR)
      dnssec      - DNSSEC zone walking
      records     - DNS record mining
      reverse     - Reverse DNS sweep
      cname       - CNAME chain analysis
      permutation - Subdomain permutation
      recursive   - Recursive sub-subdomain enumeration
      vhost       - Virtual host discovery
      tls         - TLS certificate analysis

Advanced Options:

    usfx corp.local -d 10.0.0.1 -t 50 --timeout 5.0
    usfx corp.local -d 10.0.0.1 --reverse-range 192.168.0.0/24
    usfx corp.local -d 10.0.0.1 --vhost-ip 192.168.1.100
    usfx corp.local -d 10.0.0.1 -v    # Verbose
    usfx corp.local -d 10.0.0.1 -q    # Quiet


CLI REFERENCE
-------------

Usage: usfx [OPTIONS] DOMAIN

Options:
  -d, --dns-server TEXT       DNS server IP (can be repeated)
  -w, --wordlist PATH         Custom wordlist file
  -s, --wordlist-size TEXT    Wordlist size: small|medium|large
  -o, --output PATH           Output file path
  -f, --format TEXT           Output format: json|csv|txt
  -t, --threads INTEGER       Parallel threads (default: 30, max: 100)
  --timeout FLOAT             DNS timeout in seconds (default: 3.0)
  -m, --modules TEXT          Comma-separated module list
  --reverse-range TEXT        CIDR range for reverse DNS
  --vhost-ip TEXT             IP for vhost scanning
  -v, --verbose               Verbose output
  -q, --quiet                 Suppress non-essential output
  --no-color                  Disable colored output
  --version                   Show version
  --help                      Show help message


PYTHON API
----------

    from usfx import ScanConfig, SubdomainEngine
    from usfx.config import WordlistSize

    config = ScanConfig(
        domain='corp.internal',
        dns_servers=['10.0.0.1', '10.0.0.2'],
        wordlist_size=WordlistSize.MEDIUM,
        threads=50,
        timeout=3.0
    )

    engine = SubdomainEngine()
    result = engine.scan(config)

    print(f"Found {result.total_found} subdomains")
    for sub in result.subdomains:
        print(f"  {sub.subdomain} -> {sub.ip}")


MODULE DESCRIPTIONS
-------------------

  dns_bruteforce   Wordlist-based DNS queries           Medium
  zone_transfer    AXFR zone transfer attempts          Fast
  dnssec_walker    NSEC/NSEC3 zone walking              Fast
  dns_records      MX/NS/TXT/SRV/SOA/CAA mining         Fast
  reverse_dns      PTR lookups on IP ranges             Slow
  cname_chaser     CNAME chain tracking                 Fast
  permutation      Subdomain variation generation       Medium
  recursive_enum   Sub-subdomain discovery              Medium
  vhost_scanner    Host header brute force              Slow
  tls_analyzer     TLS certificate SAN extraction       Medium


REQUIREMENTS
------------

  - Python 3.10+
  - dnspython >= 2.4.0
  - click >= 8.1.0
  - requests >= 2.28.0
  - cryptography >= 41.0.0
  - rich >= 13.0.0


USE CASES
---------

Internal Network Penetration Testing:
    usfx corp.internal -d 10.0.0.53 -s large -o findings.json

Active Directory Reconnaissance:
    usfx ad.corp.local -d 192.168.1.1 -m records,reverse,zone

IT Asset Discovery:
    usfx internal.company -d 172.16.0.1 --reverse-range 172.16.0.0/16


LICENSE
-------

MIT License - See LICENSE file for details.
