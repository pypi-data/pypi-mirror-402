import logging
import requests
import shadowScanner.helpers as HELPERS

logger = logging.getLogger()

def validate_args(args):
    # if args.status_codes:
    #     if invalid_code := validate_status_codes(args.status_codes):
    #         logger.error(f"Invalid status code: {invalid_code}")
    #         exit(1)

    if args.hackerone:
        if http_error := validate_hackerone_api_key(args.hackerone):
            logger.error(f"Invalid hackerone api key: {http_error}")
            exit(1)

    # if args.threads:
    #     if args.threads <= 0:
    #         logger.error(f"Invalid thread count: {args.threads}")


def validate_status_codes(codes: list):
    for code in codes:
        if not 100 <= code <= 599:
            return code
    return None


def validate_hackerone_api_key(key: str):
    username, token = HELPERS.split_hackerone_key(key)

    if not token:
        return "Wrong api key format (format: username:token)"

    headers = {"Accept": "application/json"}

    with HELPERS.Spinner("Validating Hackerone api key"):
        r = requests.get(
            "https://api.hackerone.com/v1/hackers/programs",
            auth=(username, token),
            headers=headers,
        )

    try:
        if r.status_code != 200:
            r.raise_for_status()
    except requests.HTTPError as e:
        return str(e)
    
    return None
