#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/afshin/IdeaProjects/sandbox/java-spring-docker')
DEFAULT_MANIFEST = ROOT / 'benchmarks' / 'common' / 'scenarios.json'


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def select_runs(item: dict, profile: str, runs_override: int | None, default_runs: dict) -> int:
    if runs_override is not None:
        return runs_override
    if 'runs' in item and profile in item['runs']:
        return int(item['runs'][profile])
    return int(default_runs[profile])


def main() -> int:
    parser = argparse.ArgumentParser(description='Run all benchmark scenarios and refresh markdown reports.')
    parser.add_argument('--profile', choices=['quick', 'full'], default=None, help='Benchmark profile from scenarios manifest.')
    parser.add_argument('--runs', type=int, default=None, help='Override run count for standard scenarios.')
    parser.add_argument('--skip-native', action='store_true', help='Skip native-vs-jvm benchmark.')
    parser.add_argument('--native-duration', default=None, help='Override native benchmark duration (e.g. 10m, 60m).')
    parser.add_argument('--native-vus', type=int, default=None, help='Override native benchmark virtual users.')
    parser.add_argument('--native-cpu-work', type=int, default=None, help='Override native benchmark CPU work value.')
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST), help='Path to benchmark scenarios manifest JSON.')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    data = load_manifest(manifest_path)

    defaults = data['defaults']
    profile = args.profile or defaults.get('profile', 'quick')
    default_runs = defaults['runs']
    native_defaults = defaults['native'][profile]
    native_cpu_work = int(args.native_cpu_work or defaults['native']['cpu_work'])

    print(f'Using profile: {profile}')
    print(f'Manifest: {manifest_path}')

    for scenario in data['scenarios']:
        if not scenario.get('enabled', True):
            continue

        scenario_id = scenario['id']
        scenario_path = ROOT / scenario['path']
        scenario_type = scenario.get('type', 'standard')

        if scenario_type == 'native':
            if args.skip_native:
                print(f'Skipping native scenario: {scenario_id}')
                continue
            duration = args.native_duration or native_defaults['duration']
            vus = str(args.native_vus or native_defaults['vus'])
            native_runs = str(native_defaults.get('runs', 1))
            env = dict(os.environ)
            env['RUN_PROFILE'] = profile
            print(f"\n=== Scenario: {scenario_id} (duration={duration}, vus={vus}) ===")
            run([
                'bash', str(scenario_path / 'run_native_vs_jvm.sh'),
                '--duration', duration,
                '--vus', vus,
                '--cpu-work', str(native_cpu_work),
                '--runs', native_runs,
            ], env=env)
            run([
                'python3', str(scenario_path / 'analyze_native_vs_jvm.py'),
                str(scenario_path / 'results' / 'raw.csv'),
            ])
            continue

        if not (scenario_path / 'variants').exists():
            print(f'Skipping scenario without variants directory: {scenario_id}')
            continue

        runs = select_runs(scenario, profile, args.runs, default_runs)
        env = dict(os.environ)
        env['RUN_PROFILE'] = profile
        print(f"\n=== Scenario: {scenario_id} (runs={runs}) ===")
        run([
            'bash', str(ROOT / 'benchmarks' / 'common' / 'run_scenario.sh'),
            scenario['path'],
            str(runs),
        ], env=env)

    print('\n=== Updating markdown summaries ===')
    run(['python3', str(ROOT / 'benchmarks' / 'common' / 'update_results.py')])
    print('\nAll done. CSV and markdown reports are updated.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

