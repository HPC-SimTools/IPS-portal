import json
import logging
import os
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import MinioException
from urllib3.exceptions import MaxRetryError
from urllib3.util import parse_url

logger = logging.getLogger(__name__)

# NOTE: you need to explicitly include the URL scheme here
MINIO_PRIVATE_URL = os.environ.get("MINIO_PRIVATE_URL", "http://localhost:9000")
"""
This is the URL the backend uses. It must NOT contain a path in the URI.
"""
MINIO_URI = parse_url(MINIO_PRIVATE_URL)
MINIO_PUBLIC_URL = os.environ.get("MINIO_PUBLIC_URL", MINIO_PRIVATE_URL)
"""
This is the URL we expose directly to end users. Paths are allowed here.
"""

MINIO_CLIENT = Minio(
    secure=(MINIO_URI.scheme == 'https'),
    access_key=os.environ.get("MINIO_ROOT_USER", "AKIAIOSFODNN7EXAMPLE"),
    secret_key=os.environ.get(
        "MINIO_ROOT_PASSWORD", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    ),
    endpoint=(MINIO_URI.host if not MINIO_URI.port else f'{MINIO_URI.host}:{MINIO_URI.port}'),  # type: ignore
)


def get_bucket_policy(bucket_name: str) -> str:
    """
    Generate a bucket policy which allows for anonymous read access of files.

    Params:
      bucket_name: name of MINIO bucket

    Returns:
      the bucket policy, as a JSON string
    """
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                },
            ],
        }
    )


def handle_bucket_init(bucket_name: str) -> None:
    """Create a bucket for the runid if it does not exist."""
    if not MINIO_CLIENT.bucket_exists(bucket_name):
        MINIO_CLIENT.make_bucket(bucket_name)
        MINIO_CLIENT.set_bucket_policy(bucket_name, get_bucket_policy(bucket_name))


def put_minio_object(
    data: bytes, bucket_name: str, object_id: str, content_type: str
) -> Optional[str]:
    """
    Adds the raw data to MINIO.

    Returns path of data file if operation successful (no leading "/"), None if exception was thrown
    """
    try:
        handle_bucket_init(bucket_name)
        buff_data = BytesIO(data)
        put_result = MINIO_CLIENT.put_object(
            bucket_name=bucket_name,
            object_name=object_id,
            data=buff_data,
            length=buff_data.getbuffer().nbytes,
            content_type=content_type,
        )
        return f'{MINIO_PUBLIC_URL}/{put_result.bucket_name}/{put_result.object_name}'
    except MaxRetryError:
        logger.error("Max retry error when trying to add object to MINIO")
        return None
    except MinioException as e:
        logger.error(f"Minio Exception when trying to add object to MINIO: \n{e}")
        return None
