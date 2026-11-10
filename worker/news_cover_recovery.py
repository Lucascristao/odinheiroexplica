"""Find an uploaded, unchanged news episode whose cover still needs delivery.

No YouTube writes here. The workflow generates/reviews pixels and attaches only
to the exact receipted video. Failed optional covers never hold up publication.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from restore_news_publication import has_completed_upload


def gh_json(*args):
    return json.loads(subprocess.check_output(['gh', *args], text=True, encoding='utf-8'))


def validate_receipt(receipt):
    pid = receipt.get('project_id', '')
    if (not re.fullmatch(r'noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+', pid)
            or not re.fullmatch(r'[A-Za-z0-9_-]{11}', receipt.get('video_id', ''))
            or receipt.get('destination') != 'youtube'
            or receipt.get('privacy_requested') != 'private'):
        raise ValueError('Cover recovery requires the exact original news upload receipt')
    return pid


def already_delivered(delivery, receipt, folder):
    image = folder / 'thumbnail.jpg'
    if not image.is_file():
        image = folder / 'thumbnail.png'
    return (image.is_file() and delivery.get('project_id') == receipt['project_id']
            and delivery.get('video_id') == receipt['video_id']
            and delivery.get('thumbnail_sha256') == hashlib.sha256(image.read_bytes()).hexdigest())


def retry_available(state, now, max_attempts=3, cooldown_minutes=60):
    attempts = state.get('attempts', [])
    if len(attempts) >= max_attempts:
        return False
    if attempts:
        last = datetime.fromisoformat(attempts[-1]['started_at'].replace('Z', '+00:00'))
        if now - last < timedelta(minutes=cooldown_minutes):
            return False
    return True


def select(root, repo, *, source_run=None, project_id=None, force=False, now=None):
    now = now or datetime.now(timezone.utc)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    if source_run:
        runs = [gh_json('api', f'repos/{repo}/actions/runs/{int(source_run)}')]
    else:
        runs = gh_json('api', f'repos/{repo}/actions/workflows/render-news-single.yml/runs?per_page=40')['workflow_runs']
    proof_dir = root / 'render-output/private-proof'
    proof_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((root / 'config/news-autonomy.json').read_text(encoding='utf-8')).get('thumbnail_recovery', {})
    if config.get('enabled') is False and not force:
        return None
    for run in runs:
        if (run.get('head_branch') != 'main' or run.get('status') != 'completed'
                or run.get('path', '').split('@')[0] != '.github/workflows/render-news-single.yml'
                or (run.get('head_repository') or {}).get('full_name') != repo):
            continue
        created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
        if not project_id and now - created > timedelta(hours=config.get('lookback_hours', 48)):
            continue
        with tempfile.TemporaryDirectory(dir=root / 'render-output') as temporary:
            result = subprocess.run(['gh', 'run', 'download', str(run['id']), '--repo', repo,
                '--name', 'news-single-youtube-private-receipt', '--dir', temporary], capture_output=True)
            if result.returncode:
                continue
            path = Path(temporary) / 'daily-youtube-private.json'
            if not path.is_file():
                continue
            receipt = json.loads(path.read_text(encoding='utf-8'))
            pid = validate_receipt(receipt)
            if project_id and pid != project_id:
                continue
            episode_path = Path('news/episodes') / (pid.removeprefix('noticia-') + '.json')
            episode_file = root / episode_path
            if not episode_file.is_file():
                continue
            episode = json.loads(episode_file.read_text(encoding='utf-8'))
            if episode.get('episode_id') != pid or episode.get('editorial_status') != 'autonomous_fact_checked':
                continue
            folder = root / 'production' / pid
            delivery_path = folder / 'thumbnail-delivery.json'
            deliveries = []
            for item in [delivery_path, Path(temporary) / 'youtube-thumbnail-delivery.json']:
                if item.is_file():
                    deliveries.append(json.loads(item.read_text(encoding='utf-8')))
            if not force and any(already_delivered(item, receipt, folder) for item in deliveries):
                continue
            state_path = folder / 'thumbnail-recovery.json'
            state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'project_id': pid, 'attempts': []}
            if not force and not retry_available(state, now, config.get('max_attempts', 3), config.get('cooldown_minutes', 60)):
                continue
            jobs = gh_json('api', f'repos/{repo}/actions/runs/{run["id"]}/jobs?filter=latest')['jobs']
            if not has_completed_upload(jobs):
                continue
            source = gh_json('api', f'repos/{repo}/contents/{episode_path.as_posix()}?ref={run["head_sha"]}')
            import base64
            if base64.b64decode(source['content']).replace(b'\r\n', b'\n') != episode_file.read_bytes().replace(b'\r\n', b'\n'):
                continue
            (proof_dir / 'daily-youtube-private.json').write_bytes(path.read_bytes())
            folder.mkdir(parents=True, exist_ok=True)
            state['attempts'].append({'started_at': now.isoformat(), 'source_run_id': run['id'], 'status': 'started'})
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            return {'PROJECT_ID': pid, 'EPISODE': episode_path.as_posix(), 'COVER_TARGET_AVAILABLE': 'true'}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-run')
    parser.add_argument('--project-id')
    parser.add_argument('--force-generate', action='store_true')
    args = parser.parse_args()
    if args.project_id and not re.fullmatch(r'noticia-\d{4}-\d{2}-\d{2}-[a-z0-9-]+', args.project_id):
        raise ValueError('Invalid project ID')
    result = select(Path.cwd(), os.environ['GITHUB_REPOSITORY'], source_run=args.source_run,
                    project_id=args.project_id, force=args.force_generate)
    if result:
        with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as stream:
            for key, value in result.items():
                stream.write(key + '=' + value + '\n')
        print('NEWS_COVER_RECOVERY_TARGET', result['PROJECT_ID'])
    else:
        print('NEWS_COVER_RECOVERY_IDLE: no pending receipted cover within the retry window')


if __name__ == '__main__':
    main()
