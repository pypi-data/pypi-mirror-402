"""
Reverse Proxy Setup for IPMI Monitor
Handles nginx configuration, SSL certificates, and landing page
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from jinja2 import Environment, PackageLoader, select_autoescape


def get_jinja_env():
    """Get Jinja2 environment for templates"""
    return Environment(
        loader=PackageLoader("ipmi_monitor", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def generate_self_signed_cert(
    domain: str = "localhost",
    cert_dir: str = "/etc/ipmi-monitor/ssl",
    days: int = 365,
) -> tuple[str, str]:
    """
    Generate self-signed SSL certificate.
    
    Returns:
        Tuple of (cert_path, key_path)
    """
    cert_dir = Path(cert_dir)
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    cert_path = cert_dir / "server.crt"
    key_path = cert_dir / "server.key"
    
    # Generate self-signed certificate
    cmd = [
        "openssl", "req", "-x509", "-nodes",
        "-days", str(days),
        "-newkey", "rsa:2048",
        "-keyout", str(key_path),
        "-out", str(cert_path),
        "-subj", f"/CN={domain}/O=IPMI Monitor/C=US",
        "-addext", f"subjectAltName=DNS:{domain},DNS:*.{domain},IP:127.0.0.1"
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Set permissions
    os.chmod(key_path, 0o600)
    os.chmod(cert_path, 0o644)
    
    print(f"✓ Generated self-signed certificate for {domain}")
    print(f"  Certificate: {cert_path}")
    print(f"  Key: {key_path}")
    
    return str(cert_path), str(key_path)


def setup_letsencrypt(
    domain: str,
    email: str,
    cert_dir: str = "/etc/letsencrypt/live",
) -> tuple[str, str]:
    """
    Setup Let's Encrypt certificate using certbot.
    
    Returns:
        Tuple of (cert_path, key_path)
    """
    # Check if certbot is installed
    if not shutil.which("certbot"):
        print("Installing certbot...")
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "certbot"], check=True)
    
    # Stop nginx temporarily if running
    subprocess.run(["systemctl", "stop", "nginx"], capture_output=True)
    
    # Get certificate
    cmd = [
        "certbot", "certonly", "--standalone",
        "-d", domain,
        "--email", email,
        "--agree-tos",
        "--non-interactive",
    ]
    
    subprocess.run(cmd, check=True)
    
    cert_path = f"{cert_dir}/{domain}/fullchain.pem"
    key_path = f"{cert_dir}/{domain}/privkey.pem"
    
    print(f"✓ Let's Encrypt certificate obtained for {domain}")
    
    return cert_path, key_path


def generate_nginx_config(
    domain: Optional[str] = None,
    ssl_cert: str = "/etc/ipmi-monitor/ssl/server.crt",
    ssl_key: str = "/etc/ipmi-monitor/ssl/server.key",
    grafana_enabled: bool = False,
    ipmi_subdomain: bool = False,
    grafana_subdomain: bool = False,
    output_path: str = "/etc/nginx/sites-available/ipmi-monitor",
) -> str:
    """
    Generate nginx configuration file.
    
    Returns:
        Path to generated config
    """
    env = get_jinja_env()
    template = env.get_template("nginx.conf.j2")
    
    config = template.render(
        domain=domain,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
        ipmi_enabled=True,  # IPMI Monitor always has itself
        grafana_enabled=grafana_enabled,
        grafana_subdomain=grafana_subdomain,
        ipmi_subdomain=ipmi_subdomain,
    )
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(config)
    
    print(f"✓ Generated nginx config: {output_path}")
    
    return str(output_path)


def generate_landing_page(
    site_name: str = "IPMI Monitor",
    grafana_enabled: bool = False,
    vastai_enabled: bool = False,
    output_dir: str = "/var/www/ipmi-monitor",
) -> str:
    """
    Generate landing page HTML.
    
    Args:
        site_name: Name shown on landing page
        grafana_enabled: Whether DC Overview (Grafana/Prometheus) is available
        vastai_enabled: Whether to show Vast.ai dashboard link
        output_dir: Directory to write index.html
    
    Returns:
        Path to generated index.html
    """
    env = get_jinja_env()
    template = env.get_template("landing.html.j2")
    
    html = template.render(
        site_name=site_name,
        grafana_enabled=grafana_enabled,
        ipmi_enabled=True,  # IPMI Monitor always has itself
        vastai_enabled=vastai_enabled,
    )
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "index.html"
    output_path.write_text(html)
    
    print(f"✓ Generated landing page: {output_path}")
    
    return str(output_path)


def install_nginx():
    """Install nginx if not present"""
    if shutil.which("nginx"):
        return True
    
    print("Installing nginx...")
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "nginx"], check=True)
    return True


def enable_nginx_site(config_path: str = "/etc/nginx/sites-available/ipmi-monitor"):
    """Enable the nginx site and reload"""
    sites_enabled = Path("/etc/nginx/sites-enabled")
    link_path = sites_enabled / "ipmi-monitor"
    
    # Remove default if exists
    default_link = sites_enabled / "default"
    if default_link.exists():
        default_link.unlink()
    
    # Create symlink
    if link_path.exists():
        link_path.unlink()
    link_path.symlink_to(config_path)
    
    # Test config
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ Nginx config test failed: {result.stderr}")
        return False
    
    # Reload nginx
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
    print("✓ Nginx reloaded")
    
    return True


def setup_reverse_proxy(
    domain: Optional[str] = None,
    email: Optional[str] = None,
    site_name: str = "IPMI Monitor",
    grafana_enabled: bool = False,
    vastai_enabled: bool = False,
    use_letsencrypt: bool = False,
):
    """
    Complete reverse proxy setup.
    
    Args:
        domain: Domain name (None for IP-only access with self-signed cert)
        email: Email for Let's Encrypt (required if use_letsencrypt=True)
        site_name: Name to display on landing page
        grafana_enabled: Whether DC Overview (Grafana/Prometheus) is installed
        vastai_enabled: Whether Vast.ai integration is enabled
        use_letsencrypt: Use Let's Encrypt instead of self-signed
    """
    print("\n━━━ Setting up Reverse Proxy ━━━\n")
    
    # Install nginx
    install_nginx()
    
    # Generate SSL certificate
    if use_letsencrypt and domain and email:
        ssl_cert, ssl_key = setup_letsencrypt(domain, email)
    else:
        ssl_cert, ssl_key = generate_self_signed_cert(domain or "localhost")
    
    # Generate nginx config
    generate_nginx_config(
        domain=domain,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
        grafana_enabled=grafana_enabled,
        grafana_subdomain=bool(domain) and grafana_enabled,
        ipmi_subdomain=bool(domain),
    )
    
    # Generate landing page
    generate_landing_page(
        site_name=site_name,
        grafana_enabled=grafana_enabled,
        vastai_enabled=vastai_enabled,
    )
    
    # Enable site
    enable_nginx_site()
    
    # Print access info
    print("\n━━━ Reverse Proxy Setup Complete ━━━\n")
    
    if domain:
        print(f"Access your dashboard at: https://{domain}/")
        print(f"  • IPMI Monitor: https://{domain}/ipmi/")
        if grafana_enabled:
            print(f"  • Grafana: https://{domain}/grafana/")
            print(f"  • Prometheus: https://{domain}/prometheus/")
        print(f"\nSubdomains (if DNS configured):")
        print(f"  • https://ipmi.{domain}/")
        if grafana_enabled:
            print(f"  • https://grafana.{domain}/")
    else:
        print("Access your dashboard at: https://<server-ip>/")
        print("  • IPMI Monitor: https://<server-ip>/ipmi/")
        if grafana_enabled:
            print("  • Grafana: https://<server-ip>/grafana/")
            print("  • Prometheus: https://<server-ip>/prometheus/")
    
    if not use_letsencrypt:
        print("\n⚠️  Using self-signed certificate - browser will show security warning")
        print("   This is normal for internal/private networks")


if __name__ == "__main__":
    # Test setup
    setup_reverse_proxy(
        domain=None,
        site_name="My Server Fleet",
        grafana_enabled=True,
        vastai_enabled=True,
    )
