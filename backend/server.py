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
from botocore.config import Config

app = FastAPI(title="Internet Archaeologist API - Local Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set to True to display the circus artifact mock response instantly for testing
FORCE_LOCAL_MOCK = True 

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
    # Read image to ensure file handling works properly on frontend-backend connection
    contents = await image.read()
    
    if FORCE_LOCAL_MOCK:
        # Circus-themed mock response to prove application works smoothly
        return {
            "artifact_name": "Grand Pyrotechnic Big-Top Spectacle Relic",
            "artifact_id": f"ARCH-{future_year}-CIRCUS",
            "estimated_era": "Late Silicon Age (c. 2000-2030 CE)",
            "civilization": "The Nomadic Carnival Guild",
            "perceived_original_function": "A colossal red-and-white striped fabric biosphere used for housing acrobatic bipedal entities and tamed fauna.",
            "archaeological_significance": "Served as a central seasonal gathering space where ancient humans partook in gravity-defying rituals, sugar-infused dust consumption ('cotton candy'), and hypnotic spinning performances.",
            "historical_context": "Before the Great Urban Merger of 2490, wandering entertainment factions would erect these massive temporary canvas shells to distract populations from their daily digital toil with death-defying feats and juggling.",
            "condition": "Faded tensile fabric with traces of popcorn resin and sawdust fossilization.",
            "curator_note": "Notice the concentric seating rings—clearly designed for spectators to watch mortal humans launch themselves through the air for momentary public validation."
        }

    try:
        retry_config = Config(retries={'max_attempts': 3, 'mode': 'adaptive'})
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            config=retry_config
        )

        image_format = image.filename.split(".")[-1].lower() if image.filename and "." in image.filename else "jpeg"
        if image_format == "jpg":
            image_format = "jpeg"

        prompt_text = f"{SYSTEM_PROMPT}\n\nAnalyze this relic from the perspective of an archaeologist in the year {future_year} AD."
        
        response = client.converse(
            modelId=os.getenv("NOVA_MODEL_ID", "amazon.nova-micro-v1:0"),
            messages=[{
                "role": "user",
                "content": [
                    {"image": {"format": image_format, "source": {"bytes": contents}}},
                    {"text": prompt_text}
                ]
            }]
        )

        raw_text = response['output']['message']['content'][0]['text'].strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].replace("json", "").strip()

        return json.loads(raw_text)

    except Exception as e:
        print(f"\n[AWS Throttled/Error caught: {e}] -> Falling back to local circus mock response.")
        return {
            "artifact_name": "Grand Pyrotechnic Big-Top Spectacle Relic (Fallback)",
            "artifact_id": f"ARCH-{future_year}-FALLBACK",
            "estimated_era": "Late Silicon Age (c. 2000-2030 CE)",
            "civilization": "The Nomadic Carnival Guild",
            "perceived_original_function": "A colossal red-and-white striped fabric biosphere.",
            "archaeological_significance": "Served as a central seasonal gathering space.",
            "historical_context": "A classic traveling entertainment ecosystem.",
            "condition": "Faded tensile fabric with dust fossilization.",
            "curator_note": "The cloud networks were busy, but the circus archive remains eternal!"
        }
