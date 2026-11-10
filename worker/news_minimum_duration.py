"""Minimum developed content for future news; never pad or slow the voice."""
import math


class DevelopmentIncomplete(RuntimeError):
    """Keep the unverified checkpoint for a later development attempt."""


def policy_for_episode(episode, config):
    policy = (config.get('editorial_quality') or {}).get('minimum_duration') or {}
    if (not policy or episode.get('news_date', '') < policy.get('effective_from_date', '9999')
            or episode.get('episode_id') in policy.get('preserved_episode_ids', [])):
        return None
    return policy


def require_developed_script(episode, config, *, stamp=False):
    policy = policy_for_episode(episode, config)
    if policy is None:
        return
    count = sum(len(s.get('narration', '').split()) for s in episode.get('segments', []))
    if count < policy['minimum_narration_words']:
        raise DevelopmentIncomplete(f"News needs developed content before voice: {count} words; "
            f"minimum preparation {policy['minimum_narration_words']}. Preserve the checkpoint; no short fallback.")
    quality = episode.setdefault('editorial_quality', {}) if stamp else (episode.get('editorial_quality') or {})
    development = (quality.get('review') or {}).get('development_checks') or {}
    if any(development.get(key) is not True for key in (
            'logical_progression', 'substantive_context', 'no_padding_or_repetition', 'opening_question_answered')):
        raise DevelopmentIncomplete('News lacks an approved review of substantive narrative development')
    if stamp:
        quality.update(minimum_duration_seconds=policy['seconds'],
                       minimum_narration_words=policy['minimum_narration_words'],
                       duration_policy_version=policy['version'])
    elif (quality.get('minimum_duration_seconds') != policy['seconds']
          or quality.get('duration_policy_version') != policy['version']):
        raise DevelopmentIncomplete('News lacks the current minimum-duration contract before voice')


def require_measured_duration(qa, seconds):
    video = (qa.get('video') or {}).get('video_seconds')
    scenes = qa.get('scenes') or []
    durations = [s.get('audio_seconds') for s in scenes]
    if (type(video) not in (int, float) or not math.isfinite(video) or not scenes
            or any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in durations)):
        raise ValueError('Minimum duration requires measured finite narration and video durations')
    narration = sum(durations)
    if video < seconds or narration < seconds:
        raise ValueError(f'News minimum is {seconds} real seconds of narration and video; '
                         f'observed narration={narration}, video={video}. No padding or slowdown.')


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--render-input', required=True)
    args = parser.parse_args()
    project = json.loads(Path(args.project).read_text(encoding='utf-8'))
    timeline = json.loads(Path(args.render_input).read_text(encoding='utf-8'))
    minimum = ((project.get('editorial') or {}).get('quality_contract') or {}).get('minimum_duration_seconds')
    if minimum:
        require_measured_duration({'video': {'video_seconds': timeline['duration_in_frames'] / timeline['fps']},
            'scenes': [{'audio_seconds': s.get('audio_duration_seconds')} for s in timeline['scenes']]}, minimum)
    print('NEWS_MEASURED_NARRATION_DURATION_PASS', minimum or 'archived contract')
