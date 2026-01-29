"""
Subdomain Takeover Detection Module

Detects potential subdomain takeover vulnerabilities by checking
CNAME records pointing to unclaimed cloud services.

Works offline - only requires DNS access to target network.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from .base import BaseModule

if TYPE_CHECKING:
    from ..utils.dns_resolver import InternalDNSResolver

logger = logging.getLogger(__name__)


# Fingerprints for subdomain takeover detection
# Format: (cname_pattern, service_name, is_vulnerable_check)
TAKEOVER_FINGERPRINTS = [
    # AWS
    (".s3.amazonaws.com", "AWS S3", ["NoSuchBucket"]),
    (".s3-website", "AWS S3 Website", ["NoSuchBucket"]),
    (".cloudfront.net", "AWS CloudFront", ["Bad request", "ERROR: The request could not be satisfied"]),
    (".elasticbeanstalk.com", "AWS Elastic Beanstalk", ["NXDOMAIN"]),

    # Azure
    (".azurewebsites.net", "Azure App Service", ["NXDOMAIN"]),
    (".cloudapp.azure.com", "Azure Cloud App", ["NXDOMAIN"]),
    (".azure-api.net", "Azure API Management", ["NXDOMAIN"]),
    (".azureedge.net", "Azure CDN", ["NXDOMAIN"]),
    (".blob.core.windows.net", "Azure Blob Storage", ["BlobNotFound", "NXDOMAIN"]),
    (".trafficmanager.net", "Azure Traffic Manager", ["NXDOMAIN"]),

    # Google Cloud
    (".storage.googleapis.com", "Google Cloud Storage", ["NoSuchBucket"]),
    (".appspot.com", "Google App Engine", ["NXDOMAIN"]),

    # GitHub
    (".github.io", "GitHub Pages", ["There isn't a GitHub Pages site here", "NXDOMAIN"]),
    (".githubusercontent.com", "GitHub User Content", ["NXDOMAIN"]),

    # Heroku
    (".herokuapp.com", "Heroku", ["No such app", "NXDOMAIN"]),
    (".herokudns.com", "Heroku DNS", ["NXDOMAIN"]),

    # Shopify
    (".myshopify.com", "Shopify", ["Sorry, this shop is currently unavailable", "NXDOMAIN"]),

    # Tumblr
    (".tumblr.com", "Tumblr", ["There's nothing here", "NXDOMAIN"]),

    # WordPress
    (".wordpress.com", "WordPress.com", ["Do you want to register", "NXDOMAIN"]),

    # Zendesk
    (".zendesk.com", "Zendesk", ["Help Center Closed", "NXDOMAIN"]),

    # Fastly
    (".fastly.net", "Fastly", ["Fastly error: unknown domain", "NXDOMAIN"]),

    # Pantheon
    (".pantheonsite.io", "Pantheon", ["The gods are wise", "NXDOMAIN"]),

    # Ghost
    (".ghost.io", "Ghost", ["NXDOMAIN"]),

    # Surge
    (".surge.sh", "Surge", ["project not found", "NXDOMAIN"]),

    # Bitbucket
    (".bitbucket.io", "Bitbucket", ["Repository not found", "NXDOMAIN"]),

    # Netlify
    (".netlify.app", "Netlify", ["Not Found", "NXDOMAIN"]),
    (".netlify.com", "Netlify", ["Not Found", "NXDOMAIN"]),

    # Vercel
    (".vercel.app", "Vercel", ["NXDOMAIN"]),
    (".now.sh", "Vercel (now.sh)", ["NXDOMAIN"]),

    # Firebase
    (".firebaseapp.com", "Firebase", ["NXDOMAIN"]),
    (".web.app", "Firebase Hosting", ["NXDOMAIN"]),

    # Fly.io
    (".fly.dev", "Fly.io", ["NXDOMAIN"]),

    # Render
    (".onrender.com", "Render", ["NXDOMAIN"]),

    # Railway
    (".up.railway.app", "Railway", ["NXDOMAIN"]),

    # Cargo Collective
    (".cargocollective.com", "Cargo", ["NXDOMAIN"]),

    # Feedpress
    (".redirect.feedpress.me", "Feedpress", ["NXDOMAIN"]),

    # Unbounce
    (".unbouncepages.com", "Unbounce", ["NXDOMAIN"]),

    # Help Scout
    (".helpscoutdocs.com", "Help Scout", ["NXDOMAIN"]),

    # Tilda
    (".tilda.ws", "Tilda", ["NXDOMAIN"]),

    # Webflow
    (".webflow.io", "Webflow", ["NXDOMAIN"]),

    # Kinsta
    (".kinsta.cloud", "Kinsta", ["NXDOMAIN"]),
]


class TakeoverDetector(BaseModule):
    """
    Subdomain Takeover Detection Module

    Checks discovered subdomains for potential takeover vulnerabilities
    by analyzing CNAME records pointing to cloud services.
    """

    MODULE_NAME = "takeover"

    def __init__(
        self,
        domain: str,
        resolver: Optional['InternalDNSResolver'] = None,
        threads: int = 10,
        **kwargs
    ):
        super().__init__(domain, resolver, **kwargs)
        self.threads = threads
        self.vulnerable: List[Dict] = []
        self.potential: List[Dict] = []

    def _check_cname(self, subdomain: str) -> Optional[str]:
        """Get CNAME record for subdomain"""
        try:
            return self.resolver.resolve_cname(subdomain)
        except:
            return None

    def _check_nxdomain(self, hostname: str) -> bool:
        """Check if hostname returns NXDOMAIN"""
        try:
            result = self.resolver.resolve_a(hostname)
            return result is None
        except:
            return True

    def _analyze_cname(self, subdomain: str, cname: str) -> Optional[Dict]:
        """
        Analyze CNAME for potential takeover

        Returns dict with vulnerability info or None
        """
        cname_lower = cname.lower()

        for pattern, service, indicators in TAKEOVER_FINGERPRINTS:
            if pattern in cname_lower:
                # Check if the CNAME target is NXDOMAIN (unclaimed)
                is_nxdomain = "NXDOMAIN" in indicators and self._check_nxdomain(cname)

                if is_nxdomain:
                    return {
                        "subdomain": subdomain,
                        "cname": cname,
                        "service": service,
                        "status": "vulnerable",
                        "reason": f"CNAME points to unclaimed {service} resource"
                    }
                else:
                    return {
                        "subdomain": subdomain,
                        "cname": cname,
                        "service": service,
                        "status": "potential",
                        "reason": f"CNAME points to {service} - verify manually"
                    }

        return None

    def enumerate(self, known_subs: Dict[str, Optional[str]] = None, **kwargs) -> Dict[str, Optional[str]]:
        """
        Check subdomains for takeover vulnerabilities

        Args:
            known_subs: Dict of known subdomains to check

        Returns:
            Dict of vulnerable subdomains (for compatibility)
        """
        if not known_subs:
            logger.info("No subdomains provided for takeover check")
            return {}

        logger.info(f"Checking {len(known_subs)} subdomains for takeover vulnerabilities")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def check_subdomain(subdomain: str) -> Optional[Dict]:
            if self.is_cancelled():
                return None

            cname = self._check_cname(subdomain)
            if cname:
                return self._analyze_cname(subdomain, cname)
            return None

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {
                executor.submit(check_subdomain, sub): sub
                for sub in known_subs.keys()
            }

            for future in as_completed(futures):
                if self.is_cancelled():
                    break

                result = future.result()
                if result:
                    if result["status"] == "vulnerable":
                        self.vulnerable.append(result)
                        self._add_discovered(result["subdomain"], None)
                    else:
                        self.potential.append(result)

        logger.info(f"Takeover check complete: {len(self.vulnerable)} vulnerable, {len(self.potential)} potential")

        return self.discovered

    def get_vulnerable(self) -> List[Dict]:
        """Get list of vulnerable subdomains"""
        return self.vulnerable

    def get_potential(self) -> List[Dict]:
        """Get list of potentially vulnerable subdomains"""
        return self.potential

    def get_all_findings(self) -> List[Dict]:
        """Get all findings (vulnerable + potential)"""
        return self.vulnerable + self.potential
