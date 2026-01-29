#!/usr/bin/env python3

from pathlib import Path
import re
import json
import shutil
import subprocess
import time
import logging
import argparse
import requests
from tqdm import tqdm
from datetime import datetime
from typing import List, Dict, Optional
import shadowScanner.helpers as HELPERS
import shadowScanner.globals as GLOBALS
from shadowScanner.validation import validate_args

logger = logging.getLogger()

# if This is not done every single request will output something when verbosity is high
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# To silence some specific messages
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)


class TargetGenerator:
    """
    Responsible ONLY for fetching programs, resolving wildcards,
    and generating the master list of targets.
    """

    def __init__(self, hackerone_key: Optional[str], use_subdomains: bool):
        self.hackerone_key = hackerone_key
        self.use_subdomains = use_subdomains
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch_hackerone_programs(self) -> List[Dict]:
        if not self.hackerone_key:
            return []

        spinner = HELPERS.Spinner("Fetching HackerOne programs metadata...")
        with spinner:
            programs = []
            metadata = []
            page = 1

            username, token = HELPERS.split_hackerone_key(self.hackerone_key)

            while True:
                try:
                    url = f"https://api.hackerone.com/v1/hackers/programs"
                    params = {"page[number]": page, "page[size]": 100}

                    response = self.session.get(
                        url,
                        auth=(username, token),
                        headers={"Accept": "application/json"},
                        params=params,
                        timeout=30,
                    )

                    if response.status_code != 200:
                        logger.error(f"\rHackerOne API error: {response.status_code}")
                        logger.error(f"\rResponse: {response.text[:500]}")
                        break

                    data = response.json()
                    batch = data.get("data", [])
                    metadata.extend(batch)

                    page += 1
                    time.sleep(0.1)

                    if len(batch) < 100:
                        break

                except Exception as e:
                    logger.error(f"\rError fetching HackerOne programs metadata: {e}")
                    time.sleep(5)
                    break

            num_programs = len(metadata)
            for i, program in enumerate(metadata):
                try:
                    handle = program["attributes"]["handle"]
                    spinner.updateMessage(f"Fetching programs data {i}/{num_programs}")
                    scope_response = self.session.get(
                        f"https://api.hackerone.com/v1/hackers/programs/{handle}",
                        auth=(username, token),
                        headers={"Accept": "application/json"},
                        timeout=30,
                    )

                    if scope_response.status_code == 200:
                        scope_data = scope_response.json()
                        programs.append(
                            {
                                "platform": "hackerone",
                                "name": program["attributes"]["name"],
                                "handle": handle,
                                "url": f"https://hackerone.com/{handle}",
                                "data": scope_data,
                            }
                        )
                except Exception as e:
                    logger.warning(f"\rError fetching program details: {e}")

        return programs

    def fetch_bugcrowd_programs(self) -> List[Dict]:
        """
        Fetches Bugcrowd programs from the community-maintained list
        instead of the official API.
        """
        logger.info("Fetching BugCrowd programs from community data...")
        programs = []

        try:
            url = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()

                for program in data:
                    programs.append(
                        {
                            "platform": "bugcrowd",
                            "name": program.get("name"),
                            "code": program.get("url").split("/")[-1],  #
                            "url": program.get("url"),
                            "data": {
                                "targets": program.get("targets", {}).get(
                                    "in_scope", []
                                )
                            },
                        }
                    )

            logger.info(f"Found {len(programs)} BugCrowd programs")

        except Exception as e:
            logger.error(f"Error fetching community data: {e}")

        return programs

    def fetch_intigriti_programs(self) -> List[Dict]:
        """
        Fetches Intigriti programs from the community-maintained list.
        """
        logger.info("Fetching Intigriti programs from community data...")
        programs = []

        try:
            url = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/intigriti_data.json"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()

                for program in data:
                    programs.append(
                        {
                            "platform": "intigriti",
                            "name": program.get("name"),
                            "handle": program.get("handle"),
                            "url": program.get("url"),
                            "data": {
                                "targets": program.get("targets", {}).get(
                                    "in_scope", []
                                )
                            },
                        }
                    )

            logger.info(f"Found {len(programs)} Intigriti programs")

        except Exception as e:
            logger.error(f"Error fetching Intigriti data: {e}")

        return programs

    def extract_targets(self, program: Dict) -> List[str]:
        targets = []
        platform = program.get("platform", "unknown")

        if platform == "hackerone":
            try:
                relationships = program["data"].get("relationships", {})
                structured_scopes = relationships.get("structured_scopes", {}).get(
                    "data", []
                )

                for scope in structured_scopes:
                    attrs = scope.get("attributes", {})
                    if not attrs.get("eligible_for_bounty", True):
                        continue

                    asset_type = attrs.get("asset_type", "")
                    asset_identifier = attrs.get("asset_identifier", "")

                    if asset_type in ["URL", "WILDCARD"]:
                        if asset_type == "WILDCARD":
                            if self.use_subdomains:
                                targets.append(asset_identifier)
                            else:
                                clean_domain = asset_identifier.replace("*.", "")
                                targets.append(HELPERS.add_https_prefix(clean_domain))
                        else:
                            targets.append(HELPERS.add_https_prefix(asset_identifier))
            except Exception as e:
                logger.warning(f"Error extracting HackerOne targets: {e}")
        elif platform == "bugcrowd":
            try:
                for target in program["data"].get("targets", []):
                    target_name = target.get("uri") or target.get("name")

                    if not target_name:
                        continue

                    if "http" in target_name.lower() or "." in target_name:
                        if "*" in target_name:
                            if self.use_subdomains:
                                targets.append(target_name)
                            else:
                                clean_domain = target_name.replace("*.", "")
                                targets.append(HELPERS.add_https_prefix(clean_domain))
                        else:
                            targets.append(HELPERS.add_https_prefix(target_name))
            except Exception as e:
                logger.warning(f"Error extracting BugCrowd targets: {e}")

        elif platform == "intigriti":
            try:
                raw_targets = program["data"].get("targets", [])

                for target in raw_targets:
                    t_type = target.get("type", "")
                    if not t_type:
                        continue

                    t_type = t_type.lower()
                    endpoint = target.get("endpoint", "")

                    if t_type == "wildcard":
                        if self.use_subdomains:
                            targets.append(endpoint)
                        else:
                            clean = endpoint.replace("*.", "")
                            targets.append(HELPERS.add_https_prefix(clean))
                    elif t_type == "url":
                        targets.append(HELPERS.add_https_prefix(endpoint))

            except Exception as e:
                logger.warning(f"Error extracting Intigriti targets: {e}")

        return targets

    def enumerate_subdomains(self, wildcard: str) -> List[str]:
        """
        Uses the installed 'subfinder' CLI tool to enumerate subdomains.
        Much more reliable than querying crt.sh directly via requests.
        """
        subdomains = []
        
        domains = re.findall(
            r"\*[\w\.-]*?\.([\w\.-]+[a-z]{2,})", wildcard, re.IGNORECASE
        )

        if not domains:
            logger.info(
                f"  No wildcard domain found in target string: {wildcard[:30]}..."
            )
            return []

        unique_domains = set(domains)

        for domain in unique_domains:
            logger.info(f"Running subfinder for {domain}...")

            # Skipping tlds
            if not "." in domain:
                continue

            try:
                if not shutil.which("subfinder"):
                    logger.error("Subfinder not found! Please install it with: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
                    subdomains.append(f"https://{domain}")
                    continue

                command = ["subfinder", "-d", domain, "-silent", "-all"]
                
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300 
                )

                if process.returncode == 0:
                    found = process.stdout.splitlines()
                    logger.info(f"  > Found {len(found)} subdomains for {domain}")
                    
                    for sub in found:
                        sub = sub.strip()
                        if sub:
                            subdomains.append(f"https://{sub}")
                else:
                    logger.warning(f"Subfinder error for {domain}: {process.stderr}")

            except subprocess.TimeoutExpired:
                logger.warning(f"Subfinder timed out for {domain}")
            except Exception as e:
                logger.warning(f"Error enumerating subdomains for {domain}: {e}")

        if not subdomains:
            for domain in unique_domains:
                subdomains.append(f"https://{domain}")

        return subdomains

    def load_existing_programs(self) -> List[Dict]:
        programs = HELPERS.get_from_cache("programs")

        if not programs:
            return []

        timestamp = programs.get("timestamp")
        data = programs.get("data")

        try:
            print(f"\nFound existing program data:")
            print(f"  Collected: {timestamp}")
            print(f"  Programs: {len(data)}")

            while True:
                response = input("\nUse this data? (y/n): ").strip().lower()
                if response in ["y", "yes"]:
                    logger.info(f"Using existing program data from {timestamp}")
                    return data
                elif response in ["n", "no"]:
                    logger.info("Will fetch fresh program data")
                    return []
                else:
                    print("Please enter 'y' or 'n'")

        except Exception as e:
            logger.warning(f"Error reading existing program file: {e}")
            return []

    def process_program(self, program: Dict) -> List[str]:
        raw_targets = self.extract_targets(program)
        final_urls = []

        for t in raw_targets:
            if "*" in t and self.use_subdomains:
                subdomains = self.enumerate_subdomains(t)
                final_urls.extend(subdomains)
            else:
                final_urls.append(t)

        return final_urls

    def save_targets_to_text(self, urls: set[str]):
        """Saves URLs to a .txt file, optionally skipping the first N items."""
        sorted_urls = sorted(urls)

        with open(GLOBALS.TARGETS_FILE, "w") as f:
            for url in sorted_urls:
                f.write(f"{url}\n")

        logger.info(f"Saved target list to {GLOBALS.TARGETS_FILE}")

    def load_targets_list(self) -> Optional[set[str]]:
        """Loads the fully enumerated list if it exists."""
        if not (Path.home() / ".cache" / "shadowScanner" / "targets.json").exists():
            return None

        try:
            with open(
                (Path.home() / ".cache" / "shadowScanner" / "targets.json"), "r"
            ) as f:
                data = json.load(f)

            print(f"\n[!] Found cached target list from {data.get('timestamp')}")
            print(f"    Contains {len(data.get('urls', []))} pre-resolved URLs.")

            while True:
                choice = (
                    input("    Skip generation and use this list? (y/n): ")
                    .strip()
                    .lower()
                )
                if choice in ["y", "yes"]:
                    return set(data.get("urls", {}))
                elif choice in ["n", "no"]:
                    return None
        except Exception as e:
            logger.warning(f"Could not load targets file: {e}")
            return None

    def generate(
        self, use_hackerone: bool, use_bugcrowd: bool, use_intigriti: bool
    ) -> bool:

        all_urls = self.load_targets_list()
        if all_urls:
            self.save_targets_to_text(all_urls)  # type: ignore
            return True


        if GLOBALS.TARGETS_FILE.exists():
            count = sum(1 for _ in open(GLOBALS.TARGETS_FILE))
            print(f"\n[!] Found existing target list with {count} URLs.")
            if input("    Skip generation and use this list? (y/n): ").lower() in ["y","yes"]:
                return True

        all_programs = self.load_existing_programs()
        if not all_programs:
            logger.info("Fetching programs from APIs...")
            if use_hackerone:
                all_programs.extend(self.fetch_hackerone_programs())
            if use_bugcrowd:
                all_programs.extend(self.fetch_bugcrowd_programs())
            if use_intigriti:
                all_programs.extend(self.fetch_intigriti_programs())

            HELPERS.store_in_cache(
                "programs",
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "data": all_programs,
                },
            )

        if not all_programs:
            logger.error("No programs found.")
            return False

        logger.info(f"Enumerating subdomains for {len(all_programs)} programs...")
        generated_urls = []

        try:
            for prog in tqdm(all_programs, desc="Processing Programs"):
                generated_urls.extend(self.process_program(prog))
        except KeyboardInterrupt:
            logger.warning(
                "\nTarget generation interrupted! Saving what we have so far..."
            )

        if not generated_urls:
            logger.error("No URLs generated.")
            return False

        self.save_targets_to_text(set(generated_urls))
        return True

def main():
    parser = argparse.ArgumentParser(
        description="ShadowScanner: BBP Discovery & Nuclei Orchestrator"
    )

    parser.add_argument("--hackerone", "-H", action="store")
    parser.add_argument(
        "--subdomains", action="store_true", help="Enumerate subdomains"
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)

    args = parser.parse_args()
    validate_args(args)
    HELPERS.configure_logging(args.verbose)

    if args.hackerone:
        HELPERS.store_in_cache("hackerone_api_key", args.hackerone)
    hackerone_key = HELPERS.get_from_cache("hackerone_api_key")

    generator = TargetGenerator(
        hackerone_key=hackerone_key, use_subdomains=args.subdomains
    )

    generator.generate(
        use_hackerone=bool(hackerone_key),
        use_bugcrowd=True,
        use_intigriti=True,
    )


if __name__ == "__main__":
    main()
