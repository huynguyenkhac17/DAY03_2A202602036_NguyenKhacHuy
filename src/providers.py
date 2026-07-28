"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import re
import sys
import json
import time
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini Provider.

    ⚠️ HAI CÁI BẪY CỦA FREE TIER — đọc trước khi đổi model:
      1. 'gemini-2.5-flash' và 'gemini-2.5-flash-lite' đã bị Google khoá với tài
         khoản tạo mới -> trả về 404 NOT_FOUND.
      2. 'gemini-flash-latest' hiện trỏ tới 'gemini-3.6-flash', free tier chỉ cho
         20 request/NGÀY. Vòng lặp ReAct đốt 2-4 request mỗi câu hỏi, chạy hết 5
         test case là cạn quota cả ngày.
    -> Dùng 'gemini-flash-lite-latest': hạn mức ngày rộng hơn nhiều, vẫn thừa sức
       bám đúng định dạng Thought/Action của bài Lab.
    """
    MAX_RETRIES = 2
    MAX_WAIT_SECONDS = 35

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-flash-lite-latest"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"

        contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        for lan_thu in range(self.MAX_RETRIES + 1):
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                )
                return response.text
            except Exception as e:
                loi = str(e)
                het_quota = "429" in loi or "RESOURCE_EXHAUSTED" in loi
                # Hết quota theo NGÀY thì chờ bao lâu cũng vô ích -> báo lỗi ngay.
                theo_ngay = "PerDay" in loi
                if het_quota and theo_ngay:
                    return ("[Gemini Error]: Hết quota FREE TIER theo NGÀY cho model "
                            f"'{self.model_name}'. Hãy đổi LLM_MODEL trong .env sang model "
                            "khác (VD: gemini-flash-lite-latest), hoặc đợi sang ngày mai.")
                if het_quota and lan_thu < self.MAX_RETRIES:
                    m = re.search(r"'retryDelay':\s*'(\d+)s'", loi)
                    cho = min(int(m.group(1)) + 2 if m else 15, self.MAX_WAIT_SECONDS)
                    print(f"   ⏳ Gemini báo 429 (giới hạn/phút), chờ {cho}s rồi thử lại "
                          f"(lần {lan_thu + 1}/{self.MAX_RETRIES})...")
                    time.sleep(cho)
                    continue
                return f"[Gemini Exception]: {loi}"
        return "[Gemini Exception]: Không thể gọi API sau nhiều lần thử lại."


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        if "thời tiết" in text and "hà nội" in text:
            return "Thought: Cần tra cứu thời tiết Hà Nội.\nAction: get_weather['Hà Nội']"
        return "🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
