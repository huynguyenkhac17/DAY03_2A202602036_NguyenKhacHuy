"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import inspect
import json
import os
import sys
import time
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


def run_baseline_chatbot(user_query: str, provider, verbose: bool = True):
    """
    Dựng Chatbot gốc (Baseline) — CẤP ĐỘ 2, không có công cụ.

    Giao thức baseline (phải giữ đúng để so sánh công bằng với Agent ở Mốc 3):
        system prompt + user message  ->  ĐÚNG 1 LLM call  ->  câu trả lời cuối

    Baseline TUYỆT ĐỐI KHÔNG được: gọi tool, nhúng sẵn kết quả tool vào prompt,
    hay khẳng định đã thực hiện xong một hành động nào đó.
    Vì vậy hàm này không hề đụng tới AVAILABLE_TOOLS -> tool_calls luôn = 0.
    """
    if verbose:
        print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    t0 = time.time()
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    elapsed = time.time() - t0

    if verbose:
        print(f"🤖 Chatbot trả lời:\n{response}")
        print(f"📊 llm_calls=1 | tool_calls=0 | {elapsed:.2f}s")

    return {
        "question": user_query,
        "answer": response,
        "llm_calls": 1,
        "tool_calls": 0,
        "elapsed": elapsed,
    }


def run_baseline_on_all_cases(tests, provider):
    """
    Chạy Chatbot Baseline trên TOÀN BỘ test cases của Role 1 (checklist Mốc 2).
    Trả về list kết quả để Role 5 đối chiếu và phân loại.
    """
    print("\n" + "=" * 70)
    print("💬 MỐC 2 — CHẠY CHATBOT BASELINE TRÊN TOÀN BỘ TEST CASES")
    print("=" * 70)
    print(f"⚙️ System Prompt đang dùng (của Role 3):\n{CHATBOT_BASELINE_PROMPT.strip()}")

    ket_qua = []
    for case in tests:
        print("\n" + "-" * 70)
        print(f"🧪 Test Case #{case['id']} — {case.get('category', '')}")
        print(f"🎯 Kỳ vọng: {case.get('expected_behavior', '')}")
        r = run_baseline_chatbot(case["question"], provider)
        r["id"] = case["id"]
        r["category"] = case.get("category", "")
        r["expected_behavior"] = case.get("expected_behavior", "")
        ket_qua.append(r)

    return ket_qua


def xuat_ket_qua_baseline(ket_qua, provider_name: str, model_name: str):
    """
    Ghi kết quả Chatbot Baseline ra docs/baseline_output.md cho Role 5.

    Role 5 giữ file docs/trace_eval.md, nên app KHÔNG ghi đè file đó.
    File này là dữ liệu thô do máy sinh, Role 5 copy sang trace_eval.md rồi
    phân loại từng case là correct / safe fallback / hallucinated.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    duong_dan = os.path.join(base_dir, "docs", "baseline_output.md")

    dong = [
        "# 💬 KẾT QUẢ CHATBOT BASELINE (Mốc 2)\n\n",
        "> File do `python src/app.py` sinh tự động — đừng sửa tay.\n",
        "> Role 5 copy sang `docs/trace_eval.md` rồi phân loại từng case.\n\n",
        f"* **Provider**: `{provider_name}` · **Model**: `{model_name}`\n",
        f"* **Thời điểm chạy**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "* **Giao thức**: 1 LLM call / câu hỏi, `tool_calls = 0`\n\n---\n",
    ]
    for r in ket_qua:
        dong.append(f"\n## Test Case #{r['id']} — {r['category']}\n\n")
        dong.append(f"**Câu hỏi**: {r['question']}\n\n")
        dong.append(f"**Kỳ vọng**: {r['expected_behavior']}\n\n")
        dong.append(f"**Chatbot trả lời**:\n\n```text\n{r['answer']}\n```\n\n")
        dong.append(f"* `llm_calls={r['llm_calls']}` · `tool_calls={r['tool_calls']}` · "
                    f"`{r['elapsed']:.2f}s`\n")
        dong.append("* **Phân loại** (Role 5 điền): `correct` / `safe fallback` / `hallucinated`\n")
        dong.append("\n---\n")

    with open(duong_dan, "w", encoding="utf-8") as f:
        f.write("".join(dong))
    return duong_dan


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

    # ---------- MỐC 2: Chatbot Baseline trên toàn bộ test cases ----------
    ket_qua_baseline = run_baseline_on_all_cases(tests, provider)

    print("\n" + "=" * 70)
    print("📊 TỔNG KẾT CHATBOT BASELINE")
    print("=" * 70)
    print(f"{'Case':<8}{'LLM calls':<12}{'Tool calls':<13}{'Thời gian':<12}")
    print("-" * 70)
    for r in ket_qua_baseline:
        print(f"#{r['id']:<7}{r['llm_calls']:<12}{r['tool_calls']:<13}{r['elapsed']:.2f}s")
    tong_tg = sum(r["elapsed"] for r in ket_qua_baseline)
    print("-" * 70)
    print(f"{'TỔNG':<8}{len(ket_qua_baseline):<12}{0:<13}{tong_tg:.2f}s")
    print("\n✅ Đúng giao thức baseline: mỗi câu 1 LLM call, tool_calls = 0.")

    duong_dan = xuat_ket_qua_baseline(ket_qua_baseline, provider.__class__.__name__, model_name)
    print(f"📝 Đã ghi kết quả ra: {os.path.relpath(duong_dan, os.getcwd())}")
    print("   ➜ Role 5 copy sang docs/trace_eval.md để phân loại từng case.")

    # ---------- MỐC 3: ReAct Agent (chưa lắp) ----------
    print("\n" + "=" * 70)
    print("🤖 MỐC 3 — REACT AGENT")
    print("=" * 70)
    run_react_agent(tests[0]["question"], provider)
