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
    "C101_Basic01": "PL7q7nkSfmotuZNz8q_dTqhXY1-rZmIRfP",
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

LEGACY_PLAYLIST_OVERRIDES = {
    "C101_Basic01": {
        "title": "Systemverilog for Absolute Beginner",
        "description": (
            "Beginner-friendly SystemVerilog starter playlist covering the first "
            "program, introductory testbench work, essential data types, and "
            "basic VLSI context."
        ),
        "moduleTitle": "Systemverilog for Absolute Beginner",
        "buildMode": "playlist_only",
        "auditNote": (
            "Legacy single-video course intentionally replaced with the public "
            "`Systemverilog for Absolute Beginner` playlist."
        ),
    }
}

PLAYLIST_ONLY_COURSES = [
    {
        "courseTag": "YT_ASSERTIONS_PLAYLIST",
        "title": "Systemverilog Assertions",
        "subtitle": "",
        "description": (
            "Short public assertions starter playlist collected from the academy "
            "channel."
        ),
        "courseImage": "",
        "playlistId": "PL7q7nkSfmotsyJxfvQFMyUvjKzOTS47aN",
        "moduleTitle": "Systemverilog Assertions",
    },
    {
        "courseTag": "YT_UVM_BEGINNER_PLAYLIST",
        "title": "UVM Beginner",
        "subtitle": "",
        "description": (
            "Short public UVM starter playlist with beginner-oriented overview "
            "videos and reusable-agent previews."
        ),
        "courseImage": "",
        "playlistId": "PL7q7nkSfmotv_LRRB2fL2LX2DUtn9cztJ",
        "moduleTitle": "UVM Beginner",
    },
]

SUPPLEMENTAL_PLAYLIST_IDS = {
    "PL7q7nkSfmotuZV2_QhFY28lHARsXPEtKf",
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
        "--mirror-report-output",
        default="scripts/youtube_sync/course-dataset-audit.md",
        help="Optional second path for writing the same markdown audit report.",
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


def clean_course_title(title: str) -> str:
    title = re.sub(r"^(paid|free)\s+course\s*:\s*", "", title, flags=re.IGNORECASE)
    return title.strip()


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

    cleaned = re.sub(
        r"^\s*course\s*:\s*[^:]+:\s*",
        "",
        cleaned,
        count=1,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"^\s*(paid|free)\s+course\s*:\s*",
        "",
        cleaned,
        count=1,
        flags=re.IGNORECASE,
    )

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


def build_playlist_course_lecture(
    *,
    video: dict[str, Any],
    module_index: int,
    position_in_module: int,
) -> dict[str, Any]:
    lesson_number = video.get("lessonNumber")
    legacy_index = lesson_number[1] if lesson_number else position_in_module
    title = video["youtubeLessonTitle"] or video["youtubeTitle"]

    return {
        "legacyIndex": legacy_index,
        "positionInModule": position_in_module,
        "title": title,
        "contentType": "VID",
        "videoSource": "YOUTUBE",
        "legacyYoutubeUrl": "",
        "muxAssetId": "",
        "muxPlaybackIdPublic": "",
        "muxPlaybackIdSigned": "",
        "youtube": {
            "videoId": video["videoId"],
            "videoUrl": video["videoUrl"],
            "title": video["youtubeTitle"],
            "thumbnailUrl": video["thumbnailUrl"],
            "playlistId": video["playlistId"],
            "playlistTitle": video["playlistTitle"],
            "lessonNumber": format_lesson_number(lesson_number),
            "moduleIndex": lesson_number[0] if lesson_number else module_index,
            "lectureIndex": lesson_number[1] if lesson_number else position_in_module,
            "durationText": video["durationText"],
        },
        "match": {
            "status": "matched",
            "method": "playlist_only",
            "titleSimilarity": 1.0,
        },
    }


def build_playlist_only_modules(
    *,
    playlist_detail: dict[str, Any],
    module_title: str,
) -> list[dict[str, Any]]:
    return [
        {
            "index": 1,
            "title": module_title,
            "lectures": [
                build_playlist_course_lecture(
                    video=video,
                    module_index=1,
                    position_in_module=position,
                )
                for position, video in enumerate(playlist_detail["videos"], start=1)
            ],
        }
    ]


def build_course_record(
    *,
    course_tag: str,
    title: str,
    subtitle: str,
    description: str,
    course_image: str,
    modules: list[dict[str, Any]],
    youtube_payload: dict[str, Any],
    audit_payload: dict[str, Any],
    source_kind: str,
    legacy_module_count: int,
    legacy_lecture_count: int,
) -> dict[str, Any]:
    catalog_module_count = len(modules)
    catalog_lecture_count = sum(len(module["lectures"]) for module in modules)

    return {
        "courseTag": course_tag,
        "slug": slugify(title),
        "title": title.strip(),
        "subtitle": subtitle.strip(),
        "description": description.strip(),
        "courseImage": course_image,
        "source": {
            "kind": source_kind,
        },
        "legacy": {
            "moduleCount": legacy_module_count,
            "lectureCount": legacy_lecture_count,
        },
        "catalog": {
            "moduleCount": catalog_module_count,
            "lectureCount": catalog_lecture_count,
        },
        "youtube": youtube_payload,
        "audit": audit_payload,
        "modules": modules,
    }


def build_mux_payload(
    *,
    asset_id: str,
    playback_id_public: str,
    playback_id_signed: str,
) -> dict[str, Any] | None:
    if not any([asset_id, playback_id_public, playback_id_signed]):
        return None

    return {
        "assetId": asset_id or None,
        "playbackIdPublic": playback_id_public or None,
        "playbackIdSigned": playback_id_signed or None,
    }


def build_youtube_payload(youtube: dict[str, Any] | None) -> dict[str, Any] | None:
    if not youtube:
        return None

    return {
        "videoId": youtube.get("videoId"),
        "url": youtube.get("videoUrl"),
        "title": youtube.get("title"),
        "thumbnailUrl": youtube.get("thumbnailUrl"),
        "playlistId": youtube.get("playlistId"),
        "playlistTitle": clean_course_title(youtube.get("playlistTitle"))
        if youtube.get("playlistTitle")
        else None,
        "lessonNumber": youtube.get("lessonNumber"),
        "moduleIndex": youtube.get("moduleIndex"),
        "lessonIndex": youtube.get("lectureIndex"),
        "durationText": youtube.get("durationText"),
    }


def transform_lesson_record(lecture: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": lecture["positionInModule"],
        "title": lecture["title"],
        "kind": "video" if lecture.get("contentType") == "VID" else lecture.get("contentType"),
        "youtube": build_youtube_payload(lecture.get("youtube")),
        "mux": build_mux_payload(
            asset_id=lecture.get("muxAssetId", ""),
            playback_id_public=lecture.get("muxPlaybackIdPublic", ""),
            playback_id_signed=lecture.get("muxPlaybackIdSigned", ""),
        ),
        "metadata": {
            "legacy": {
                "lectureIndex": lecture.get("legacyIndex"),
                "youtubeUrl": lecture.get("legacyYoutubeUrl") or None,
                "contentType": lecture.get("contentType") or None,
                "videoSource": lecture.get("videoSource") or None,
            },
            "sync": {
                "status": lecture["match"].get("status"),
                "method": lecture["match"].get("method"),
                "titleSimilarity": lecture["match"].get("titleSimilarity"),
            },
        },
    }


def transform_module_record(module: dict[str, Any]) -> dict[str, Any]:
    lessons = [transform_lesson_record(lecture) for lecture in module["lectures"]]
    return {
        "index": module["index"],
        "slug": slugify(module["title"]),
        "title": module["title"],
        "lessonCount": len(lessons),
        "lessons": lessons,
    }


def transform_course_record(course: dict[str, Any]) -> dict[str, Any]:
    modules = [transform_module_record(module) for module in course["modules"]]

    return {
        "id": course["courseTag"],
        "slug": course["slug"],
        "title": course["title"],
        "subtitle": course["subtitle"],
        "description": course["description"],
        "image": course["courseImage"],
        "counts": {
            "modules": course["catalog"]["moduleCount"],
            "lessons": course["catalog"]["lectureCount"],
        },
        "youtube": {
            "channelHandle": course["youtube"]["channelHandle"],
            "playlistId": course["youtube"]["playlistId"],
            "playlistUrl": course["youtube"]["playlistUrl"],
            "playlistTitle": clean_course_title(course["youtube"]["playlistTitle"])
            if course["youtube"]["playlistTitle"]
            else None,
            "playlistVideoCount": course["youtube"]["playlistVideoCount"],
        },
        "modules": modules,
        "metadata": {
            "source": {
                **course["source"],
                "legacyTag": course["courseTag"],
                "legacyCounts": {
                    "modules": course["legacy"]["moduleCount"],
                    "lessons": course["legacy"]["lectureCount"],
                },
            },
            "sync": {
                "mappingStatus": course["youtube"]["mappingStatus"],
                "mappedLessonCount": course["youtube"]["mappedLectureCount"],
                "missingLessonCount": course["youtube"]["missingLectureCount"],
                "playlistCandidates": course["youtube"]["playlistCandidates"],
                "indexCorrections": course["audit"]["legacyIndexCorrections"],
                "missingLessons": course["audit"]["missingLectures"],
                "discrepancies": course["audit"]["discrepancies"],
            },
        },
    }


def transform_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "legacySourceCourseCount": summary["legacySourceCourseCount"],
        "legacySourceModuleCount": summary["legacySourceModuleCount"],
        "legacySourceLessonCount": summary["legacySourceLectureCount"],
        "catalogCourseCount": summary["catalogCourseCount"],
        "catalogModuleCount": summary["catalogModuleCount"],
        "catalogLessonCount": summary["catalogLectureCount"],
        "mappedLessonCount": summary["mappedLectureCount"],
        "missingLessonCount": summary["missingLectureCount"],
        "exactPlaylistCourseCount": summary["exactPlaylistCourseCount"],
        "playlistWithMissingLessonCourseCount": summary[
            "playlistWithMissingLectureCourseCount"
        ],
        "noExactPlaylistCourseCount": summary["noExactPlaylistCourseCount"],
        "unmappedChannelPlaylistCount": summary["unmappedChannelPlaylistCount"],
        "supplementalChannelPlaylistCount": summary[
            "supplementalChannelPlaylistCount"
        ],
    }


def transform_playlist_list(playlists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": playlist["playlistId"],
            "title": clean_course_title(playlist["playlistTitle"]),
            "url": playlist["playlistUrl"],
            "videoCount": playlist["playlistVideoCount"],
        }
        for playlist in playlists
    ]


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
    source_legacy_course_count = len(legacy_courses)
    source_legacy_module_count = sum(len(course["modules"]) for course in legacy_courses)
    source_legacy_lecture_count = sum(
        sum(len(module["lectures"]) for module in course["modules"])
        for course in legacy_courses
    )

    for course in legacy_courses:
        course_info = course["course_info"]
        course_tag = course_info["course_tag"]
        legacy_lectures = flatten_legacy_lectures(course)
        lecture_lookup: dict[tuple[int, int], dict[str, Any]] = {}

        playlist_id = MANUAL_PLAYLIST_MAP.get(course_tag)
        playlist_detail = playlist_details.get(playlist_id) if playlist_id else None
        playlist_override = LEGACY_PLAYLIST_OVERRIDES.get(course_tag)
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
        legacy_module_count = len(course["modules"])
        legacy_lecture_count = sum(len(module["lectures"]) for module in course["modules"])

        if playlist_detail and playlist_override and playlist_override["buildMode"] == "playlist_only":
            for video in playlist_detail["videos"]:
                assigned_video_ids.add(video["videoId"])

            modules = build_playlist_only_modules(
                playlist_detail=playlist_detail,
                module_title=playlist_override["moduleTitle"],
            )
            course_discrepancies.append(playlist_override["auditNote"])

            course_records.append(
                build_course_record(
                    course_tag=course_tag,
                    title=playlist_override["title"],
                    subtitle=course_info.get("title2", ""),
                    description=playlist_override["description"],
                    course_image=course_info.get("course_image", ""),
                    modules=modules,
                    source_kind="legacy_playlist_override",
                    legacy_module_count=legacy_module_count,
                    legacy_lecture_count=legacy_lecture_count,
                    youtube_payload={
                        "channelHandle": YOUTUBE_CHANNEL_HANDLE,
                        "playlistId": playlist_id,
                        "playlistUrl": playlist_detail["playlistUrl"],
                        "playlistTitle": playlist_detail["playlistTitle"],
                        "playlistVideoCount": playlist_detail["playlistVideoCount"],
                        "mappingStatus": "playlist_only_override",
                        "mappedLectureCount": playlist_detail["playlistVideoCount"],
                        "missingLectureCount": 0,
                        "playlistCandidates": [],
                    },
                    audit_payload={
                        "lectureMatchMethods": {"playlist_only": playlist_detail["playlistVideoCount"]},
                        "legacyIndexCorrections": [],
                        "missingLectures": [],
                        "discrepancies": course_discrepancies,
                    },
                )
            )
            continue

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
            source_kind = "legacy_course"
        else:
            playlist_candidates = playlist_overlap_candidates(
                direct_video_ids=direct_video_ids,
                channel_playlists=channel_playlists,
                playlist_details=playlist_details,
                excluded_playlist_ids=mapped_playlist_ids | SUPPLEMENTAL_PLAYLIST_IDS,
            )
            if len(direct_video_ids) <= 1:
                mapping_status = "standalone_video_course"
                course_discrepancies.append(
                    f"No public playlist currently lists this course on the channel playlists tab as of {snapshot_date}."
                )
                course_discrepancies.append(
                    "The course is retained as a standalone public video because the video is still live and relevant."
                )
            else:
                mapping_status = "curated_video_collection"
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
            source_kind = "legacy_video_only"

        modules = build_modules_for_course(course, lecture_lookup)
        course_title = playlist_override["title"] if playlist_override else course_info["title1"]
        course_description = (
            playlist_override["description"]
            if playlist_override and playlist_override.get("description")
            else course_info.get("description", "")
        )

        course_records.append(
            build_course_record(
                course_tag=course_tag,
                title=course_title,
                subtitle=course_info.get("title2", ""),
                description=course_description,
                course_image=course_info.get("course_image", ""),
                modules=modules,
                source_kind=source_kind,
                legacy_module_count=legacy_module_count,
                legacy_lecture_count=legacy_lecture_count,
                youtube_payload={
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
                    "mappedLectureCount": sum(len(module["lectures"]) for module in modules)
                    - len(missing_lectures),
                    "missingLectureCount": len(missing_lectures),
                    "playlistCandidates": playlist_candidates,
                },
                audit_payload={
                    "lectureMatchMethods": dict(lecture_match_methods),
                    "legacyIndexCorrections": legacy_index_corrections,
                    "missingLectures": missing_lectures,
                    "discrepancies": course_discrepancies,
                },
            )
        )

    for playlist_course in PLAYLIST_ONLY_COURSES:
        playlist_id = playlist_course["playlistId"]
        playlist_detail = playlist_details[playlist_id]
        for video in playlist_detail["videos"]:
            assigned_video_ids.add(video["videoId"])

        modules = build_playlist_only_modules(
            playlist_detail=playlist_detail,
            module_title=playlist_course["moduleTitle"],
        )
        course_records.append(
            build_course_record(
                course_tag=playlist_course["courseTag"],
                title=playlist_course["title"],
                subtitle=playlist_course["subtitle"],
                description=playlist_course["description"],
                course_image=playlist_course["courseImage"],
                modules=modules,
                source_kind="youtube_playlist_only",
                legacy_module_count=0,
                legacy_lecture_count=0,
                youtube_payload={
                    "channelHandle": YOUTUBE_CHANNEL_HANDLE,
                    "playlistId": playlist_id,
                    "playlistUrl": playlist_detail["playlistUrl"],
                    "playlistTitle": playlist_detail["playlistTitle"],
                    "playlistVideoCount": playlist_detail["playlistVideoCount"],
                    "mappingStatus": "playlist_only_public_course",
                    "mappedLectureCount": playlist_detail["playlistVideoCount"],
                    "missingLectureCount": 0,
                    "playlistCandidates": [],
                },
                audit_payload={
                    "lectureMatchMethods": {"playlist_only": playlist_detail["playlistVideoCount"]},
                    "legacyIndexCorrections": [],
                    "missingLectures": [],
                    "discrepancies": [],
                },
            )
        )

    exact_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] in {"playlist_exact_match", "playlist_only_public_course", "playlist_only_override"}
    )
    partial_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] == "playlist_missing_lectures"
    )
    no_exact_playlist_courses = sum(
        1
        for course in course_records
        if course["youtube"]["mappingStatus"] in {"standalone_video_course", "curated_video_collection"}
    )
    missing_lecture_count = sum(
        course["youtube"]["missingLectureCount"] for course in course_records
    )
    catalog_lecture_count = sum(
        course["catalog"]["lectureCount"] for course in course_records
    )
    catalog_module_count = sum(
        course["catalog"]["moduleCount"] for course in course_records
    )
    mapped_lecture_count = catalog_lecture_count - missing_lecture_count
    supplemental_channel_playlists = [
        {
            "playlistId": playlist_id,
            "playlistTitle": channel_playlists[playlist_id]["playlistTitle"],
            "playlistUrl": channel_playlists[playlist_id]["playlistUrl"],
            "playlistVideoCount": playlist_details[playlist_id]["playlistVideoCount"],
        }
        for playlist_id in sorted(SUPPLEMENTAL_PLAYLIST_IDS)
        if playlist_id in channel_playlists
    ]
    unmapped_channel_playlists = [
        {
            "playlistId": playlist_id,
            "playlistTitle": playlist["playlistTitle"],
            "playlistUrl": playlist["playlistUrl"],
            "playlistVideoCount": playlist_details[playlist_id]["playlistVideoCount"],
        }
        for playlist_id, playlist in sorted(channel_playlists.items())
        if playlist_id not in mapped_playlist_ids
        and playlist_id not in SUPPLEMENTAL_PLAYLIST_IDS
        and playlist_id
        not in {course["youtube"]["playlistId"] for course in course_records if course["youtube"]["playlistId"]}
    ]

    summary = {
        "legacySourceCourseCount": source_legacy_course_count,
        "legacySourceModuleCount": source_legacy_module_count,
        "legacySourceLectureCount": source_legacy_lecture_count,
        "catalogCourseCount": len(course_records),
        "catalogModuleCount": catalog_module_count,
        "catalogLectureCount": catalog_lecture_count,
        "mappedLectureCount": mapped_lecture_count,
        "missingLectureCount": missing_lecture_count,
        "exactPlaylistCourseCount": exact_playlist_courses,
        "playlistWithMissingLectureCourseCount": partial_playlist_courses,
        "noExactPlaylistCourseCount": no_exact_playlist_courses,
        "unmappedChannelPlaylistCount": len(unmapped_channel_playlists),
        "supplementalChannelPlaylistCount": len(supplemental_channel_playlists),
    }

    dataset = {
        "metadata": {
            "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "snapshotDate": snapshot_date,
            "generator": {
                "script": "scripts/youtube_sync/generate_course_dataset.py",
            },
            "source": {
                "legacyCourseFile": str(legacy_file),
                "youtubeChannel": {
                    "handle": YOUTUBE_CHANNEL_HANDLE,
                    "channelUrl": YOUTUBE_CHANNEL_URL,
                    "playlistIndexUrl": YOUTUBE_PLAYLISTS_URL,
                    "playlistCountDiscovered": len(channel_playlists),
                },
            },
            "summary": transform_summary(summary),
            "supplementalPlaylists": transform_playlist_list(supplemental_channel_playlists),
            "unmappedPlaylists": transform_playlist_list(unmapped_channel_playlists),
        },
        "courses": [transform_course_record(course) for course in course_records],
    }

    report = build_audit_report(
        {
            "snapshotDate": snapshot_date,
            "summary": summary,
            "supplementalChannelPlaylists": supplemental_channel_playlists,
            "unmappedChannelPlaylists": unmapped_channel_playlists,
            "courses": course_records,
        }
    )
    return dataset, report


def build_audit_report(dataset: dict[str, Any]) -> str:
    snapshot_date = dataset["snapshotDate"]
    summary = dataset["summary"]
    courses = dataset["courses"]

    missing_playlist_courses = [
        course
        for course in courses
        if course["youtube"]["mappingStatus"] in {"standalone_video_course", "curated_video_collection"}
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
        f"- Legacy source courses: `{summary['legacySourceCourseCount']}`",
        f"- Legacy source modules: `{summary['legacySourceModuleCount']}`",
        f"- Legacy source lectures: `{summary['legacySourceLectureCount']}`",
        f"- Catalog courses: `{summary['catalogCourseCount']}`",
        f"- Catalog modules: `{summary['catalogModuleCount']}`",
        f"- Catalog lectures: `{summary['catalogLectureCount']}`",
        f"- Mapped lectures: `{summary['mappedLectureCount']}`",
        f"- Missing lectures: `{summary['missingLectureCount']}`",
        f"- Exact course-playlist matches: `{summary['exactPlaylistCourseCount']}`",
        f"- Playlists with missing lecture(s): `{summary['playlistWithMissingLectureCourseCount']}`",
        f"- Courses without an exact public playlist: `{summary['noExactPlaylistCourseCount']}`",
        f"- Extra public channel playlists not mapped 1:1: `{summary['unmappedChannelPlaylistCount']}`",
        f"- Supplemental channel playlists intentionally not modeled as courses: `{summary['supplementalChannelPlaylistCount']}`",
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

    lines.extend(["## Playlist-Only Public Courses", ""])
    playlist_only_courses = [
        course
        for course in courses
        if course["youtube"]["mappingStatus"] in {"playlist_only_public_course", "playlist_only_override"}
    ]
    if playlist_only_courses:
        for course in playlist_only_courses:
            lines.append(f"- `{course['courseTag']}`: {course['title']}")
            lines.append(
                f"  Playlist: `{course['youtube']['playlistTitle']}` "
                f"({course['youtube']['playlistVideoCount']} videos)"
            )
            for discrepancy in course["audit"]["discrepancies"]:
                lines.append(f"  {discrepancy}")
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

    lines.extend(["## Supplemental Channel Playlists", ""])
    supplemental_channel_playlists = dataset.get("supplementalChannelPlaylists", [])
    if supplemental_channel_playlists:
        for playlist in supplemental_channel_playlists:
            lines.append(
                f"- `{playlist['playlistTitle']}` ({playlist['playlistVideoCount']} videos)"
            )
    else:
        lines.append("- None")
    lines.append("")

    lines.extend(["## Unmapped Channel Playlists", ""])
    if dataset["unmappedChannelPlaylists"]:
        for playlist in dataset["unmappedChannelPlaylists"]:
            lines.append(
                f"- `{playlist['playlistTitle']}` ({playlist['playlistVideoCount']} videos)"
            )
    else:
        lines.append("- None")
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
    mirror_report_output = (
        Path(args.mirror_report_output) if args.mirror_report_output else None
    )

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
    if mirror_report_output and mirror_report_output != report_output:
        write_text(mirror_report_output, report)

    print(f"Wrote dataset to {output_json}")
    print(f"Wrote audit report to {report_output}")
    if mirror_report_output and mirror_report_output != report_output:
        print(f"Wrote audit report mirror to {mirror_report_output}")


if __name__ == "__main__":
    main()
