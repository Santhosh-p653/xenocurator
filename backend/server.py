import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3

app = FastAPI(title="Internet Archaeologist API - Key Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_artifact(
    image: UploadFile = File(...),
    future_year: str = Form("3026"),
    description: str = Form("")
):
    try:
        # 1. Test raw boto3 client initialization with new keys
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

        contents = await image.read()
        image_format = image.filename.split(".")[-1].lower() if image.filename and "." in image.filename else "jpeg"
        if image_format == "jpg":
            image_format = "jpeg"

        prompt_text = f"Analyze this relic from the perspective of an archaeologist in the year {future_year} AD. Respond ONLY with a valid JSON object with keys: artifact_name, artifact_id, estimated_era, civilization, perceived_original_function, archaeological_significance, historical_context, condition, curator_note."

        # 2. Direct Bedrock Converse API payload structure (skips Strands layer completely)
        response = client.converse(
            modelId=os.getenv("NOVA_MODEL_ID", "us.amazon.nova-lite-v1:0"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": image_format,
                                "source": {"bytes": contents}
                            }
                        },
                        {"text": prompt_text}
                    ]
                }
            ]
        )

        # Extract text response from Bedrock Converse structure
        raw_text = response['output']['message']['content'][0]['text'].strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].replace("json", "").strip()

        return json.loads(raw_text)

    except Exception as e:
        import traceback
        print("\n================ DIRECT BEDROCK TEST ERROR ================")
        traceback.print_exc()
        print("===========================================================\n")
        raise HTTPException(status_code=500, detail=str(e))
