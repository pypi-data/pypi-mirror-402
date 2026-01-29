"""VPN configuration downloader for NordVPN.

Downloads and filters NordVPN OpenVPN configuration files,
keeping only geographically suitable US servers.
"""

import os
import shutil
from glob import glob
from multiprocessing import Pool
from pathlib import Path
from zipfile import ZipFile

import geoip2.database
import requests

CONFIG_DIR = "config"
DB_URL = "https://git.io/GeoLite2-City.mmdb"
DB_PATH = f"{CONFIG_DIR}/{DB_URL.split('/')[-1]}"
VPN_DIR = "ovpn"
TCP_DIR = "ovpn_tcp"
VPN_EXT = "zip"
ZIP_FN = f"{VPN_DIR}.{VPN_EXT}"
ZIP_PATH = os.path.join(CONFIG_DIR, ZIP_FN)
UNZIP_PATH = os.path.join(CONFIG_DIR, VPN_DIR)


def download_db() -> None:
    """Download the GeoLite2 City database."""
    response = requests.get(DB_URL, timeout=60)
    response.raise_for_status()
    with open(DB_PATH, "wb") as f:
        f.write(response.content)


def download_file(url: str) -> str:
    """Download a file from a URL.

    Args:
        url: The URL to download.

    Returns:
        The local path where the file was saved.
    """
    filename = os.path.join(CONFIG_DIR, url.split("/")[-1])
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(filename, "wb") as f:
        f.write(response.content)
    return filename


def delete(path: str) -> None:
    """Delete a file or directory.

    Args:
        path: Path to delete.

    Raises:
        FileNotFoundError: If the path does not exist.
    """
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        raise FileNotFoundError(f"Path to delete does not exist: {path}")


def multidelete(paths: list[str]) -> list[None]:
    """Delete multiple paths in parallel.

    Args:
        paths: List of paths to delete.

    Returns:
        List of None values (one per deleted path).
    """
    with Pool() as p:
        return p.map(delete, paths)


def geolocate(filename: str) -> str | None:
    """Get the city name for a VPN server configuration.

    Args:
        filename: Path to the OpenVPN config file.

    Returns:
        The city name, or None if not found.
    """
    with open(filename) as file:
        lines = file.readlines()
        ip = None
        for line in lines:
            if line.startswith("remote "):
                ip = line.split(" ")[1]
                break
        if ip:
            with geoip2.database.Reader(DB_PATH) as reader:
                response = reader.city(ip)
                return response.city.names.get("en")
    return None


def move(cfg: str) -> str:
    """Move a config file to the config directory.

    Args:
        cfg: Path to the config file.

    Returns:
        The new path.
    """
    return shutil.move(cfg, CONFIG_DIR)


def get_servers() -> list[str]:
    """Download and extract NordVPN server configurations.

    Returns:
        List of paths to US server config files.
    """
    download_file(f"https://downloads.nordcdn.com/configs/archives/servers/{ZIP_FN}")
    with ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(UNZIP_PATH)
    # Only use American servers
    cfgs = glob(os.path.join(UNZIP_PATH, TCP_DIR, "us*.tcp.ovpn"))
    with Pool() as p:
        return p.map(move, cfgs)


def multigeolocate(servers: list[str]) -> list[str | None]:
    """Geolocate multiple servers in parallel.

    Args:
        servers: List of server config paths.

    Returns:
        List of city names.
    """
    with Pool() as p:
        return p.map(geolocate, servers)


if __name__ == "__main__":
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    download_db()
    servers = get_servers()
    locations = multigeolocate(servers)
    far_servers = [
        server
        for server, location in zip(servers, locations, strict=False)
        if location not in {"Miami", "Atlanta"}
    ]
    multidelete(far_servers + [DB_PATH, ZIP_PATH, UNZIP_PATH])
