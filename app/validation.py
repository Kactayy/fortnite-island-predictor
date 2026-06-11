from io import BytesIO

from PIL import Image

from app.tags import VALID_TAG_NAMES

TITLE_MIN = 3
TITLE_MAX = 120
DESCRIPTION_MIN = 10
DESCRIPTION_MAX = 2000
MAX_THUMBNAIL_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


def validate_title(title: str) -> str | None:
    title = title.strip()
    if len(title) < TITLE_MIN:
        return f"Title must be at least {TITLE_MIN} characters."
    if len(title) > TITLE_MAX:
        return f"Title must be at most {TITLE_MAX} characters."
    return None


def validate_description(description: str) -> str | None:
    description = description.strip()
    if len(description) < DESCRIPTION_MIN:
        return f"Description must be at least {DESCRIPTION_MIN} characters."
    if len(description) > DESCRIPTION_MAX:
        return f"Description must be at most {DESCRIPTION_MAX} characters."
    return None


def validate_tags(tags: str) -> tuple[list[str], str | None]:
    if not tags or not tags.strip():
        return [], None

    parsed = [t.strip().lower() for t in tags.split(",") if t.strip()]
    invalid = [t for t in parsed if t not in VALID_TAG_NAMES]

    if invalid:
        return parsed, (
            f"Unknown tag(s): {', '.join(invalid)}. "
            "Use comma-separated tags from the Fortnite Creative tag list."
        )

    return parsed, None


def validate_has_video(has_video: int) -> str | None:
    if has_video not in (0, 1):
        return "Video flag must be 0 or 1."
    return None


def validate_num_extra_images(num_extra_images: int) -> str | None:
    if num_extra_images < 0 or num_extra_images > 3:
        return "Additional images must be between 0 and 3."
    return None


def validate_thumbnail(
    content: bytes,
    content_type: str | None,
) -> str | None:
    if not content:
        return "Thumbnail image is required."

    if len(content) > MAX_THUMBNAIL_BYTES:
        return "Thumbnail must be 5 MB or smaller."

    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        return "Thumbnail must be a JPEG, PNG, WebP, or GIF image."

    try:
        with Image.open(BytesIO(content)) as img:
            img.verify()
    except Exception:
        return "Thumbnail file is not a valid image."

    return None
