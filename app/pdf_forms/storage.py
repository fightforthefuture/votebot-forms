import os
import tempfile
from boto.s3.connection import S3Connection
from boto.s3.key import Key

S3_CONNECTION = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                             os.environ.get('AWS_SECRET_KEY'))
BUCKET_NAME = 'hellovote'


def write_to_tmp(file_stream):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(file_stream)
    tmp.close()
    return tmp.name


def upload_to_s3(file_stream, filename):
    bucket = S3_CONNECTION.get_bucket(BUCKET_NAME)
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_string(file_stream)

    return sign_s3_url(bucket.name, filename, force_download=True)


def sign_s3_url(bucket, key, seconds_available=60 * 60 * 24 * 7, force_download=True):
    # seconds_available defaults to 7 days

    if force_download:
        headers = {'response-content-disposition': 'attachment;'}

    access_url = S3_CONNECTION.generate_url(seconds_available, 'GET', bucket, key,
        response_headers=headers or None)

    return access_url
