import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from backend folder
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3

app = FastAPI(title="Internet Archaeologist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """
You are a senior curator at the Intergalactic Institute of Deep Temporal Archaeology operating in the distant future. 
Your task is to analyze modern-day human relics through a wildly mistaken, overly academic, yet logical futuristic lens.

Respond ONLY with a valid JSON object matching this schema precisely without markdown code blocks:
{
  "artifact_name": "Fictional speculative name",
  "artifact_id": "ARCH-XXXX-XXXX",
  "estimated_era": "e.g., Late Silicon Age (c. 2000-2030 CE)",
  "civilization": "e.g., The Proto-Digital Nomads",
  "perceived_original_function": "Funny/misunderstood purpose",
  "archaeological_significance": "Why this object mattered to their ritualistic or daily life",
  "historical_context": "Deep historical lore explaining how humans lived back then based on this artifact",
  "condition": "e.g., Heavily fossilized, missing battery sac",
  "curator_note": "A witty closing comment from the chief archaeologist"
}
"""

@app.post("/analyze")
async def analyze_artifact(
    image: UploadFile = File(...),
    future_year: str = Form("3026"),
    description: str = Form("")
):
    try:
        # Initialize boto3 client using environment variables
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

        prompt_text = f"{SYSTEM_PROMPT}\n\nAnalyze this relic from the perspective of an archaeologist in the year {future_year} AD."
        if description:
            prompt_text += f"\nFragmentary record notes found near site: '{description}'"

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

        raw_text = response['output']['message']['content'][0]['text'].strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].replace("json", "").strip()

        return json.loads(raw_text)

    except Exception as e:
        import traceback
        print("\n================ BACKEND ERROR TRACE ================")
        traceback.print_exc()
        print("=====================================================\n")
        raise HTTPException(status_code=500, detail=str(e))
