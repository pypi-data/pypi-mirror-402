"""
HTTP Session Configuration Module

This module provides a centralized HTTP session with configurable SSL verification
for all HTTP requests throughout the AltaSigma package.
"""

import os
import requests

# Global session instance
http_session = None

def _http_session():
    """Gets or creates the configured HTTP session.

    Creates a requests session with SSL verification settings based on
    the DISABLE_SSL_VERIFICATION environment variable. When DISABLE_SSL_VERIFICATION=true,
    SSL certificate verification is disabled.

    Note: The requests library automatically uses REQUESTS_CA_BUNDLE environment
    variable for custom CA certificates when verification is enabled.

    Returns:
        requests.Session: A configured requests session.
    """
    global http_session
    if http_session is not None:
        return http_session
    else:
        http_session = requests.Session()

        # Get SSL configuration
        ssl_config = _get_ssl_config()

        if not ssl_config['verify']:
            # Disable SSL verification
            http_session.verify = False
            # Disable SSL warnings when verification is disabled
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # else: requests automatically uses REQUESTS_CA_BUNDLE if set

        return http_session


def _get_ssl_config():
    """Get SSL configuration settings for use across different HTTP clients.

    Returns a dictionary with SSL configuration that can be used by
    boto3, requests, and other HTTP clients.

    Consumers should check the 'verify' boolean first. If verification is not
    disabled and 'ca_bundle' is provided, use the ca_bundle path.

    Returns:
        dict: SSL configuration with keys:
            - 'verify': Boolean indicating whether to verify SSL certificates
            - 'ca_bundle': Path to CA certificate bundle if set via REQUESTS_CA_BUNDLE, or None
    """
    disable_ssl_verification = os.environ.get('DISABLE_SSL_VERIFICATION', 'false').lower() == 'true'
    ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE')

    return {
        'verify': not disable_ssl_verification,
        'ca_bundle': ca_bundle
    }