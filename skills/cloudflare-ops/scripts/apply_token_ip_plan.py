import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from token_ip_plan import digest, token_body


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate(plan):
    request = plan['request']
    match = re.fullmatch(r'/(?:accounts/[a-fA-F0-9]{32}|user)/tokens/([a-fA-F0-9]{32})', request['path'])
    if plan.get('format') != 1 or request['method'] != 'PUT' or not match:
        raise ValueError('Only a single-token IP update plan is accepted')
    token_id = match.group(1)
    before = plan['before']
    after = request['body']
    if digest({'id': token_id, 'body': before}) != plan['baseSha256']:
        raise ValueError('Plan baseline digest mismatch')
    rule_keys = [key for key in ('request.ip', 'request_ip') if key in (after.get('condition') or {})]
    if len(rule_keys) != 1:
        raise ValueError('Expected one unambiguous IP condition')
    key = rule_keys[0]
    incoming = after['condition'][key]['in']
    if not isinstance(incoming, list) or not incoming:
        raise ValueError('Refusing empty IP conditions')
    networks = [ipaddress.ip_network(value) for value in incoming]
    if any(network.prefixlen == 0 for network in networks):
        raise ValueError('Refusing unrestricted /0 networks')
    if len(set(incoming)) != len(incoming):
        raise ValueError('Duplicate CIDRs in plan')
    expected = copy.deepcopy(before)
    condition = expected.setdefault('condition', {})
    if condition is None:
        condition = expected['condition'] = {}
    condition.setdefault(key, {})['in'] = incoming
    if expected != after:
        raise ValueError('Plan changes fields other than IP allowlist')
    return token_id


@contextmanager
def token_lock(path):
    name = 'cf-ops-token-' + str(os.getuid()) + '-' + hashlib.sha256(path.encode()).hexdigest() + '.lock'
    fd = os.open(Path(tempfile.gettempdir()) / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise ValueError('Token lock is owned by a different user')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another local process is updating this Token') from None
        yield
    finally:
        os.close(fd)


def check_target(plan, token_id, owner, account_id):
    if not re.fullmatch('[a-fA-F0-9]{32}', token_id or ''):
        raise ValueError('Apply requires the independently verified target Token ID')
    if owner == 'account':
        if not re.fullmatch('[a-fA-F0-9]{32}', account_id or ''):
            raise ValueError('Apply requires the independently verified account ID')
        expected = f'/accounts/{account_id}/tokens/{token_id}'
    elif owner == 'user' and not account_id:
        expected = f'/user/tokens/{token_id}'
    else:
        raise ValueError('Apply requires an explicit owner and matching account selection')
    if plan['request']['path'] != expected:
        raise ValueError('Plan target differs from the independently verified target')


def call_api(method, path, credential, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request('https://api.cloudflare.com/client/v4' + path, data=data, method=method,
        headers={'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(5_000_001)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Cloudflare {method} returned HTTP {error.code}; no automatic retry') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError(f'Cloudflare {method} transport failure; no automatic retry') from None
    if len(raw) > 5_000_000:
        raise RuntimeError('Cloudflare response exceeds expected size')
    result = json.loads(raw)
    if result.get('success') is not True:
        raise RuntimeError(f'Cloudflare {method} reported failure; inspect through authorized tools')
    return result['result']


def apply_plan(plan, credential, api=call_api):
    token_id = validate(plan)
    path = plan['request']['path']
    current = api('GET', path, credential)
    current_digest = digest({'id': current.get('id'), 'body': token_body(current)})
    if current.get('id') != token_id or current_digest != plan['baseSha256']:
        raise ValueError('Token changed since planning; create a new plan')
    api('PUT', path, credential, plan['request']['body'])
    verified = api('GET', path, credential)
    if verified.get('id') != token_id or token_body(verified) != plan['request']['body']:
        raise RuntimeError('Write completed but read-back differs; investigate before further changes')
    return {'status': 'configuration_read_back_matched', 'tokenId': token_id,
            'sourceIpAuthorization': 'NOT RUN', 'atomicConditionalWrite': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--expected-token-id')
    parser.add_argument('--expected-account-id')
    parser.add_argument('--owner', choices=['account', 'user'])
    parser.add_argument('--exclusive-writer', action='store_true')
    args = parser.parse_args()
    raw = args.plan_file.read_bytes()
    plan = json.loads(raw)
    validate(plan)
    sha = hashlib.sha256(raw).hexdigest()
    if not args.apply:
        print(json.dumps({'status': 'validated_offline_no_request_sent', 'planSha256': sha}))
        return
    if args.expected_plan_sha256 != sha:
        raise ValueError('Apply requires the SHA-256 of the reviewed plan bytes')
    check_target(plan, args.expected_token_id, args.owner, args.expected_account_id)
    if not args.exclusive_writer:
        raise ValueError('Apply requires coordinated exclusive ownership of Token updates')
    credential = os.environ.get('CF_OPS_TOKEN_ADMIN', '')
    if not credential:
        raise ValueError('CF_OPS_TOKEN_ADMIN must be supplied through secure environment injection')
    with token_lock(plan['request']['path']):
        print(json.dumps(apply_plan(plan, credential)))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if isinstance(error, (RuntimeError, ValueError)):
            print(str(error), file=sys.stderr)
        else:
            print('Operation failed; inspect inputs without displaying credentials. A PUT may already have completed.', file=sys.stderr)
        sys.exit(1)
