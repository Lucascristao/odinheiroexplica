"""Withdraw only one explicitly recorded, receipted incorrect news video."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import time
from pathlib import Path
from youtube_publication import youtube_service, assert_channel, EXPECTED_ID


def hold(service, record, receipt, episode_bytes):
    pid, vid = record['project_id'], record['video_id']
    if (receipt.get('project_id') != pid or receipt.get('video_id') != vid
            or receipt.get('destination') != 'youtube'
            or record.get('episode_sha256') != hashlib.sha256(episode_bytes.replace(b'\r\n', b'\n')).hexdigest()
            or len(record.get('reason', '')) < 30 or record.get('requested_privacy') != 'private'):
        raise ValueError('Hold requires original episode, exact upload receipt and material reason')
    assert_channel(service)
    items = service.videos().list(part='status,snippet', id=vid).execute().get('items', [])
    if (len(items) != 1 or items[0].get('id') != vid
            or items[0].get('snippet', {}).get('channelId') != EXPECTED_ID
            or 'ODE_EPISODE_' + pid not in items[0].get('snippet', {}).get('tags', [])):
        raise ValueError('Hold video/channel/episode identity mismatch')
    previous = items[0].get('status', {}).get('privacyStatus')
    if previous != 'private':
        service.videos().update(part='status', body={'id': vid, 'status': {'privacyStatus': 'private'}}).execute()
    for attempt in range(5):
        observed = service.videos().list(part='status,snippet', id=vid).execute().get('items', [])
        if len(observed) == 1 and observed[0].get('status', {}).get('privacyStatus') == 'private':
            break
        if attempt == 4:
            raise ValueError('YouTube did not confirm private status')
        time.sleep(3 * (attempt + 1))
    return {**record, 'previous_privacy': previous, 'confirmed_privacy': 'private',
            'confirmed_at': datetime.now(timezone.utc).isoformat()}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--record', required=True)
    p.add_argument('--receipt', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    record = json.loads(Path(args.record).read_text(encoding='utf-8'))
    episode = Path('news/episodes') / (record['project_id'].removeprefix('noticia-') + '.json')
    result = hold(youtube_service(), record, json.loads(Path(args.receipt).read_text(encoding='utf-8')), episode.read_bytes())
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('NEWS_CONTENT_HOLD_CONFIRMED', result['video_id'], result['confirmed_privacy'])
