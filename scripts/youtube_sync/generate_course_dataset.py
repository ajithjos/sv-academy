#!/usr/bin/env python3
"""Generate the public course dataset from legacy metadata plus YouTube playlists."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import unicodedata
import urllib.parse
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


YOUTUBE_CHANNEL_HANDLE = "@SystemverilogAcademy"
YOUTUBE_CHANNEL_URL = f"https://www.youtube.com/{YOUTUBE_CHANNEL_HANDLE}"
YOUTUBE_PLAYLISTS_URL = f"{YOUTUBE_CHANNEL_URL}/playlists"
USER_AGENT = "Mozilla/5.0"

# Exact legacy-course-to-playlist mappings validated against the public
# channel playlists on June 20, 2026.
MANUAL_PLAYLIST_MAP = {
    "C102_Basic02": "PL7q7nkSfmotviU7n0zZV7tO0ugSXnAuDy",
    "C111_Design01": "PL7q7nkSfmotu0fDb4fVwVmYnWiO9WRw4q",
    "C112_Design": "PL7q7nkSfmotugRbxXVagnEGmOZiLHLD_d",
    "C113_Design": "PL7q7nkSfmots-1G13YGbWJEqMEH4u8Gnj",
    "C121_Verif01": "PL7q7nkSfmotv4_qFU1kmJCeDobCjJlhld",
    "C122_Verif": "PL7q7nkSfmotvrvHX3yj2FChRkxAzXbv3l",
    "C123_Verif": "PL7q7nkSfmotutQcM9VergQFUpyLs6diJ5",
    "C124_Verif": "PL7q7nkSfmotuM8m6MgFIcLGvV7rMJXYdi",
    "C125_Verif05": "PL7q7nkSfmotu4ddfhdt8gW7EkMQepvTCN",
    "C126_Verif06": "PL7q7nkSfmotu2jLS9dspVJWVZ5XA3mum6",
    "C131_Assert01": "PL7q7nkSfmotuKW6Gcyiz2DCju1CkNIC28",
    "C141_Uvm01": "PL7q7nkSfmotsIgPgf9KKfJ1MKfLSPhUmS",
    "C142_Uvm02": "PL7q7nkSfmotvnnYUx7TWipiMZiIuqum3B",
    "C143_Uvm03": "PL7q7nkSfmotvGFs1GxlyevQtV7qOA_NEq",
}

STOPWORDS = {
    "academy",
    "and",
    "basics",
    "beginner",
    "beginners",
    "classes",
    "complete",
    "course",
    "data",
    "design",
    "free",
    "general",
    "in",
    "introduction",
    "intro",
    "lesson",
    "module",
    "of",
    "part",
    "quick",
    "start",
    "sv",
    "systemverilog",
    "the",
    "to",
    "training",
    "tutorial",
    "uvm",
    "verification",
    "vlsi",
    "welcome",
    "with",
    "writing",
}


@dataclass(frozen=True)
class LegacyLectureRef:
    course_position: int
    module_index: int
    module_title: str
    lecture_index: int
    position_in_module: int
    title: str
    content_type: str
    video_source: str
    youtube_url: str
    mux_asset_id: str
    mux_playback_id_public: str
    mux_playback_id_signed: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the SystemVerilog Academy public course dataset."
    )
    parser.add_argument(
        "--legacy-file",
        required=True,
        help="Path to the legacy courses.py file.",
    )
    parser.add_argument(
        "--output-json",
        default="src/content/courses.json",
        help="Path for the generated JSON dataset.",
    )
    parser.add_argument(
        "--report-output",
        default="docs/course-dataset-audit.md",
        help="Path for the generated markdown audit report.",
    )
    parser.add_argument(
        "--snapshot-date",
        default=datetime.now(UTC).date().isoformat(),
        help="Date string to stamp into the generated outputs.",
    )
    return parser.parse_args()


def load_legacy_courses(legacy_file: Path) -> list[dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("legacy_courses", legacy_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load legacy course file: {legacy_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ALL_COURSE_DATA


def fetch_html(url: str) -> str:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT})) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_initial_data(html: str) -> dict[str, Any]:
    match = re.search(r"var ytInitialData = (\{.*?\});</script>", html)
    if not match:
        raise RuntimeError("ytInitialData payload was not found.")
    return json.loads(match.group(1))


def fetch_oembed(video_id: str) -> dict[str, Any]:
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "format": "json",
        }
    )
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT})) as response:
        return json.loads(response.read().decode("utf-8"))


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode(
        "ascii"
    )
    normalized = normalized.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode(
        "ascii"
    )
    normalized = normalized.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def token_set(text: str) -> set[str]:
    return {
        token
        for token in normalize_text(text).split()
        if token not in STOPWORDS and not token.isdigit()
    }


def title_similarity(left: str, right: str) -> float:
    left_text = normalize_text(left)
    right_text = normalize_text(right)

    if not left_text and not right_text:
        return 1.0
    if not left_text or not right_text:
        return 0.0

    left_pairs = set(zip(left_text.split(), left_text.split()[1:]))
    right_pairs = set(zip(right_text.split(), right_text.split()[1:]))
    pair_overlap = 0.0
    if left_pairs or right_pairs:
        pair_overlap = len(left_pairs & right_pairs) / max(
            1, len(left_pairs | right_pairs)
        )

    token_overlap = 0.0
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if left_tokens or right_tokens:
        token_overlap = len(left_tokens & right_tokens) / max(
            1, len(left_tokens | right_tokens)
        )

    sequence_overlap = _sequence_ratio(left_text, right_text)
    return round(max(sequence_overlap, token_overlap, pair_overlap), 4)


def _sequence_ratio(left: str, right: str) -> float:
    # Local import keeps the top-level imports smaller and still stays stdlib-only.
    import difflib

    return difflib.SequenceMatcher(None, left, right).ratio()


def video_id_from_url(url: str) -> str | None:
    if not url:
        return None
    if "youtu.be/" in url:
        return url.rstrip("/").split("/")[-1]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    return params.get("v", [None])[0]


def parse_lesson_number(title: str) -> tuple[int, int] | None:
    patterns = [
        re.compile(r"\bL\s*\.?\s*(\d+)\.(\d+)\b", re.IGNORECASE),
        re.compile(r"[:\s](\d{1,2})\.(\d)\s*:", re.IGNORECASE),
        re.compile(r"\bL\s*\.?\s*(\d{2,3})\b", re.IGNORECASE),
    ]

    for index, pattern in enumerate(patterns):
        match = pattern.search(title)
        if not match:
            continue

        if index == 2:
            digits = match.group(1)
            return int(digits[:-1]), int(digits[-1])

        return int(match.group(1)), int(match.group(2))

    return None


def clean_youtube_lesson_title(title: str) -> str:
    lesson_patterns = [
        r"\bL\s*\.?\s*\d+(?:\.\d+)?\b\s*[:\-]?\s*",
        r"[:\s]\d{1,2}\.\d\s*:\s*",
    ]

    cleaned = title
    for pattern in lesson_patterns:
        cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE)

    return cleaned.strip(" :-")


def extract_duration_text(lockup_view_model: dict[str, Any]) -> str | None:
    overlays = (
        lockup_view_model.get("contentImage", {})
        .get("thumbnailViewModel", {})
        .get("overlays", [])
    )
    for overlay in overlays:
        text = (
            overlay.get("thumbnailBottomOverlayViewModel", {})
            .get("badges", [{}])[0]
            .get("thumbnailBadgeViewModel", {})
            .get("text")
        )
        if text:
            return text
    return None


def extract_channel_playlists() -> dict[str, dict[str, Any]]:
    initial_data = extract_initial_data(fetch_html(YOUTUBE_PLAYLISTS_URL))
    items = (
        initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][3]["tabRenderer"][
            "content"
        ]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0][
            "gridRenderer"
        ]["items"]
    )

    playlists: dict[str, dict[str, Any]] = {}
    for item in items:
        lockup = item["lockupViewModel"]
        playlist_id = lockup["contentId"]
        badge_text = (
            lockup["contentImage"]["collectionThumbnailViewModel"]["primaryThumbnail"][
                "thumbnailViewModel"
            ]["overlays"][0]["thumbnailOverlayBadgeViewModel"]["thumbnailBadges"][0][
                "thumbnailBadgeViewModel"
            ]["text"]
        )
        playlists[playlist_id] = {
            "playlistId": playlist_id,
            "playlistTitle": lockup["metadata"]["lockupMetadataViewModel"]["title"][
                "content"
            ],
            "playlistUrl": f"https://www.youtube.com/playlist?list={playlist_id}",
            "badgeText": badge_text,
        }

    return playlists


def extract_playlist_detail(playlist_id: str) -> dict[str, Any]:
    initial_data = extract_initial_data(
        fetch_html(f"https://www.youtube.com/playlist?list={playlist_id}")
    )
    playlist_title = initial_data["metadata"]["playlistMetadataRenderer"]["title"]
    items = (
        initial_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
            "tabRenderer"
        ]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
            "contents"
        ]
    )

    videos: list[dict[str, Any]] = []
    for position, item in enumerate(items, start=1):
        lockup = item.get("lockupViewModel")
        if not lockup or lockup.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO":
            continue

        youtube_title = lockup["metadata"]["lockupMetadataViewModel"]["title"]["content"]
        video_id = (
            lockup["rendererContext"]["commandContext"]["onTap"]["innertubeCommand"][
                "watchEndpoint"
            ]["videoId"]
        )
        thumbnail_sources = (
            lockup.get("contentImage", {})
            .get("thumbnailViewModel", {})
            .get("image", {})
            .get("sources", [])
        )
        thumbnail_url = thumbnail_sources[-1]["url"] if thumbnail_sources else None

        videos.append(
            {
                "playlistId": playlist_id,
                "playlistTitle": playlist_title,
                "position": position,
                "videoId": video_id,
                "videoUrl": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnailUrl": thumbnail_url,
                "durationText": extract_duration_text(lockup),
                "youtubeTitle": youtube_title,
                "youtubeLessonTitle": clean_youtube_lesson_title(youtube_title),
                "lessonNumber": parse_lesson_number(youtube_title),
            }
        )

    return {
        "playlistId": playlist_id,
        "playlistTitle": playlist_title,
        "playlistUrl": f"https://www.youtube.com/playlist?list={playlist_id}",
        "playlistVideoCount": len(videos),
        "videos": videos,
    }


def flatten_legacy_lectures(course: dict[str, Any]) -> list[LegacyLectureRef]:
    lectures: list[LegacyLectureRef] = []
    course_position = 0

    for module in course["modules"]:
        for position_in_module, lecture in enumerate(module["lectures"], start=1):
            course_position += 1
            lectures.append(
                LegacyLectureRef(
                    course_position=course_position,
                    module_index=module["index"],
                    module_title=module["title"],
                    lecture_index=lecture["index"],
                    position_in_module=position_in_module,
                    title=lecture["title"],
                    content_type=lecture.get("content_type", ""),
                    video_source=lecture.get("video_source", ""),
                    youtube_url=lecture.get("youtube_url", ""),
                    mux_asset_id=lecture.get("mux_asset_id", ""),
                    mux_playback_id_public=lecture.get("mux_playback_id_public", ""),
                    mux_playback_id_signed=lecture.get("mux_playback_id_signed", ""),
                )
            )

    return lectures


def map_lectures_to_playlist(
    legacy_lectures: list[LegacyLectureRef],
    playlist_detail: dict[str, Any],
) -> tuple[
    dict[int, dict[str, Any]],
    list[LegacyLectureRef],
    Counter,
    list[dict[str, Any]],
]:
    videos = playlist_detail["videos"]
    by_video_id = {video["videoId"]: video for video in videos}
    by_lesson_number = {
        tuple(video["lessonNumber"]): video
        for video in videos
        if video["lessonNumber"] is not None
    }

    mapping: dict[int, dict[str, Any]] = {}
    used_video_ids: set[str] = set()
    match_methods: Counter = Counter()
    index_corrections: list[dict[str, Any]] = []

    # Prefer exact legacy video IDs whenever they already exist.
    for lecture in legacy_lectures:
        video_id = video_id_from_url(lecture.youtube_url)
        if not video_id or video_id not in by_video_id or video_id in used_video_ids:
            continue

        mapping[lecture.course_position] = {
            "video": by_video_id[video_id],
            "method": "legacy_video_id",
        }
        used_video_ids.add(video_id)
        match_methods["legacy_video_id"] += 1

    # Then try direct module/lecture-number alignment from the YouTube titles.
    for lecture in legacy_lectures:
        if lecture.course_position in mapping:
            continue

        video = by_lesson_number.get((lecture.module_index, lecture.lecture_index))
        if not video or video["videoId"] in used_video_ids:
            continue

        mapping[lecture.course_position] = {"video": video, "method": "lesson_number"}
        used_video_ids.add(video["videoId"])
        match_methods["lesson_number"] += 1

    # Legacy lecture indexes are not always consistent, so within a module we
    # fall back to position ordering when the remaining counts line up.
    for module_index in sorted({lecture.module_index for lecture in legacy_lectures}):
        remaining_lectures = [
            lecture
            for lecture in legacy_lectures
            if lecture.module_index == module_index
            and lecture.course_position not in mapping
        ]
        remaining_videos = [
            video
            for video in videos
            if video["videoId"] not in used_video_ids
            and video["lessonNumber"] is not None
            and video["lessonNumber"][0] == module_index
        ]
        remaining_lectures.sort(key=lambda lecture: lecture.course_position)
        remaining_videos.sort(key=lambda video: (video["lessonNumber"][1], video["position"]))

        if not remaining_lectures or len(remaining_lectures) != len(remaining_videos):
            continue

        for lecture, video in zip(remaining_lectures, remaining_videos):
            mapping[lecture.course_position] = {"video": video, "method": "module_position"}
            used_video_ids.add(video["videoId"])
            match_methods["module_position"] += 1

            index_corrections.append(
                {
                    "moduleIndex": lecture.module_index,
                    "moduleTitle": lecture.module_title,
                    "legacyLectureIndex": lecture.lecture_index,
                    "legacyPositionInModule": lecture.position_in_module,
                    "legacyLectureTitle": lecture.title,
                    "youtubeLessonNumber": format_lesson_number(video["lessonNumber"]),
                    "youtubeTitle": video["youtubeTitle"],
                }
            )

    unmatched_lectures = [
        lecture
        for lecture in legacy_lectures
        if lecture.course_position not in mapping
    ]
    unmatched_videos = [
        video for video in videos if video["videoId"] not in used_video_ids
    ]

    # If the counts still line up, preserve overall course ordering as a final
    # fallback rather than losing a likely good match.
    if unmatched_lectures and len(unmatched_lectures) == len(unmatched_videos):
        for lecture, video in zip(unmatched_lectures, unmatched_videos):
            mapping[lecture.course_position] = {"video": video, "method": "course_sequence"}
            used_video_ids.add(video["videoId"])
            match_methods["course_sequence"] += 1

        unmatched_lectures = []

    return mapping, unmatched_lectures, match_methods, index_corrections


def format_lesson_number(lesson_number: tuple[int, int] | None) -> str | None:
    if lesson_number is None:
        return None
    return f"L{lesson_number[0]}.{lesson_number[1]}"


def build_video_only_entry(
    lecture: LegacyLectureRef,
    current_video_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    video_id = video_id_from_url(lecture.youtube_url)
    return {
        "legacyIndex": lecture.lecture_index,
        "positionInModule": lecture.position_in_module,
        "title": lecture.title,
        "contentType": lecture.content_type,
        "videoSource": lecture.video_source,
        "legacyYoutubeUrl": lecture.youtube_url,
        "muxAssetId": lecture.mux_asset_id,
        "muxPlaybackIdPublic": lecture.mux_playback_id_public,
        "muxPlaybackIdSigned": lecture.mux_playback_id_signed,
        "youtube": {
            "videoId": video_id,
            "videoUrl": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
            "title": current_video_meta.get("title") if current_video_meta else None,
            "thumbnailUrl": current_video_meta.get("thumbnail_url")
            if current_video_meta
            else None,
            "playlistId": None,
            "playlistTitle": None,
            "lessonNumber": None,
            "moduleIndex": None,
            "lectureIndex": None,
            "durationText": None,
        },
        "match": {
            "status": "matched",
            "method": "legacy_video_id",
            "titleSimilarity": title_similarity(
                lecture.title,
                current_video_meta.get("title", "") if current_video_meta else "",
            ),
        },
    }


def playlist_overlap_candidates(
    direct_video_ids: list[str],
    channel_playlists: dict[str, dict[str, Any]],
    playlist_details: dict[str, dict[str, Any]],
    excluded_playlist_ids: set[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    direct_video_id_set = {video_id for video_id in direct_video_ids if video_id}

    for playlist_id, playlist in channel_playlists.items():
        if playlist_id in excluded_playlist_ids:
            continue

        playlist_video_ids = {
            video["videoId"] for video in playlist_details[playlist_id]["videos"]
        }
        overlap = sorted(direct_video_id_set & playlist_video_ids)
        if not overlap:
            continue

        candidates.append(
            {
                "playlistId": playlist_id,
                "playlistTitle": playlist["playlistTitle"],
                "playlistUrl": playlist["playlistUrl"],
                "playlistVideoCount": playlist_details[playlist_id]["playlistVideoCount"],
                "overlapCount": len(overlap),
                "overlapVideoIds": overlap,
            }
        )

    candidates.sort(key=lambda candidate: (-candidate["overlapCount"], candidate["playlistTitle"]))
    return candidates


def missing_lecture_candidates(
    lecture_title: str,
    all_playlist_videos: list[dict[str, Any]],
    excluded_video_ids: set[str],
    source_playlist_id: str | None,
) -> list[dict[str, Any]]:
    query_tokens = token_set(lecture_title)
    candidates: list[dict[str, Any]] = []

    for video in all_playlist_videos:
        if video["videoId"] in excluded_video_ids:
            continue
        if source_playlist_id and video["playlistId"] == source_playlist_id:
            continue

        candidate_tokens = token_set(video["youtubeLessonTitle"])
        shared_tokens = sorted(query_tokens & candidate_tokens)
        if len(shared_tokens) < 2:
            continue

        similarity = title_similarity(lecture_title, video["youtubeLessonTitle"])
        if similarity < 0.35:
            continue

        candidates.append(
            {
                "videoId": video["videoId"],
                "videoUrl": video["videoUrl"],
                "title": video["youtubeTitle"],
                "playlistId": video["playlistId"],
                "playlistTitle": video["playlistTitle"],
                "similarity": similarity,
                "sharedTokens": shared_tokens,
            }
        )

    candidates.sort(
        key=lambda candidate: (-candidate["similarity"], candidate["title"])
    )
    return candidates[:3]


def build_modules_for_course(
    course: dict[str, Any],
    lecture_lookup: dict[tuple[int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []

    for module in course["modules"]:
        lectures: list[dict[str, Any]] = []
        for position_in_module, lecture in enumerate(module["lectures"], start=1):
            lectures.append(lecture_lookup[(module["index"], position_in_module)])

        modules.append(
            {
                "index": module["index"],
                "title": module["title"],
                "lectures": lectures,
            }
        )

    return modules


def generate_dataset(
    legacy_courses: list[dict[str, Any]],
    channel_playlists: dict[str, dict[str, Any]],
    playlist_details: dict[str, dict[str, Any]],
    snapshot_date: str,
    legacy_file: Path,
) -> tuple[dict[str, Any], str]:
    mapped_playlist_ids = set(MANUAL_PLAYLIST_MAP.values())
    all_playlist_videos = [
        video
        for playlist in playlist_details.values()
        for video in playlist["videos"]
    ]

    direct_video_meta_cache: dict[str, dict[str, Any]] = {}
    assigned_video_ids: set[str] = set()
    course_records: list[dict[str, Any]] = []

    for course in legacy_courses:
        course_info = course["course_info"]
        course_tag = course_info["course_tag"]
        legacy_lectures = flatten_legacy_lectures(course)
        lecture_lookup: dict[tuple[int, int], dict[str, Any]] = {}

        playlist_id = MANUAL_PLAYLIST_MAP.get(course_tag)
        playlist_detail = playlist_details.get(playlist_id) if playlist_id else None
        direct_video_ids = [
            video_id_from_url(lecture.youtube_url)
            for lecture in legacy_lectures
            if lecture.youtube_url
        ]
        direct_video_ids = [video_id for video_id in direct_video_ids if video_id]
        course_discrepancies: list[str] = []
        lecture_match_methods: Counter = Counter()
        legacy_index_corrections: list[dict[str, Any]] = []
        missing_lectures: list[dict[str, Any]] = []

        if playlist_detail:
            mapping, unmatched_lectures, lecture_match_methods, legacy_index_corrections = (
                map_lectures_to_playlist(legacy_lectures, playlist_detail)
            )

            for lecture in legacy_lectures:
                match_record = mapping.get(lecture.course_position)
                if not match_record:
                    continue

                video = match_record["video"]
                assigned_video_ids.add(video["videoId"])
                lecture_lookup[(lecture.module_index, lecture.position_in_module)] = {
                    "legacyIndex": lecture.lecture_index,
                    "positionInModule": lecture.position_in_module,
                    "title": lecture.title,
                    "contentType": lecture.content_type,
                    "videoSource": lecture.video_source,
                    "legacyYoutubeUrl": lecture.youtube_url,
                    "muxAssetId": lecture.mux_asset_id,
                    "muxPlaybackIdPublic": lecture.mux_playback_id_public,
                    "muxPlaybackIdSigned": lecture.mux_playback_id_signed,
                    "youtube": {
                        "videoId": video["videoId"],
                        "videoUrl": video["videoUrl"],
                        "title": video["youtubeTitle"],
                        "thumbnailUrl": video["thumbnailUrl"],
                        "playlistId": playlist_id,
                        "playlistTitle": playlist_detail["playlistTitle"],
                        "lessonNumber": format_lesson_number(video["lessonNumber"]),
                        "moduleIndex": video["lessonNumber"][0]
                        if video["lessonNumber"]
                        else None,
                        "lectureIndex": video["lessonNumber"][1]
                        if video["lessonNumber"]
                        else None,
                        "durationText": video["durationText"],
                    },
                    "match": {
                        "status": "matched",
                        "method": match_record["method"],
                        "titleSimilarity": title_similarity(
                            lecture.title, video["youtubeLessonTitle"]
                        ),
                    },
                }

            if unmatched_lectures:
                course_discrepancies.append(
                    f"{len(unmatched_lectures)} legacy lecture(s) still have no direct "
                    f"YouTube match inside the mapped playlist as of {snapshot_date}."
                )

            for unmatched_lecture in unmatched_lectures:
                candidate_videos = missing_lecture_candidates(
                    unmatched_lecture.title,
                    all_playlist_videos,
                    assigned_video_ids,
                    playlist_id,
                )
                missing_lectures.append(
                    {
                        "moduleIndex": unmatched_lecture.module_index,
                        "moduleTitle": unmatched_lecture.module_title,
                        "legacyLectureIndex": unmatched_lecture.lecture_index,
                        "positionInModule": unmatched_lecture.position_in_module,
                        "title": unmatched_lecture.title,
                        "candidateVideos": candidate_videos,
                    }
                )

                lecture_lookup[
                    (unmatched_lecture.module_index, unmatched_lecture.position_in_module)
                ] = {
                    "legacyIndex": unmatched_lecture.lecture_index,
                    "positionInModule": unmatched_lecture.position_in_module,
                    "title": unmatched_lecture.title,
                    "contentType": unmatched_lecture.content_type,
                    "videoSource": unmatched_lecture.video_source,
                    "legacyYoutubeUrl": unmatched_lecture.youtube_url,
                    "muxAssetId": unmatched_lecture.mux_asset_id,
                    "muxPlaybackIdPublic": unmatched_lecture.mux_playback_id_public,
                    "muxPlaybackIdSigned": unmatched_lecture.mux_playback_id_signed,
                    "youtube": None,
                    "match": {
                        "status": "missing",
                        "method": None,
                        "titleSimilarity": None,
                    },
                }

            if legacy_index_corrections:
                course_discrepancies.append(
                    f"{len(legacy_index_corrections)} lecture(s) used within-module order "
                    "fallback because the legacy lecture index and YouTube lesson number "
                    "do not line up cleanly."
                )

            playlist_candidates = []
            mapping_status = (
                "playlist_missing_lectures" if missing_lectures else "playlist_exact_match"
            )
        else:
            playlist_candidates = playlist_overlap_candidates(
                direct_video_ids=direct_video_ids,
                channel_playlists=channel_playlists,
                playlist_details=playlist_details,
                excluded_playlist_ids=mapped_playlist_ids,
            )
            mapping_status = "video_only_no_exact_playlist"
            course_discrepancies.append(
                f"No exact public playlist was found on the channel playlists tab as of {snapshot_date}."
            )
            if playlist_candidates:
                course_discrepancies.append(
                    "The course overlaps one or more broader public playlists, but none "
                    "of them are a 1:1 legacy-course match."
                )

            for lecture in legacy_lectures:
                video_id = video_id_from_url(lecture.youtube_url)
                current_video_meta = None
                if video_id:
                    assigned_video_ids.add(video_id)
                    if video_id not in direct_video_meta_cache:
                        direct_video_meta_cache[video_id] = fetch_oembed(video_id)
                    current_video_meta = direct_video_meta_cache[video_id]

                lecture_lookup[(lecture.module_index, lecture.position_in_module)] = (
                    build_video_only_entry(lecture, current_video_meta)
                )

        modules = build_modules_for_course(course, lecture_lookup)
        legacy_lecture_count = sum(len(module["lectures"]) for module in course["modules"])

        course_records.append(
            {
                "courseTag": course_tag,
                "slug": slugify(course_info["title1"]),
                "title": course_info["title1"].strip(),
                "subtitle": course_info.get("title2", "").strip(),
                "description": course_info.get("description", "").strip(),
                "courseImage": course_info.get("course_image", ""),
                "legacy": {
                    "moduleCount": len(course["modules"]),
                    "lectureCount": legacy_lecture_count,
                },
                "youtube": {
                    "channelHandle": YOUTUBE_CHANNEL_HANDLE,
                    "playlistId": playlist_id,
                    "playlistUrl": playlist_detail["playlistUrl"] if playlist_detail else None,
                    "playlistTitle": playlist_detail["playlistTitle"]
                    if playlist_detail
                    else None,
                    "playlistVideoCount": playlist_detail["playlistVideoCount"]
                    if playlist_detail
                    else None,
                    "mappingStatus": mapping_status,
                    "mappedLectureCount": legacy_lecture_count - len(missing_lectures),
                    "missingLectureCount": len(missing_lectures),
                    "playlistCandidates": playlist_candidates,
                },
                "audit": {
                    "lectureMatchMethods": dict(lecture_match_methods),
                    "legacyIndexCorrections": legacy_index_corrections,
                    "missingLectures": missing_lectures,
                    "discrepancies": course_discrepancies,
                },
                "modules": modules,
            }
        )

    exact_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] == "playlist_exact_match"
    )
    partial_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] == "playlist_missing_lectures"
    )
    no_exact_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] == "video_only_no_exact_playlist"
    )
    missing_lecture_count = sum(
        course["youtube"]["missingLectureCount"] for course in course_records
    )
    total_lecture_count = sum(
        course["legacy"]["lectureCount"] for course in course_records
    )
    mapped_lecture_count = total_lecture_count - missing_lecture_count
    unmapped_channel_playlists = [
        {
            "playlistId": playlist_id,
            "playlistTitle": playlist["playlistTitle"],
            "playlistUrl": playlist["playlistUrl"],
            "playlistVideoCount": playlist_details[playlist_id]["playlistVideoCount"],
        }
        for playlist_id, playlist in sorted(channel_playlists.items())
        if playlist_id not in mapped_playlist_ids
    ]

    dataset = {
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "snapshotDate": snapshot_date,
        "source": {
            "legacyCourseFile": str(legacy_file),
            "youtubeChannel": {
                "handle": YOUTUBE_CHANNEL_HANDLE,
                "channelUrl": YOUTUBE_CHANNEL_URL,
                "playlistIndexUrl": YOUTUBE_PLAYLISTS_URL,
                "playlistCountDiscovered": len(channel_playlists),
            },
        },
        "summary": {
            "legacyCourseCount": len(course_records),
            "legacyModuleCount": sum(course["legacy"]["moduleCount"] for course in course_records),
            "legacyLectureCount": total_lecture_count,
            "mappedLectureCount": mapped_lecture_count,
            "missingLectureCount": missing_lecture_count,
            "exactPlaylistCourseCount": exact_playlist_courses,
            "playlistWithMissingLectureCourseCount": partial_playlist_courses,
            "noExactPlaylistCourseCount": no_exact_playlist_courses,
            "unmappedChannelPlaylistCount": len(unmapped_channel_playlists),
        },
        "unmappedChannelPlaylists": unmapped_channel_playlists,
        "courses": course_records,
    }

    report = build_audit_report(dataset)
    return dataset, report


def build_audit_report(dataset: dict[str, Any]) -> str:
    snapshot_date = dataset["snapshotDate"]
    summary = dataset["summary"]
    courses = dataset["courses"]

    missing_playlist_courses = [
        course
        for course in courses
        if course["youtube"]["mappingStatus"] == "video_only_no_exact_playlist"
    ]
    missing_lecture_courses = [
        course
        for course in courses
        if course["youtube"]["missingLectureCount"] > 0
    ]
    index_correction_courses = [
        course
        for course in courses
        if course["audit"]["legacyIndexCorrections"]
    ]

    lines = [
        "# Course Dataset Audit",
        "",
        f"Snapshot date: `{snapshot_date}`",
        "",
        "## Summary",
        "",
        f"- Legacy courses: `{summary['legacyCourseCount']}`",
        f"- Legacy modules: `{summary['legacyModuleCount']}`",
        f"- Legacy lectures: `{summary['legacyLectureCount']}`",
        f"- Mapped lectures: `{summary['mappedLectureCount']}`",
        f"- Missing lectures: `{summary['missingLectureCount']}`",
        f"- Exact course-playlist matches: `{summary['exactPlaylistCourseCount']}`",
        f"- Playlists with missing lecture(s): `{summary['playlistWithMissingLectureCourseCount']}`",
        f"- Courses without an exact public playlist: `{summary['noExactPlaylistCourseCount']}`",
        f"- Extra public channel playlists not mapped 1:1: `{summary['unmappedChannelPlaylistCount']}`",
        "",
    ]

    lines.extend(["## Courses Without Exact Public Playlists", ""])
    if missing_playlist_courses:
        for course in missing_playlist_courses:
            lines.append(
                f"- `{course['courseTag']}`: {course['title']}"
            )
            for discrepancy in course["audit"]["discrepancies"]:
                lines.append(f"  {discrepancy}")
            for candidate in course["youtube"]["playlistCandidates"][:3]:
                lines.append(
                    f"  Candidate playlist: `{candidate['playlistTitle']}` "
                    f"(`{candidate['overlapCount']}` overlapping video IDs)"
                )
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Missing Lectures From Mapped Playlists", ""])
    if missing_lecture_courses:
        for course in missing_lecture_courses:
            lines.append(f"- `{course['courseTag']}`: {course['title']}")
            for missing in course["audit"]["missingLectures"]:
                lines.append(
                    f"  Missing lecture: `L{missing['moduleIndex']}.{missing['legacyLectureIndex']}` "
                    f"{missing['title']}"
                )
                for candidate in missing["candidateVideos"][:2]:
                    lines.append(
                        f"  Candidate public video: `{candidate['title']}` "
                        f"from `{candidate['playlistTitle']}`"
                    )
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Legacy Index Corrections", ""])
    if index_correction_courses:
        for course in index_correction_courses:
            lines.append(f"- `{course['courseTag']}`: {course['title']}")
            for correction in course["audit"]["legacyIndexCorrections"]:
                lines.append(
                    f"  `{correction['moduleTitle']}` / `{correction['legacyLectureTitle']}` "
                    f"used module-order fallback to `{correction['youtubeLessonNumber']}`"
                )
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Unmapped Channel Playlists", ""])
    for playlist in dataset["unmappedChannelPlaylists"]:
        lines.append(
            f"- `{playlist['playlistTitle']}` ({playlist['playlistVideoCount']} videos)"
        )
    lines.append("")

    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    legacy_file = Path(args.legacy_file).expanduser().resolve()
    output_json = Path(args.output_json)
    report_output = Path(args.report_output)

    legacy_courses = load_legacy_courses(legacy_file)
    channel_playlists = extract_channel_playlists()
    playlist_details = {
        playlist_id: extract_playlist_detail(playlist_id)
        for playlist_id in channel_playlists
    }

    dataset, report = generate_dataset(
        legacy_courses=legacy_courses,
        channel_playlists=channel_playlists,
        playlist_details=playlist_details,
        snapshot_date=args.snapshot_date,
        legacy_file=legacy_file,
    )

    write_text(output_json, json.dumps(dataset, indent=2) + "\n")
    write_text(report_output, report)

    print(f"Wrote dataset to {output_json}")
    print(f"Wrote audit report to {report_output}")


if __name__ == "__main__":
    main()
