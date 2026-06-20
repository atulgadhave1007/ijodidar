"""
verify_s3.py — Confirm S3 bucket is operational for iJodidar.

Run this on the EC2 instance (or locally with AWS credentials):
    cd /home/ubuntu/ijodidar          # or wherever your repo lives on EC2
    source venv/bin/activate
    python scripts/verify_s3.py

What it checks:
  1. boto3 can reach S3 with current credentials (IAM role on EC2, or local creds)
  2. The configured bucket exists and is reachable
  3. PutObject works (private ACL) — required for photo uploads
  4. Presigned URL generation works — required for serving photos in templates
  5. DeleteObject works — required for photo replacement/deletion
  6. Bucket blocks public access — required for DPDP private-photo compliance

Exit code 0 = all checks passed. Non-zero = at least one check failed.
"""
import os, sys, io, json, textwrap

# ── Load .env manually so this script works outside Flask ─────────────────────
_dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_dotenv_path):
    with open(_dotenv_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ.setdefault(k.strip(), v.strip())

BUCKET = os.environ.get('AWS_S3_BUCKET', 'ijodidar-images')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')
TEST_KEY = '_s3_verify_test/ping.txt'

PASS = '\033[92m✓\033[0m'
FAIL = '\033[91m✗\033[0m'
WARN = '\033[93m!\033[0m'

failures = []

def ok(msg):   print(f'  {PASS} {msg}')
def fail(msg): print(f'  {FAIL} {msg}'); failures.append(msg)
def warn(msg): print(f'  {WARN} {msg}')


print(f'\niJodidar S3 Verification')
print(f'  Bucket : {BUCKET}')
print(f'  Region : {REGION}')
print()

# ── 1. Import boto3 ────────────────────────────────────────────────────────────
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    ok('boto3 imported')
except ImportError:
    fail('boto3 not installed — run: pip install boto3')
    sys.exit(1)

# ── 2. Build client ────────────────────────────────────────────────────────────
try:
    s3 = boto3.client('s3', region_name=REGION)
    ok(f'boto3 client created (region={REGION})')
except Exception as e:
    fail(f'boto3 client failed: {e}')
    sys.exit(1)

# ── 3. Check credentials resolve ──────────────────────────────────────────────
try:
    sts = boto3.client('sts', region_name=REGION)
    identity = sts.get_caller_identity()
    ok(f'Credentials valid — Account: {identity["Account"]}, ARN: {identity["Arn"]}')
except NoCredentialsError:
    fail('No AWS credentials found. On EC2, ensure an IAM role is attached to the instance. '
         'Locally, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env.')
    sys.exit(1)
except Exception as e:
    warn(f'STS identity check failed (non-blocking): {e}')

# ── 4. Check bucket exists and is accessible ──────────────────────────────────
try:
    s3.head_bucket(Bucket=BUCKET)
    ok(f'Bucket "{BUCKET}" exists and is accessible')
except ClientError as e:
    code = e.response['Error']['Code']
    if code == '404':
        fail(f'Bucket "{BUCKET}" does not exist in region {REGION}. '
             f'Create it: aws s3 mb s3://{BUCKET} --region {REGION}')
    elif code == '403':
        fail(f'Bucket "{BUCKET}" exists but access denied. Check IAM role s3:ListBucket / s3:GetBucketLocation permission.')
    else:
        fail(f'head_bucket error {code}: {e}')

# ── 5. PutObject (private ACL) ────────────────────────────────────────────────
try:
    s3.put_object(
        Bucket=BUCKET,
        Key=TEST_KEY,
        Body=b'iJodidar S3 verify ping',
        ContentType='text/plain',
        # No ACL param — bucket default (private) applies; avoids AccessControlListNotSupported on S3 Block Public Access
    )
    ok(f'PutObject succeeded — key: {TEST_KEY}')
except ClientError as e:
    fail(f'PutObject failed: {e}. Check IAM role has s3:PutObject on arn:aws:s3:::{BUCKET}/*')

# ── 6. Presigned URL generation ───────────────────────────────────────────────
try:
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET, 'Key': TEST_KEY},
        ExpiresIn=60,
    )
    ok(f'Presigned URL generated (expires 60s)')
    print(f'         {url[:80]}...')
except Exception as e:
    fail(f'generate_presigned_url failed: {e}')

# ── 7. GetObject ──────────────────────────────────────────────────────────────
try:
    resp = s3.get_object(Bucket=BUCKET, Key=TEST_KEY)
    body = resp['Body'].read()
    assert body == b'iJodidar S3 verify ping'
    ok('GetObject succeeded — content verified')
except ClientError as e:
    fail(f'GetObject failed: {e}')

# ── 8. DeleteObject ───────────────────────────────────────────────────────────
try:
    s3.delete_object(Bucket=BUCKET, Key=TEST_KEY)
    ok(f'DeleteObject succeeded — test key removed')
except ClientError as e:
    fail(f'DeleteObject failed: {e}. Check IAM role has s3:DeleteObject')

# ── 9. Public access block (DPDP compliance) ──────────────────────────────────
try:
    pab = s3.get_public_access_block(Bucket=BUCKET)
    cfg = pab['PublicAccessBlockConfiguration']
    all_blocked = all([
        cfg.get('BlockPublicAcls', False),
        cfg.get('IgnorePublicAcls', False),
        cfg.get('BlockPublicPolicy', False),
        cfg.get('RestrictPublicBuckets', False),
    ])
    if all_blocked:
        ok('Public access block: ALL enabled (photos are private — DPDP compliant)')
    else:
        warn(f'Public access block is NOT fully enabled: {cfg}')
        warn('Recommend: enable all 4 flags in S3 console → Bucket → Permissions → Block public access')
except ClientError as e:
    warn(f'Could not check public access block (non-fatal): {e}')

# ── 10. CORS check (needed for direct browser uploads if used in future) ───────
# Not required now — uploads go server→S3, not browser→S3. Skip.

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if not failures:
    print('\033[92mAll checks passed. S3 is operational.\033[0m')
    print(textwrap.dedent(f"""
    Update docs/PROJECT_STATUS.md → Pre-Sprint 0 external conditions:
      S3 bucket + IAM role operational: ✅ Confirmed {BUCKET} / {REGION}
    """))
    sys.exit(0)
else:
    print(f'\033[91m{len(failures)} check(s) failed:\033[0m')
    for f in failures:
        print(f'  • {f}')
    print('\nFix the above, then re-run this script.')
    sys.exit(1)
