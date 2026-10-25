import argparse
import urllib.request
import datetime
import hashlib
import ipaddress
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--source-file', type=Path)
    source_group.add_argument('--fetch-openai', action='store_true')
    parser.add_argument('--condition-key', choices=['request.ip', 'request_ip'], default='request_ip')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--add', action='append', default=[])
    args = parser.parse_args()
    source_url = 'https://openai.com/chatgpt-agents.json' if args.fetch_openai else None
    fetched_at = None
    if source_url:
        with urllib.request.urlopen(source_url, timeout=30) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Feed exceeds expected maximum size')
        fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    else:
        raw = args.source_file.read_bytes()
    source = json.loads(raw)
    rows = source['prefixes']
    if not rows:
        raise ValueError('prefixes must not be empty')
    values = []
    for row in rows:
        keys = [key for key in ('ipv4Prefix', 'ipv6Prefix') if key in row]
        if len(keys) != 1:
            raise ValueError('Each prefix must contain exactly one IP prefix')
        network = ipaddress.ip_network(row[keys[0]])
        if network.version != (4 if keys[0] == 'ipv4Prefix' else 6):
            raise ValueError('IP version does not match prefix field')
        values.append(str(network))
    additions = list(dict.fromkeys(str(ipaddress.ip_network(v)) for v in args.add))
    values = [v for v in dict.fromkeys(values) if v not in additions] + additions
    metadata = {
        'sourceCreationTime': source['creationTime'],
        'sourceUrl': source_url,
        'fetchedAt': fetched_at,
        'conditionKey': args.condition_key,
        'generatedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'sourceEntries': len(rows),
        'entries': len(values),
        'ipv4': sum(ipaddress.ip_network(v).version == 4 for v in values),
        'ipv6': sum(ipaddress.ip_network(v).version == 6 for v in values),
        'addedCidrs': additions,
    }
    outputs = {
        'source.json': raw,
        'allowlist.txt': ('\n'.join(values) + '\n').encode(),
        'allowlist-comma.txt': (','.join(values) + '\n').encode(),
        'condition.json': (json.dumps({'condition': {args.condition_key: {'in': values}}}, indent=2) + '\n').encode(),
        'metadata.json': (json.dumps(metadata, indent=2) + '\n').encode(),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if any((args.output_dir / name).exists() for name in outputs):
        raise FileExistsError('Use a fresh output directory to preserve previous artifacts')
    for name, content in outputs.items():
        (args.output_dir / name).write_bytes(content)
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
