from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, HTTPException, Body

# 1) 更稳的 .env 加载
env_path = find_dotenv()
load_dotenv(env_path)

# 2) 统一用 GITHUB_TOKEN（与 curl 一致）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN not set. Check your .env or environment.")

# 3) 个人账号用这个；若走组织额度，替换为：
# GITHUB_API_URL = "https://models.github.ai/orgs/<ORG>/inference/chat/completions"
GITHUB_API_URL = "https://models.github.ai/inference/chat/completions"

# 4) FastAPI
app = FastAPI()

class ResumeInput(BaseModel):
    resume_text: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/analyze")
async def analyze_resume(resume_data: ResumeInput):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    prompt = (
        "You are a professional resume reviewer. "
        "Analyze the following resume text and provide 3-5 actionable suggestions for improvement.\n\n"
        f"Resume Text:\n\"{resume_data.resume_text}\"\n\n"
        "Suggestions:"
    )

    payload = {
        # 5) 先用你已验证可用的模型
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(GITHUB_API_URL, headers=headers, json=payload)
            resp.raise_for_status()

            data = resp.json()
            # 6) 更健壮的解析
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise HTTPException(status_code=502, detail={"error": "Unexpected response schema", "raw": data})

            return {"ai_suggestion": content}

        except httpx.HTTPStatusError as e:
            # 返回 GitHub 的状态码和 body，方便定位
            raise HTTPException(status_code=e.response.status_code, detail={"error": "GitHub API error", "body": e.response.text})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": f"Internal error: {e}"})



# -----------------------------------------------
# 🟢 新增的 API 接口：接受纯文本 (text/plain)
# 使用 GitHub Models API，与 /analyze 一致
# -----------------------------------------------
from fastapi import Body

@app.post("/analyze_plain_text")
async def analyze_resume_plain_text(
    resume_text: str = Body(..., media_type="text/plain")
):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }

    prompt = (
        "You are a professional resume reviewer. "
        "Analyze the following resume text and provide 3-5 actionable suggestions for improvement.\n\n"
        f"Resume Text:\n\"{resume_text}\"\n\n"
        "Suggestions:"
    )

    payload = {
        "model": "openai/gpt-4o-mini",  # ✅ 用你在 GitHub Models 上能用的模型
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GITHUB_API_URL, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            # 解析返回内容
            ai_suggestion = data["choices"][0]["message"]["content"]
            return {"ai_suggestion": ai_suggestion}

        except httpx.HTTPStatusError as e:
            return {
                "error": f"GitHub API error: {e.response.status_code}",
                "details": e.response.text,
            }
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}
