import json
import os
import re
import requests

DEFAULT_WINDOW_SECONDS = 600
DEFAULT_OVERLAP_SECONDS = 60

EMPTY_SCHEMA = {
    "Participants": [],
    "Goals": [],
    "DiscussionTopics": [],
    "ActionItems": [],
    "Decisions": []
}

def _extract_json_from_completion(completion_text):
    if not completion_text:
        return None

    match = re.search(r'```json\s*(\{.*\})\s*```', completion_text, re.DOTALL)
    if match:
        return match.group(1)

    start = completion_text.find("{")
    end = completion_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return completion_text[start:end + 1]

    return None

def _safe_parse_json(json_text):
    if not json_text:
        return None
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return None

def _normalize_dedupe_key(value):
    if not isinstance(value, str):
        return None
    return " ".join(value.strip().split()).lower()

def _merge_unique_strings(target_list, source_list):
    if not source_list:
        return
    existing = {_normalize_dedupe_key(item): item for item in target_list if isinstance(item, str)}
    for item in source_list:
        if not isinstance(item, str):
            continue
        key = _normalize_dedupe_key(item)
        if not key or key in existing:
            continue
        existing[key] = item
        target_list.append(item)

def _parse_time_range(time_range):
    if not isinstance(time_range, str):
        return None
    parts = [part.strip() for part in time_range.split("-")]
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None

def _merge_discussion_topics(all_topics, new_topics):
    if not new_topics:
        return
    for topic in new_topics:
        if isinstance(topic, dict):
            all_topics.append(topic)

def _sort_discussion_topics(topics):
    def sort_key(topic):
        parsed = _parse_time_range(topic.get("Time"))
        if parsed:
            return parsed[0]
        return float("inf")
    topics.sort(key=sort_key)

def _chunk_audio_segments(segments, window_seconds, overlap_seconds):
    if not segments:
        return []

    segments_sorted = sorted(segments, key=lambda s: s.get("start_time", 0))
    blocks = []
    start_index = 0
    window_start = segments_sorted[0].get("start_time", 0)
    window_end = window_start + window_seconds

    while start_index < len(segments_sorted):
        block = []
        index = start_index
        while index < len(segments_sorted):
            segment = segments_sorted[index]
            start_time = segment.get("start_time", 0)
            if start_time < window_end:
                block.append(segment)
                index += 1
            else:
                break

        if block:
            blocks.append(block)

        if index >= len(segments_sorted):
            break

        window_start = max(0, window_end - overlap_seconds)
        window_end = window_start + window_seconds

        while start_index < len(segments_sorted):
            if segments_sorted[start_index].get("start_time", 0) >= window_start:
                break
            start_index += 1

    return blocks

def _build_prompt(audio_segments):
    template_file_path = os.path.join(os.path.dirname(__file__), "./prompt_template.txt")
    with open(template_file_path, 'r') as template_file:
        prompt_template = template_file.read()
    return prompt_template.replace("{audio_segments}", json.dumps({"audio_segments": audio_segments}, indent=2))

def _invoke_huggingface(prompt):
    api_url = os.environ.get("HF_API_URL", "https://router.huggingface.co/v1/chat/completions")
    model_id = os.environ.get("HF_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")
    api_token = os.environ.get("HF_API_TOKEN")

    if not api_token:
        raise ValueError("HF_API_TOKEN must be set.")

    messages = [
        {
            "role": "system",
            "content": (
                "You summarize meeting transcript chunks into JSON. "
                "Return ONLY a JSON object wrapped in a ```json code block."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = requests.post(
        api_url,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        },
        json={
            "model": model_id,
            "messages": messages
        },
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(f"Hugging Face error: {response.status_code} {response.text}")

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return {"completion": content}

def extract_meeting_summary(audio_segments, window_seconds=DEFAULT_WINDOW_SECONDS, overlap_seconds=DEFAULT_OVERLAP_SECONDS):
    processed_segments = []
    for segment in audio_segments:
        processed_segments.append({
            "start_time": segment['start_time'],
            "end_time": segment['end_time'],
            "transcript": segment['transcript']
        })

    blocks = _chunk_audio_segments(processed_segments, window_seconds, overlap_seconds)
    if not blocks:
        return EMPTY_SCHEMA.copy()

    merged = {key: list(value) for key, value in EMPTY_SCHEMA.items()}

    for block in blocks:
        prompt = _build_prompt(block)
        response_body = _invoke_huggingface(prompt)
        completion_text = response_body.get("completion", "")
        json_text = _extract_json_from_completion(completion_text)
        parsed = _safe_parse_json(json_text)
        if not isinstance(parsed, dict):
            continue

        _merge_unique_strings(merged["Participants"], parsed.get("Participants", []))
        _merge_unique_strings(merged["Goals"], parsed.get("Goals", []))
        _merge_unique_strings(merged["ActionItems"], parsed.get("ActionItems", []))
        _merge_unique_strings(merged["Decisions"], parsed.get("Decisions", []))
        _merge_discussion_topics(merged["DiscussionTopics"], parsed.get("DiscussionTopics", []))

    _sort_discussion_topics(merged["DiscussionTopics"])

    return merged
