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
