import argparse
import copy
import hashlib
import ipaddress
import json
import re
from pathlib import Path


FIELDS = ('name', 'policies', 'condition', 'expires_on', 'not_before', 'status')
METADATA = ('id', 'creator_email_at_creation', 'issued_on', 'last_used_on', 'modified_on', 'provisioner_id', 'provisioner_type')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def token_body(token):
    if set(token) - set(FIELDS) - set(METADATA):
        raise ValueError('Unrecognized Token fields; inspect the current API schema before planning')
    if not isinstance(token.get('name'), str) or not token['name'] or not token.get('policies'):
        raise ValueError('Token export must include name and nonempty policies')
    body = {key: copy.deepcopy(token[key]) for key in FIELDS if key in token}
    for policy in body['policies']:
        if not policy.get('permission_groups') or not policy.get('resources'):
            raise ValueError('Token export lacks complete policy details')
    return body


def cidrs(items):
    return list(dict.fromkeys(str(ipaddress.ip_network(value)) for value in items))


def build_plan(token, incoming, owner, account_id, mode, condition_key):
    token_id = token.get('id', '')
    if not re.fullmatch('[a-fA-F0-9]{32}', token_id):
        raise ValueError('Expected a 32-character Token ID, never a Token secret')
    if owner == 'account' and not re.fullmatch('[a-fA-F0-9]{32}', account_id or ''):
        raise ValueError('Account token requires a 32-character account ID')
    if owner == 'user' and account_id:
        raise ValueError('User token must not include an account ID')
    before = token_body(token)
    after = copy.deepcopy(before)
    condition = after.setdefault('condition', {})
    if condition is None:
        condition = after['condition'] = {}
    existing_keys = [key for key in ('request.ip', 'request_ip') if key in condition]
    if len(existing_keys) > 1:
        raise ValueError('Ambiguous request.ip/request_ip keys; reconcile API schema first')
    if existing_keys and condition_key and existing_keys[0] != condition_key:
        raise ValueError('Condition key conflicts with the exported token')
    key = existing_keys[0] if existing_keys else condition_key
    if key is None:
        raise ValueError('No existing IP condition; specify the wire key verified for this API')
    rule = condition.setdefault(key, {})
    old = cidrs(rule.get('in', []))
    incoming = cidrs(incoming)
    if not incoming:
        raise ValueError('Refusing an empty allowlist')
    target = cidrs(old + incoming) if mode == 'add' else incoming
    rule['in'] = target
    excluded = cidrs(rule.get('not_in', []))
    if any(n.prefixlen == 0 for n in map(ipaddress.ip_network, target)):
        raise ValueError('Refusing unrestricted /0 networks')
    path = f'/accounts/{account_id}/tokens/{token_id}' if owner == 'account' else f'/user/tokens/{token_id}'
    return {
        'format': 1,
        'baseSha256': digest({'id': token_id, 'body': before}),
        'before': before,
        'request': {'method': 'PUT', 'path': path, 'body': after},
        'summary': {
            'mode': mode, 'tokenId': token_id, 'tokenName': token['name'],
            'oldCount': len(old), 'newCount': len(target),
            'added': [v for v in target if v not in old],
            'removed': [v for v in old if v not in target],
            'preservedNotIn': excluded,
            'authorizationPoliciesUnchanged': before['policies'] == after['policies'],
            'note': 'CIDR entry differences; overlapping ranges require IP-set review. No request sent.',
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token-file', type=Path, required=True)
    parser.add_argument('--cidr-file', type=Path, required=True)
    parser.add_argument('--owner', choices=['account', 'user'], required=True)
    parser.add_argument('--account-id')
    parser.add_argument('--mode', choices=['add', 'replace'], default='add')
    parser.add_argument('--condition-key', choices=['request.ip', 'request_ip'])
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    exported = json.loads(args.token_file.read_text())
    if 'success' in exported:
        if exported['success'] is not True:
            raise ValueError('Token export is a failed API response')
        token = exported['result']
    else:
        token = exported
    raw = args.cidr_file.read_text()
    incoming = [v.strip() for v in re.split(r'[,\s]+', raw) if v.strip()]
    plan = build_plan(token, incoming, args.owner, args.account_id, args.mode, args.condition_key)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {'plan.json': plan, 'request-body.json': plan['request']['body']}
    if any((args.output_dir / name).exists() for name in outputs):
        raise FileExistsError('Use a fresh output directory to preserve prior plans')
    for name, content in outputs.items():
        target = args.output_dir / name
        with target.open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(content, indent=2) + '\n')
        target.chmod(0o600)
    print(json.dumps({key: value for key, value in plan['summary'].items() if key not in ('added', 'removed')}, indent=2))


if __name__ == '__main__':
    main()
