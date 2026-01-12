import os, boto3, logging, requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_S3_FOLDER = os.getenv("AWS_S3_FOLDER", "")
LARK_BOT_URL = os.getenv("LARK_BOT_URL")

app = FastAPI()

# Configure logging
app_logger = logging.getLogger("s3presigned")
app_logger.setLevel(logging.INFO)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.INFO)

handler = RotatingFileHandler("app.log", maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app_logger.addHandler(handler)
uvicorn_access_logger.addHandler(handler)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=f'https://s3.{AWS_REGION}.amazonaws.com',
    config=boto3.session.Config(s3={'addressing_style': 'virtual'}),
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def send_lark(text, parse_mode):
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    content = {"msg_type": parse_mode, "content": {"text": text}}
    req = requests.post(LARK_BOT_URL, headers=headers, json=content)
    return req.json()

@app.get("/generate_presigned_urls")
async def generate_presigned_urls(file_name: str):
    try:
        full_file_path = f"{AWS_S3_FOLDER}{file_name}"
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': full_file_path},
            ExpiresIn=3600
        )
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': full_file_path},
            ExpiresIn=3600
        )
        app_logger.info(f"Generated presigned URLs for file: {full_file_path}")
        #return {"upload_url": upload_url, "download_url": download_url}
        text = f"jvm oom, download link: {download_url}"
        message = send_lark(text, 'text')
        app_logger.info(f"send_lark: {message}")
        return {"upload_url": upload_url}
    except ClientError as e:
        app_logger.error(f"Error generating presigned URLs: {e}")
        raise HTTPException(status_code=500, detail="Error generating presigned URLs")

@app.get("/check_file_exists")
async def check_file_exists(file_name: str):
    try:
        full_file_path = f"{AWS_S3_FOLDER}{file_name}"
        s3_client.head_object(Bucket=AWS_S3_BUCKET, Key=full_file_path)
        app_logger.info(f"File exists: {full_file_path}")
        return {"exists": True}
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            app_logger.info(f"File does not exist: {full_file_path}")
            return {"exists": False}
        else:
            app_logger.error(f"Error checking file existence: {e}")
            raise HTTPException(status_code=500, detail="Error checking file existence")

@app.get("/dump_hprof")
async def download_dump_hprof():
    file_path = "dump_hprof.sh"
    if os.path.exists(file_path):
        app_logger.info(f"File {file_path} requested for download.")
        return FileResponse(path=file_path, filename="dump_hprof.sh", media_type='text/x-shellscript')
    else:
        app_logger.error(f"File {file_path} not found.")
        return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    app_logger.info("Starting the FastAPI application.")
    uvicorn.run(app, host="0.0.0.0", port=8811, headers=[("server", "Gkqos")])
