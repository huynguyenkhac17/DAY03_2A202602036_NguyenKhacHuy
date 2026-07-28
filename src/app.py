"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import inspect
import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
#
# ⚠️ CHỈ import AVAILABLE_TOOLS, KHÔNG import trực tiếp từng hàm tool.
#    Bản gốc viết `from tools import AVAILABLE_TOOLS, get_weather, search_flights`,
#    nên khi Role 2 đổi bộ tool sang đề tài đơn hàng thì app.py crash ngay
#    (ImportError: cannot import name 'get_weather').
#    Đi qua registry AVAILABLE_TOOLS thì Role 2 thêm/xoá/đổi tên tool bao nhiêu lần
#    app.py cũng không cần sửa lại.
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def kiem_tra_tool_registry():
    """
    Smoke test Mốc 1: in ra các tool Role 2 đã đăng ký kèm chữ ký hàm.
    Dùng để cả nhóm xác nhận môi trường + file tools.py đã nạp được.
    """
    print(f"\n🛠️ Tool Registry ({len(AVAILABLE_TOOLS)} tool đã đăng ký):")
    for ten, fn in AVAILABLE_TOOLS.items():
        tham_so = ", ".join(inspect.signature(fn).parameters.keys()) or "(không tham số)"
        doc = (inspect.getdoc(fn) or "").strip().splitlines()
        mo_ta = doc[0] if doc else "(chưa có docstring)"
        print(f"   • {ten}({tham_so}) — {mo_ta}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.

    🚧 CHƯA LẮP — đây là phần việc của MỐC 3.
    Bản mẫu cũ ở đây chỉ `if step == 1 / elif step == 2` rồi print sẵn Thought/Action/
    Final Answer về thời tiết Hà Nội: nó KHÔNG gọi LLM, KHÔNG parse Action, KHÔNG dùng
    AVAILABLE_TOOLS. Đó là trace diễn kịch chứ không phải ReAct.

    Mốc 3 sẽ thay bằng vòng lặp thật:
        LLM sinh Thought + Action -> app parse -> app gọi tool trong AVAILABLE_TOOLS
        -> app chèn Observation -> quay lại LLM, đến khi có Final Answer hoặc chạm
        phanh MAX_ITERATIONS.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"🛡️ Guardrail đang cấu hình: MAX_ITERATIONS = {MAX_ITERATIONS}")
    print("🚧 Vòng lặp ReAct chưa được lắp — sẽ hoàn thiện ở Mốc 3 (Role 3 + Role 4).")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    # Smoke test Mốc 1: xác nhận tools.py của Role 2 nạp được
    kiem_tra_tool_registry()

    tests = load_test_cases()
    print(f"\n✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    if not tests:
        print("⚠️ config/test_cases.json đang rỗng — Role 1 cần bổ sung ở Mốc 2.")
        sys.exit(0)

    # Chạy thử câu test số 3 (nếu chưa đủ 3 case thì lấy case đầu tiên)
    sample_query = tests[2]["question"] if len(tests) >= 3 else tests[0]["question"]
    print(f"🧪 Câu test đang dùng để demo: {sample_query}\n")

    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
