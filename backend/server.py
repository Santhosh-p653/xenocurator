import os
import json
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3

app = FastAPI(title="Internet Archaeologist API")

# Allow CORS for React local dev & serverless deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AWS Bedrock Runtime Client (Credentials pulled from env)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

SYSTEM_PROMPT = """
You are a senior curator at the Intergalactic Institute of Deep Temporal Archaeology operating in the distant future. 
Your task is to analyze modern-day human relics (21st century or earlier) through a wildly mistaken, overly academic, yet logical futuristic lens. 
You will receive an image of an object, a target future year, and optional user notes.

Respond ONLY with a valid JSON object matching this schema precisely without markdown wrapping:
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
        # Read and encode image to Base64
        contents = await image.read()
        encoded_image = base64.b64encode(contents).decode("utf-8")
        
        # User message construct
        prompt_text = f"Analyze this relic from the perspective of an archaeologist in the year {future_year} AD."
        if description:
            prompt_text += f"\nFragmentary record notes found near site: '{description}'"

        # Amazon Nova / Bedrock Payload Construction
        body = {
            "schemaVersion": "messages-v1",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": image.filename.split(".")[-1].lower() if "." in image.filename else "jpeg",
                                "source": {"bytes": encoded_image}
                            }
                        },
                        {"text": prompt_text}
                    ]
                }
            ],
            "system": [{"text": SYSTEM_PROMPT}],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.7
            }
        }

        # Invoke Amazon Nova (amazon.nova-lite-v1:0 or amazon.nova-pro-v1:0)
        response = bedrock.invoke_model(
            modelId=os.getenv("NOVA_MODEL_ID", "amazon.nova-lite-v1:0"),
            body=json.dumps(body)
        )
        
        response_body = json.loads(response.get("body").read())
        raw_text = response_body['output']['message']['content'][0]['text']
        
        # Parse and return JSON artifact payload
        artifact_data = json.loads(raw_text)
        return artifact_data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse structured response from Nova model.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
