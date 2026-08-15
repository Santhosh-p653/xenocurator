
# Internet Archaeologist 

Speculative AI application analyzing modern objects as distant future artifacts using Amazon Nova.

## Running Locally

### 1. Backend Setup
```bash
pip install -r requirements.txt
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
uvicorn backend.server:app --reload --port 8000
```
### Frontend Setup 
```bash
npm install
npm run dev
```