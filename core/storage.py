"""
Supabase Storage backend for Django.

Used in production (serverless) where the local filesystem is read-only.
Falls back to Django's default FileSystemStorage in DEBUG / local mode.

Bucket: media-files  (create this as a PUBLIC bucket in your Supabase dashboard)
"""

import mimetypes
import os
from datetime import datetime

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseMediaStorage(Storage):
    """
    Stores files in a Supabase Storage bucket.

    Required settings (already in .env):
        SUPABASE_URL         – e.g. https://xxxx.supabase.co
        SUPABASE_SERVICE_KEY – service-role JWT (never expose to clients)

    Optional settings:
        SUPABASE_MEDIA_BUCKET (default: "media-files")
    """

    def __init__(self):
        from supabase import create_client
        from django.core.exceptions import ImproperlyConfigured

        self.bucket = getattr(settings, "SUPABASE_MEDIA_BUCKET", "media-files")
        url = getattr(settings, "SUPABASE_URL", "")
        key = getattr(settings, "SUPABASE_SERVICE_KEY", "")

        if not url or not key:
            raise ImproperlyConfigured(
                "Supabase Storage is not configured! In live production (Vercel serverless), "
                "the local filesystem is read-only. You must set SUPABASE_URL and SUPABASE_SERVICE_KEY "
                "in your Vercel Environment Variables to upload files."
            )

        self.client = create_client(url, key)
        self.storage = self.client.storage.from_(self.bucket)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open(self, name, mode="rb"):
        """Download a file from Supabase and return a File-like object."""
        from django.core.files.base import ContentFile
        data = self.storage.download(name)
        return ContentFile(data, name=name)

    def _save(self, name, content):
        """Upload a file to Supabase Storage and return the stored name."""
        name = name.replace("\\", "/").lstrip("/")
        content.seek(0)
        file_data = content.read()

        mime_type, _ = mimetypes.guess_type(name)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            self.storage.upload(
                path=name,
                file=file_data,
                file_options={"content-type": mime_type, "upsert": "true"},
            )
        except Exception as e:
            try:
                self.client.storage.create_bucket(self.bucket, {"public": True})
                self.storage.upload(
                    path=name,
                    file=file_data,
                    file_options={"content-type": mime_type, "upsert": "true"},
                )
            except Exception as e2:
                import logging
                logging.getLogger(__name__).error(f"SupabaseMediaStorage upload error for {name}: {e2}")
                raise e
        return name

    # ------------------------------------------------------------------
    # Required Storage API
    # ------------------------------------------------------------------

    def delete(self, name):
        try:
            self.storage.remove([name])
        except Exception:
            pass

    def exists(self, name):
        try:
            self.storage.download(name)
            return True
        except Exception:
            return False

    def url(self, name):
        """Return a public URL for the file."""
        return (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{name}"
        )

    def size(self, name):
        data = self.storage.download(name)
        return len(data)

    def listdir(self, path):
        items = self.storage.list(path)
        dirs = [i["name"] for i in items if i.get("id") is None]
        files = [i["name"] for i in items if i.get("id") is not None]
        return dirs, files

    def get_available_name(self, name, max_length=None):
        """
        Always allow overwrites (upsert=true above).
        Keeps the name as-is so upload_to paths remain predictable.
        """
        return name
