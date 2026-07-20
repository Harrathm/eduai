"""
Media Service - S3/MinIO presigned URLs
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import MediaAsset


class MediaService:
    """Handle media uploads to S3/MinIO"""
    
    # MIME type whitelist
    ALLOWED_MIME_TYPES = {
        "video": ["video/mp4", "video/webm", "video/quicktime"],
        "image": ["image/png", "image/jpeg", "image/webp", "image/gif"],
        "document": ["application/pdf", "application/msword", 
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   "application/vnd.ms-powerpoint",
                   "application/vnd.openxmlformats-officedocument.presentationml.presentation"],
        "audio": ["audio/mpeg", "audio/wav", "audio/ogg"]
    }
    
    MAX_SIZES = {
        "video": 2 * 1024 * 1024 * 1024,  # 2GB
        "image": 10 * 1024 * 1024,  # 10MB
        "document": 50 * 1024 * 1024,  # 50MB
        "audio": 100 * 1024 * 1024  # 100MB
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.s3_bucket = os.getenv("S3_BUCKET", "eduai-media")
        self.s3_endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        self.s3_access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.s3_secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
    
    def get_mime_category(self, mime_type: str) -> Optional[str]:
        """Get category from MIME type"""
        for category, mimes in self.ALLOWED_MIME_TYPES.items():
            if mime_type in mimes:
                return category
        return None
    
    def validate_upload(self, filename: str, mime_type: str, size_bytes: int) -> dict:
        """Validate upload request"""
        errors = []
        
        category = self.get_mime_category(mime_type)
        if not category:
            errors.append(f"MIME type {mime_type} not allowed")
        
        if category:
            max_size = self.MAX_SIZES.get(category, 0)
            if size_bytes > max_size:
                errors.append(f"File too large. Max {max_size // 1024 // 1024}MB for {category}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def generate_presigned_url(self, owner_id: int, filename: str, mime_type: str, size_bytes: int) -> dict:
        """Generate presigned upload URL"""
        # Validate
        validation = self.validate_upload(filename, mime_type, size_bytes)
        if not validation["valid"]:
            raise ValueError(", ".join(validation["errors"]))
        
        # Generate unique filename
        ext = os.path.splitext(filename)[1]
        unique_name = f"{secrets.token_urlsafe(16)}{ext}"
        key = f"uploads/{owner_id}/{datetime.now(timezone.utc).year}/{datetime.now(timezone.utc).month:02d}/{unique_name}"
        
        # Create DB record
        asset = MediaAsset(
            owner_id=owner_id,
            filename=key,
            original_filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            url=f"{self.s3_endpoint}/{self.s3_bucket}/{key}",
            storage_type="s3" if self.s3_bucket != "local" else "local"
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        
        # Generate presigned URL (would use boto3 in production)
        upload_url = f"{self.s3_endpoint}/{self.s3_bucket}/{key}?presigned"
        
        # For local storage, just return the URL
        if self.s3_bucket == "local":
            return {
                "asset_id": asset.id,
                "upload_url": asset.url,
                "public_url": asset.url,
                "expires": 3600
            }
        
        # For S3, would generate presigned PUT URL
        # In production: use boto3 client
        return {
            "asset_id": asset.id,
            "upload_url": upload_url,
            "public_url": asset.url,
            "expires": 3600
        }
    
    def finalize_upload(self, asset_id: int) -> MediaAsset:
        """Mark upload as complete and extract metadata"""
        asset = self.db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
        if not asset:
            raise ValueError("Asset not found")
        
        # Extract video duration if applicable
        if asset.mime_type.startswith("video/"):
            # Would use ffprobe here in production
            pass
        
        return asset
    
    def get_presigned_download_url(self, asset_id: int, expires: int = 3600) -> str:
        """Get presigned download URL"""
        asset = self.db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
        if not asset:
            raise ValueError("Asset not found")
        
        # Would generate presigned GET URL with boto3
        return asset.url
    
    def delete_asset(self, asset_id: int, user_id: int) -> bool:
        """Delete an asset"""
        asset = self.db.query(MediaAsset).filter(
            MediaAsset.id == asset_id,
            MediaAsset.owner_id == user_id
        ).first()
        
        if not asset:
            raise ValueError("Asset not found or unauthorized")
        
        # Would delete from S3
        self.db.delete(asset)
        self.db.commit()
        
        return True