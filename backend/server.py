import os
import json
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import Strands components
from strands import Agent
from strands.models import BedrockModel

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

# Initialize Amazon Nova via Strands Bedrock Model driver
nova_model = BedrockModel(
    model_id=os.getenv("NOVA_MODEL_ID", "amazon.nova-lite-v1:0"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# Initialize the Strands Archaeologist Agent
archaeologist_agent = Agent(
    model=nova_model,
    system_prompt=SYSTEM_PROMPT
)

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
        image_format = image.filename.split(".")[-1].lower() if "." in image.filename else "jpeg"
        
        # User message construct
        prompt_text = f"Analyze this relic from the perspective of an archaeologist in the year {future_year} AD."
        if description:
            prompt_text += f"\nFragmentary record notes found near site: '{description}'"

        # Pass multimodal payload to the Strands Agent
        # Strands standard message structure for multimodal input
        message = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": image_format,
                            "source": {"bytes": encoded_image}
                        }
                    },
                    {"text": prompt_text}
                ]
            }
        ]

        # Execute Strands Agent workflow
        response = archaeologist_agent.run(message)
        
        # Parse JSON output from Strands Agent text response
        raw_text = response.text.strip()
        
        # Strip potential markdown formatting if returned
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].replace("json", "").strip()

        artifact_data = json.loads(raw_text)
        return artifact_data

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse structured JSON response from Strands Agent.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
