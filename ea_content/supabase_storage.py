from django.conf import settings
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set to use Supabase Storage.")
    return create_client(url, key)


def upload_ebook_pdf(topic_id: int, file_obj) -> str:
    """
    Uploads a PDF file object to the 'ea-ebooks' private bucket.
    Overwrites if exists.
    Returns the storage path e.g., 'topic_14_ebook.pdf'.
    """
    client = get_supabase_client()
    bucket_name = "ea-ebooks"
    
    # Optional: ensure bucket exists (if permissions allow)
    # try:
    #     client.storage.create_bucket(bucket_name, {"public": False})
    # except Exception:
    #     pass # Bucket already exists or insufficient perms to create
        
    file_path = f"topic_{topic_id}_ebook.pdf"
    
    try:
        # file_obj is an In-Memory File or Temporary Uploaded File from Django
        file_bytes = file_obj.read()
        # Overwrite requires upsert=True, but standard client might not expose it directly in python sdk cleanly,
        # so we attempt remove first to be safe
        try:
            client.storage.from_(bucket_name).remove([file_path])
        except Exception:
            pass
            
        res = client.storage.from_(bucket_name).upload(
            file_path, 
            file_bytes, 
            {"content-type": "application/pdf"}
        )
        return file_path
    except Exception as e:
        logger.error(f"Supabase upload failed for topic {topic_id}: {e}")
        raise


def delete_ebook_pdf(storage_path: str) -> bool:
    """Removes the file from the Supabase bucket."""
    if not storage_path:
        return False
        
    client = get_supabase_client()
    bucket_name = "ea-ebooks"
    try:
        client.storage.from_(bucket_name).remove([storage_path])
        return True
    except Exception as e:
        logger.error(f"Supabase delete failed for {storage_path}: {e}")
        return False


def get_ebook_pdf_bytes(storage_path: str) -> bytes:
    """
    Downloads the raw bytes of the PDF file from the private bucket.
    Used to stream the file through Django proxy.
    """
    if not storage_path:
        raise ValueError("No storage path provided.")
        
    client = get_supabase_client()
    bucket_name = "ea-ebooks"
    try:
        # Download file securely using the service key
        response = client.storage.from_(bucket_name).download(storage_path)
        return response
    except Exception as e:
        logger.error(f"Supabase download failed for {storage_path}: {e}")
        raise


# ──────────────────────────────────────────────
# TOPIC RESOURCES (topic-resources private bucket)
# ──────────────────────────────────────────────
# Bucket path structure:
#   topic_resources/{part_number}/{domain_slug}/{topic_id}/{safe_filename}
# Example:
#   topic_resources/1/bookkeeping/42/trial_balance_template.xlsx
# ──────────────────────────────────────────────

RESOURCES_BUCKET = "topic-resources"


def _slugify(text: str) -> str:
    """Simple slug: lowercase, keep alphanumeric and hyphens, replace spaces/underscores with '-'."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w\-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text[:50]  # cap length


def _safe_filename(original: str) -> str:
    """Make a filename safe for storage (no spaces, no special chars)."""
    import re
    import os
    name, ext = os.path.splitext(original)
    name = re.sub(r"[^\w\-]", "_", name).strip("_")
    return f"{name}{ext.lower()}"


def upload_topic_resource(topic, file_obj, title: str) -> tuple:
    """
    Upload a resource file to the private 'topic-resources' Supabase bucket.

    Path: topic_resources/{part_number}/{domain_slug}/{topic_id}/{safe_filename}

    Returns:
        (storage_path: str, file_size_bytes: int)
    """
    import os
    client = get_supabase_client()

    part_number = topic.domain.part.number
    domain_slug = _slugify(topic.domain.name)
    topic_id    = topic.id
    safe_fname  = _safe_filename(file_obj.name)

    storage_path = f"topic_resources/{part_number}/{domain_slug}/{topic_id}/{safe_fname}"

    try:
        file_bytes = file_obj.read()
        file_size  = len(file_bytes)

        # Determine MIME type
        ext = os.path.splitext(file_obj.name)[1].lower()
        mime_map = {
            ".pdf":  "application/pdf",
            ".xls":  "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv":  "text/csv",
            ".ppt":  "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".doc":  "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt":  "text/plain",
            ".md":   "text/markdown",
        }
        content_type = mime_map.get(ext, "application/octet-stream")

        # Remove existing file at this path first (safe overwrite)
        try:
            client.storage.from_(RESOURCES_BUCKET).remove([storage_path])
        except Exception:
            pass

        client.storage.from_(RESOURCES_BUCKET).upload(
            storage_path,
            file_bytes,
            {"content-type": content_type},
        )
        logger.info(f"Uploaded topic resource: {storage_path} ({file_size} bytes)")
        return storage_path, file_size

    except Exception as e:
        logger.error(f"Supabase resource upload failed for topic {topic_id}: {e}")
        raise


def download_topic_resource(storage_path: str) -> bytes:
    """
    Securely download a topic resource file from the private bucket.
    Returns raw bytes — stream through Django proxy, never expose bucket URL.
    """
    if not storage_path:
        raise ValueError("No storage path provided.")

    client = get_supabase_client()
    try:
        response = client.storage.from_(RESOURCES_BUCKET).download(storage_path)
        return response
    except Exception as e:
        logger.error(f"Supabase resource download failed for {storage_path}: {e}")
        raise


def delete_topic_resource(storage_path: str) -> bool:
    """Remove a topic resource file from the Supabase bucket."""
    if not storage_path:
        return False

    client = get_supabase_client()
    try:
        client.storage.from_(RESOURCES_BUCKET).remove([storage_path])
        logger.info(f"Deleted topic resource: {storage_path}")
        return True
    except Exception as e:
        logger.error(f"Supabase resource delete failed for {storage_path}: {e}")
        return False



# ──────────────────────────────────────────────
# PROFILE PICTURE (avatars bucket - public)
# ──────────────────────────────────────────────

AVATAR_BUCKET = "avatars"


def upload_profile_picture(user_id: int, file_obj) -> str:
    """
    Uploads a profile picture to the 'avatars' public bucket.
    Returns the full public URL of the uploaded image.
    """
    import os
    client = get_supabase_client()

    # Determine file extension from the uploaded file name
    ext = os.path.splitext(file_obj.name)[1].lower() if file_obj.name else ".jpg"
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        ext = '.jpg'

    file_path = f"user_{user_id}{ext}"

    # Determine content type
    content_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
    }
    content_type = content_types.get(ext, 'image/jpeg')

    try:
        file_bytes = file_obj.read()

        # Remove old file first (ignore errors if not found)
        try:
            client.storage.from_(AVATAR_BUCKET).remove([file_path])
        except Exception:
            pass

        # Upload new file
        client.storage.from_(AVATAR_BUCKET).upload(
            file_path,
            file_bytes,
            {"content-type": content_type}
        )

        # Build public URL
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{AVATAR_BUCKET}/{file_path}"
        return public_url

    except Exception as e:
        logger.error(f"Supabase avatar upload failed for user {user_id}: {e}")
        raise


def delete_profile_picture(user_id: int) -> bool:
    """Removes the user's profile picture from the avatars bucket."""
    client = get_supabase_client()
    try:
        # Try common extensions
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            try:
                client.storage.from_(AVATAR_BUCKET).remove([f"user_{user_id}{ext}"])
            except Exception:
                pass
        return True
    except Exception as e:
        logger.error(f"Supabase avatar delete failed for user {user_id}: {e}")
        return False
