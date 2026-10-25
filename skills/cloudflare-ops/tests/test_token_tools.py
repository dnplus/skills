import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from token_ip_plan import build_plan
from apply_token_ip_plan import apply_plan, validate, check_target, token_lock


class TokenPolicyTests(unittest.TestCase):
    def setUp(self):
        self.token = {
            'id': 'a' * 32, 'name': 'fixture-observe', 'status': 'active',
            'expires_on': '2027-01-01T00:00:00Z', 'not_before': '2026-01-01T00:00:00Z',
            'policies': [{'effect': 'allow', 'permission_groups': [{'id': 'b' * 32}],
                          'resources': {'fixture-worker': '*'}}],
            'condition': {'request_ip': {'in': ['192.0.2.0/24'], 'not_in': ['192.0.2.1/32']}},
            'last_used_on': '2026-10-01T00:00:00Z',
        }

    def plan(self, mode='add'):
        return build_plan(self.token, ['198.51.100.0/24', '2001:db8::/32'], 'account', 'c' * 32, mode, None)

    def test_add_preserves_scope_ttl_status_and_exclusions(self):
        plan = self.plan()
        body = plan['request']['body']
        for key in ('policies', 'expires_on', 'not_before', 'status', 'name'):
            self.assertEqual(body[key], self.token[key])
        self.assertEqual(body['condition']['request_ip']['not_in'], ['192.0.2.1/32'])
        self.assertIn('192.0.2.0/24', body['condition']['request_ip']['in'])
        self.assertNotIn('last_used_on', body)
        self.assertEqual(self.token['condition']['request_ip']['in'], ['192.0.2.0/24'])

    def test_unknown_api_fields_fail_closed(self):
        self.token['future_constraint'] = {'purpose': 'fixture'}
        with self.assertRaises(ValueError): self.plan()

    def test_independent_target_must_match(self):
        plan = self.plan()
        check_target(plan, 'a' * 32, 'account', 'c' * 32)
        for token_id, owner, account_id in [('d' * 32, 'account', 'c' * 32), ('a' * 32, 'account', 'd' * 32), ('a' * 32, 'user', None)]:
            with self.assertRaises(ValueError): check_target(plan, token_id, owner, account_id)

    def test_same_token_local_updates_are_serialized(self):
        with token_lock('/fixture-test/token-lock'):
            with self.assertRaises(ValueError):
                with token_lock('/fixture-test/token-lock'): pass

    def test_replace_reports_removed_entries(self):
        plan = self.plan('replace')
        self.assertEqual(plan['summary']['removed'], ['192.0.2.0/24'])
        validate(plan)

    def test_existing_wire_key_preserved(self):
        self.token['condition']['request.ip'] = self.token['condition'].pop('request_ip')
        self.assertIn('request.ip', self.plan()['request']['body']['condition'])

    def test_new_condition_requires_explicit_key(self):
        self.token.pop('condition')
        with self.assertRaises(ValueError): self.plan()
        plan = build_plan(self.token, ['192.0.2.0/24'], 'user', None, 'add', 'request_ip')
        validate(plan)
        self.assertEqual(plan['request']['path'], '/user/tokens/' + 'a' * 32)

    def test_reject_empty_and_unrestricted_lists(self):
        for values in ([], ['0.0.0.0/0'], ['::/0'], ['not-a-cidr']):
            with self.assertRaises(ValueError):
                build_plan(self.token, values, 'account', 'c' * 32, 'replace', None)

    def test_reject_ambiguous_and_conflicting_wire_keys(self):
        with self.assertRaises(ValueError):
            build_plan(self.token, ['192.0.2.0/24'], 'account', 'c' * 32, 'add', 'request.ip')
        self.token['condition']['request.ip'] = {}
        with self.assertRaises(ValueError): self.plan()

    def test_reject_scope_ttl_status_and_exclusion_tampering(self):
        for field, value in [('policies', []), ('expires_on', '2035-01-01T00:00:00Z'), ('status', 'disabled')]:
            plan = self.plan(); plan['request']['body'][field] = value
            with self.assertRaises(ValueError): validate(plan)
        plan = self.plan(); plan['request']['body']['condition']['request_ip']['not_in'] = []
        with self.assertRaises(ValueError): validate(plan)

    def test_reject_changed_baseline_or_arbitrary_endpoint(self):
        plan = self.plan(); plan['before']['name'] = 'changed'
        with self.assertRaises(ValueError): validate(plan)
        plan = self.plan(); plan['request']['path'] = '/accounts/' + 'c' * 32 + '/workers/scripts'
        with self.assertRaises(ValueError): validate(plan)

    def test_drift_stops_before_write(self):
        calls = []
        def api(method, path, credential, body=None):
            calls.append(method)
            result = copy.deepcopy(self.token); result['policies'][0]['resources'] = {'different': '*'}
            return result
        with self.assertRaises(ValueError): apply_plan(self.plan(), 'synthetic', api)
        self.assertEqual(calls, ['GET'])

    def test_matching_readback_single_put_and_no_ip_claim(self):
        state = copy.deepcopy(self.token); calls = []
        def api(method, path, credential, body=None):
            calls.append(method)
            if method == 'PUT': state.update(copy.deepcopy(body))
            return copy.deepcopy(state)
        result = apply_plan(self.plan(), 'synthetic', api)
        self.assertEqual(calls, ['GET', 'PUT', 'GET'])
        self.assertEqual(result['sourceIpAuthorization'], 'NOT RUN')

    def test_timeout_after_write_does_not_retry(self):
        calls = []
        def api(method, path, credential, body=None):
            calls.append(method)
            if method == 'PUT': raise TimeoutError('fixture timeout')
            return copy.deepcopy(self.token)
        with self.assertRaises(TimeoutError): apply_plan(self.plan(), 'synthetic', api)
        self.assertEqual(calls, ['GET', 'PUT'])

    def test_readback_mismatch_is_failure(self):
        calls = []
        def api(method, path, credential, body=None):
            calls.append(method); return copy.deepcopy(self.token)
        with self.assertRaises(RuntimeError): apply_plan(self.plan(), 'synthetic', api)
        self.assertEqual(calls, ['GET', 'PUT', 'GET'])

    def test_plan_cli_requires_apply_and_reviewed_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'plan.json'; p.write_text(json.dumps(self.plan()))
            command = [sys.executable, str(SCRIPTS / 'apply_token_ip_plan.py'), '--plan-file', str(p)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'validated_offline_no_request_sent')
            result = subprocess.run(command + ['--apply', '--expected-plan-sha256', 'invalid'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('SHA-256', result.stderr)


class FeedTests(unittest.TestCase):
    def test_mixed_families_dedup_add_and_output_equivalence(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); source = p / 'feed.json'; out = p / 'out'
            raw = json.dumps({'creationTime': 'fixture', 'prefixes': [
                {'ipv4Prefix': '192.0.2.0/24'}, {'ipv6Prefix': '2001:db8::/32'}, {'ipv4Prefix': '192.0.2.0/24'}]})
            source.write_text(raw)
            command = [sys.executable, str(SCRIPTS / 'format_cidrs.py'), '--source-file', str(source),
                       '--output-dir', str(out), '--add', '198.51.100.1/32', '--add', '198.51.100.1/32']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            values = (out / 'allowlist.txt').read_text().splitlines()
            self.assertEqual(values, ['192.0.2.0/24', '2001:db8::/32', '198.51.100.1/32'])
            self.assertEqual((out / 'allowlist-comma.txt').read_text().strip().split(','), values)
            self.assertEqual(json.loads((out / 'condition.json').read_text())['condition']['request_ip']['in'], values)
            self.assertEqual(json.loads((out / 'metadata.json').read_text())['sourceSha256'], hashlib.sha256(raw.encode()).hexdigest())
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_invalid_feed_never_creates_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            for index, rows in enumerate([[], [{'ipv4Prefix': '2001:db8::/32'}], [{'ipv4Prefix': 'broken'}]]):
                source = p / f'{index}.json'; out = p / f'out-{index}'
                source.write_text(json.dumps({'creationTime': 'fixture', 'prefixes': rows}))
                result = subprocess.run([sys.executable, str(SCRIPTS / 'format_cidrs.py'), '--source-file', str(source), '--output-dir', str(out)], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
