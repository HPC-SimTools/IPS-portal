import json
import logging
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import MinioException
from urllib3.exceptions import MaxRetryError

from .environment import MINIO_PUBLIC_URL, MINIO_ROOT_PASSWORD, MINIO_ROOT_USER, MINIO_URI

logger = logging.getLogger(__name__)

MINIO_CLIENT = Minio(
    secure=(MINIO_URI.scheme == 'https'),
    access_key=MINIO_ROOT_USER,  # type: ignore[arg-type]
    secret_key=MINIO_ROOT_PASSWORD,  # type: ignore[arg-type]
    endpoint=(MINIO_URI.host if not MINIO_URI.port else f'{MINIO_URI.host}:{MINIO_URI.port}'),  # type: ignore[arg-type]
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
