import os
import json
from pathlib import Path
from dotenv import load_dotenv

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

# Set to True if you want to bypass AWS entirely and test locally right now
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
        # Instant local mock response to verify frontend UI works smoothly
        return {
            "artifact_name": "Quantum Crystalline Glyph-Tablet (Simulated Local Mode)",
            "artifact_id": f"ARCH-{future_year}-9988",
            "estimated_era": "Late Silicon Age (c. 2000-2030 CE)",
            "civilization": "The Proto-Digital Nomads of Sector 4",
            "perceived_original_function": "A sacred handheld scrying mirror used for projecting glowing portal illusions.",
            "archaeological_significance": "Essential ritualistic tool for summoning food particles and communicating with distant nomadic tribes.",
            "historical_context": "Before the great grid expansion of 2412, ancient humans spent hours staring blankly into these rectangular glass monoliths as a form of meditation.",
            "condition": "Heavily fossilized with minor fingerprint smudges from ancient carbon-based lifeforms.",
            "curator_note": "Notice how the screen is cracked—clearly a sacred offering broken during a primitive ritual known as 'dropping the phone'."
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
        # Fallback to mock response if AWS throttles so your frontend never breaks during demos/testing
        print(f"\n[AWS Throttled/Error caught: {e}] -> Falling back to local mock response.")
        return {
            "artifact_name": "Resilient Silicon Relic (Fallback Mode)",
            "artifact_id": f"ARCH-{future_year}-FALLBACK",
            "estimated_era": "Late Silicon Age (c. 2000-2030 CE)",
            "civilization": "The Proto-Digital Nomads",
            "perceived_original_function": "An ancient portable altar slab.",
            "archaeological_significance": "Used for spiritual alignment and casting glowing runes.",
            "historical_context": "A classic artifact of the pre-singularity human era.",
            "condition": "Fossilized state, network connection throttled.",
            "curator_note": "The cloud spirits (AWS) were sleeping, but the local archive holds steady!"
        }
