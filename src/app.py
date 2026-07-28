"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import inspect
import json
import os
import re
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

# Import thêm cả module để đọc được các hằng số TUỲ CHỌN của Role 3 bằng getattr()
# (VD: SAFE_FALLBACK_MESSAGE). Làm vậy thì Role 3 chưa khai báo app vẫn chạy bình thường.
import prompts as prompts_module

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
    Ghi dữ liệu thô của Chatbot Baseline ra docs/auto/baseline_raw.md.

    ⚠️ Vì sao ghi vào thư mục docs/auto/ chứ không ghi thẳng vào docs/:
    file này bị GHI ĐÈ mỗi lần chạy app. Trước đây nó nằm ở
    docs/baseline_output.md, Role 5 sửa tay vào đó để phân loại -> lần chạy
    sau xoá sạch, và git thì conflict. Tách hẳn thư mục docs/auto/ cho máy,
    còn docs/ để cho người viết.

    File nộp bài vẫn là docs/trace_eval.md do Role 5 giữ — app KHÔNG đụng vào.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    thu_muc = os.path.join(base_dir, "docs", "auto")
    os.makedirs(thu_muc, exist_ok=True)
    duong_dan = os.path.join(thu_muc, "baseline_raw.md")

    dong = [
        "# 💬 KẾT QUẢ CHATBOT BASELINE (Mốc 2)\n\n",
        "> ⚠️ File do `python src/app.py` sinh tự động, BỊ GHI ĐÈ mỗi lần chạy — đừng sửa tay.\n",
        "> Đây KHÔNG phải file nộp bài. File nộp là `docs/trace_eval.md`.\n",
        "> Role 5 copy số liệu sang `docs/trace_eval.md` rồi phân loại ở đó.\n\n",
        f"* **Provider**: `{provider_name}` · **Model**: `{model_name}`\n",
        f"* **Thời điểm chạy**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "* **Giao thức**: 1 LLM call / câu hỏi, `tool_calls = 0`\n\n---\n",
    ]
    for r in ket_qua:
        dong.append(f"\n## Test Case #{r['id']} — {r['category']}\n\n")
        dong.append(f"**Câu hỏi**: {r['question']}\n\n")
        # Lưu ý: expected_behavior của Role 1 mô tả hành vi mong đợi ở AGENT.
        # Phải ghi rõ, không thì đọc báo cáo baseline sẽ tưởng Chatbot làm sai,
        # trong khi Chatbot vốn KHÔNG được phép gọi tool.
        dong.append(f"**Kỳ vọng ở Agent** (chỉ để đối chiếu — Chatbot baseline "
                    f"không được gọi tool): {r['expected_behavior']}\n\n")
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


# =============================================================================
# 🔍 PARSER — Bóc tách Thought / Action / Final Answer từ output thô của LLM
# Bám đúng định dạng Role 3 quy định trong REACT_SYSTEM_PROMPT:
#     Action: get_order_status[ORD1001]          (tham số KHÔNG có dấu nháy)
#     Action: create_return_request[ORD1001, Sản phẩm bị lỗi]
#     Action: get_return_policy[]                (không tham số)
# =============================================================================
FENCE_RE = re.compile(r"^\s*```[a-zA-Z]*\s*$", re.MULTILINE)
THOUGHT_RE = re.compile(r"^\s*Thought\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
ACTION_RE = re.compile(r"^\s*Action\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
FINAL_RE = re.compile(r"Final\s*Answer\s*:\s*(.*)", re.IGNORECASE | re.DOTALL)
OBSERVATION_RE = re.compile(r"^\s*Observation\s*:", re.IGNORECASE | re.MULTILINE)
CALL_RE = re.compile(r"^([A-Za-z_]\w*)\s*[\[\(](.*)[\]\)]\s*$", re.DOTALL)
BARE_CALL_RE = re.compile(r"^([A-Za-z_]\w*)\s*$")


def _split_args(raw: str):
    """
    Tách chuỗi tham số thành args/kwargs. Chấp nhận cả có lẫn không có dấu nháy,
    vì prompt của Role 3 dạy LLM viết không nháy: create_return_request[ORD1001, Sản phẩm bị lỗi]
    """
    args, kwargs = [], {}
    if not raw.strip():
        return args, kwargs

    phan, buf, quote = [], "", None
    for ch in raw:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf += ch
        elif ch in "\"'":
            quote = ch
        elif ch == ",":
            phan.append(buf)
            buf = ""
        else:
            buf += ch
    phan.append(buf)

    for p in phan:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"^([A-Za-z_]\w*)\s*=\s*(.+)$", p, re.DOTALL)
        if m:
            kwargs[m.group(1)] = m.group(2).strip().strip("\"'")
        else:
            args.append(p)
    return args, kwargs


def parse_llm_output(raw: str) -> dict:
    """
    Trả về dict có 'kind' ∈ {final, action, malformed, empty}.

    🛡️ AN TOÀN QUAN TRỌNG: cắt bỏ mọi thứ từ dòng "Observation:" trở đi.
    LLM rất hay tự bịa Observation giả để "diễn" cho trọn kịch bản. Nếu không chặn,
    Agent sẽ kết luận dựa trên dữ liệu do chính nó tưởng tượng ra — đúng thứ mà cả
    bài Lab đang muốn chứng minh là KHÔNG được phép xảy ra.
    """
    text = FENCE_RE.sub("", raw or "")

    m_obs = OBSERVATION_RE.search(text)
    bia_observation = m_obs is not None
    if bia_observation:
        text = text[: m_obs.start()]

    m_thought = THOUGHT_RE.search(text)
    thought = m_thought.group(1).strip() if m_thought else ""

    m_final = FINAL_RE.search(text)
    m_action = ACTION_RE.search(text)

    # Có cả hai thì cái nào xuất hiện TRƯỚC sẽ thắng — chặn kiểu LLM vừa gọi Action
    # vừa tự kết luận Final Answer khi chưa hề có dữ liệu.
    if m_final and (m_action is None or m_final.start() < m_action.start()):
        return {"kind": "final", "thought": thought,
                "final_answer": m_final.group(1).strip(), "bia_observation": bia_observation}

    if m_action:
        call = m_action.group(1).strip().rstrip(".")
        m_call = CALL_RE.match(call)
        if m_call:
            ten, raw_args = m_call.group(1), m_call.group(2)
            args, kwargs = _split_args(raw_args)
        elif BARE_CALL_RE.match(call):
            ten, args, kwargs = call, [], {}
        else:
            return {"kind": "malformed", "thought": thought,
                    "raw_action": call, "bia_observation": bia_observation}
        return {"kind": "action", "thought": thought, "tool": ten,
                "args": args, "kwargs": kwargs, "bia_observation": bia_observation}

    return {"kind": "empty", "thought": thought, "bia_observation": bia_observation}


# =============================================================================
# ⚙️ EXECUTOR — Thực thi tool an toàn. Mọi lỗi đều biến thành Observation
# để Agent đọc và tự sửa, thay vì làm sập chương trình.
# =============================================================================
def execute_tool(ten: str, args: list, kwargs: dict, tools: dict):
    """Trả về (status, observation). Không bao giờ raise ra ngoài."""
    if ten not in tools:
        return "unknown_tool", (
            f"LỖI: Tool '{ten}' không tồn tại. Các tool hợp lệ là: "
            f"{', '.join(tools.keys())}. Hãy chọn lại một tool trong danh sách."
        )

    fn = tools[ten]
    sig = inspect.signature(fn)
    try:
        sig.bind(*args, **kwargs)
    except TypeError as e:
        return "bad_args", (
            f"LỖI THAM SỐ: {e}. Cú pháp đúng là: "
            f"{ten}[{', '.join(sig.parameters.keys())}]. Hãy gọi lại cho đúng."
        )

    try:
        ket_qua = str(fn(*args, **kwargs))
    except Exception as e:  # noqa: BLE001 - tool tuyệt đối không được làm sập app
        return "crash", f"LỖI THỰC THI TOOL: {type(e).__name__}: {e}"

    if ket_qua.strip().upper().startswith("LỖI"):
        return "tool_error", ket_qua
    return "ok", ket_qua


def _loi_provider(text: str) -> bool:
    """Nhận diện chuỗi lỗi do providers.py trả về, VD: '[Gemini Exception]: ...'"""
    t = (text or "").strip()
    return t.startswith("[") and ("Error]" in t[:40] or "Exception]" in t[:40])


# =============================================================================
# 🧠 CẤP 3 — REACT AGENT LOOP (Thought -> Action -> Observation)
# =============================================================================
def run_react_agent(user_query: str, provider, tools: dict = None,
                    max_iterations: int = None, verbose: bool = True):
    """
    Vòng lặp ReAct thật sự:

        LLM sinh Thought + Action  ->  app parse  ->  app gọi tool thật trong
        AVAILABLE_TOOLS  ->  app chèn Observation vào scratchpad  ->  quay lại LLM

    lặp cho tới khi có Final Answer hoặc chạm phanh Guardrail.

    4 nguyên tắc bất biến được cài đặt ở đây:
      1. Không lặp vô hạn        -> MAX_ITERATIONS + chống lặp Action trùng.
      2. Mỗi Action đúng 1 Observation, do APP chèn -> parse_llm_output() cắt bỏ
         mọi Observation do LLM tự bịa.
      3. Observation quay lại prompt -> scratchpad được nối vào mỗi lượt gọi.
      4. Không khẳng định khi thiếu bằng chứng -> lỗi tool trả về dạng Observation
         để Agent đổi hướng, không cho phép đoán bừa.
    """
    tools = tools if tools is not None else AVAILABLE_TOOLS
    gioi_han = max_iterations or MAX_ITERATIONS
    fallback = getattr(
        prompts_module, "SAFE_FALLBACK_MESSAGE",
        "Xin lỗi bạn, mình chưa thể hoàn tất yêu cầu này một cách chắc chắn nên xin phép "
        "dừng lại thay vì đưa thông tin có thể sai. Bạn vui lòng kiểm tra lại mã đơn hàng "
        "hoặc liên hệ tổng đài 1900-1234 để được hỗ trợ trực tiếp nhé!",
    )

    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
        print(f"🛡️ Guardrails: MAX_ITERATIONS={gioi_han}, chống lặp Action trùng")

    scratchpad = ""
    trace = []
    da_goi = {}
    llm_calls = tool_calls = errors = 0
    final_answer = None
    dung_boi = None
    t0 = time.time()
    step = 0

    while step < gioi_han:
        step += 1
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{gioi_han}) ---")

        # Observation của các bước trước được nối vào đây -> nguyên tắc số 3
        user_prompt = f"Question: {user_query}\n\n{scratchpad}"
        raw = provider.generate(user_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        llm_calls += 1

        # Provider chết (sai key, hết quota, mất mạng) -> dừng ngay, đừng đốt vòng lặp
        if _loi_provider(raw):
            dung_boi = "provider_error"
            final_answer = f"{fallback}\n(Chi tiết kỹ thuật: {raw})"
            if verbose:
                print(f"💥 LỖI PROVIDER: {raw}")
            break

        parsed = parse_llm_output(raw)
        buoc = {"step": step, "thought": parsed.get("thought", "")}

        if parsed.get("bia_observation") and verbose:
            print("   ⚠️ LLM cố tự bịa 'Observation:' — parser đã cắt bỏ.")

        if verbose and parsed.get("thought"):
            print(f"🧠 Thought: {parsed['thought']}")

        # ---------- Agent kết luận ----------
        if parsed["kind"] == "final":
            final_answer = parsed["final_answer"]
            dung_boi = "final_answer"
            buoc["final_answer"] = final_answer
            trace.append(buoc)
            if verbose:
                print(f"🏁 Final Answer: {final_answer}")
            break

        # ---------- Agent gọi tool ----------
        if parsed["kind"] == "action":
            ten, args, kwargs = parsed["tool"], parsed["args"], parsed["kwargs"]
            hien_thi = f"{ten}[{', '.join(list(args) + [f'{k}={v}' for k, v in kwargs.items()])}]"
            buoc["action"] = hien_thi
            if verbose:
                print(f"🛠️ Action: {hien_thi}")

            # 🛡️ GUARDRAIL: phát hiện gọi lại y hệt một Action đã gọi
            khoa = f"{ten}|{args}|{sorted(kwargs.items())}"
            da_goi[khoa] = da_goi.get(khoa, 0) + 1
            if da_goi[khoa] > 2:
                dung_boi = "guardrail_lap_action"
                if verbose:
                    print(f"🛡️ GUARDRAIL: Action này đã lặp {da_goi[khoa]} lần với cùng tham số. Ngắt an toàn!")
                trace.append(buoc)
                break

            status, observation = execute_tool(ten, args, kwargs, tools)
            tool_calls += 1
            if status != "ok":
                errors += 1

            if da_goi[khoa] > 1:
                observation = (
                    "⚠️ LƯU Ý: Bạn đã gọi đúng action này trước đó, kết quả không đổi. "
                    f"Hãy đổi hướng hoặc kết luận. || {observation}"
                )

            buoc["observation"] = observation
            buoc["status"] = status
            trace.append(buoc)
            if verbose:
                print(f"👁️ Observation: {observation}")

            scratchpad += (
                f"Thought: {parsed.get('thought', '')}\n"
                f"Action: {hien_thi}\n"
                f"Observation: {observation}\n\n"
            )
            continue

        # ---------- Output sai định dạng -> dạy lại Agent ----------
        errors += 1
        if parsed["kind"] == "malformed":
            observation = (
                f"LỖI CÚ PHÁP: Không đọc được lệnh '{parsed['raw_action']}'. "
                f"Hãy viết đúng dạng: Action: ten_cong_cu[tham_so]"
            )
        else:
            observation = (
                "LỖI ĐỊNH DẠNG: Phản hồi không chứa 'Action:' cũng không chứa 'Final Answer:'. "
                "Hãy xuất lại theo đúng một trong hai mẫu đã quy định."
            )
        buoc["observation"] = observation
        buoc["status"] = "format_error"
        trace.append(buoc)
        if verbose:
            print(f"👁️ Observation (hệ thống sửa lỗi): {observation}")
        scratchpad += f"{raw.strip()}\nObservation: {observation}\n\n"

    # ---------- Chạm phanh Guardrail ----------
    if final_answer is None:
        dung_boi = dung_boi or "guardrail_max_iterations"
        final_answer = fallback
        if verbose:
            print(f"\n🛡️ GUARDRAIL TRIGGERED ({dung_boi}) — dừng an toàn sau {step} bước.")
            print(f"🏁 Safe Fallback: {final_answer}")

    elapsed = time.time() - t0
    if verbose:
        print(f"\n📊 steps={step} | llm_calls={llm_calls} | tool_calls={tool_calls} | "
              f"errors={errors} | dung_boi={dung_boi} | {elapsed:.2f}s")

    return {
        "question": user_query,
        "final_answer": final_answer,
        "steps": step,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "errors": errors,
        "dung_boi": dung_boi,
        "elapsed": elapsed,
        "trace": trace,
    }


def run_react_on_all_cases(tests, provider):
    """Chạy ReAct Agent trên toàn bộ test cases của Role 1 (checklist Mốc 3)."""
    print("\n" + "=" * 70)
    print("🤖 MỐC 3 — CHẠY REACT AGENT TRÊN TOÀN BỘ TEST CASES")
    print("=" * 70)

    ket_qua = []
    for case in tests:
        print("\n" + "-" * 70)
        print(f"🧪 Test Case #{case['id']} — {case.get('category', '')}")
        print(f"🎯 Kỳ vọng: {case.get('expected_behavior', '')}")
        r = run_react_agent(case["question"], provider)
        r["id"] = case["id"]
        r["category"] = case.get("category", "")
        r["expected_behavior"] = case.get("expected_behavior", "")
        ket_qua.append(r)

    return ket_qua


def xuat_trace_react(ket_qua, provider_name: str, model_name: str):
    """Ghi trace ReAct ra docs/react_trace.md cho Role 5 (không đụng trace_eval.md)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    thu_muc = os.path.join(base_dir, "docs", "auto")
    os.makedirs(thu_muc, exist_ok=True)
    duong_dan = os.path.join(thu_muc, "react_raw.md")

    dong = [
        "# 🤖 TRACE LOG REACT AGENT (Mốc 3)\n\n",
        "> File do `python src/app.py` sinh tự động — đừng sửa tay.\n",
        "> Role 5 copy sang `docs/trace_eval.md` rồi chấm điểm từng case.\n\n",
        f"* **Provider**: `{provider_name}` · **Model**: `{model_name}`\n",
        f"* **Thời điểm chạy**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"* **Guardrails**: `MAX_ITERATIONS={MAX_ITERATIONS}`\n\n---\n",
    ]
    for r in ket_qua:
        dong.append(f"\n## Test Case #{r['id']} — {r['category']}\n\n")
        dong.append(f"**Câu hỏi**: {r['question']}\n\n")
        dong.append(f"**Kỳ vọng**: {r['expected_behavior']}\n\n")
        dong.append("**Trace đầy đủ**:\n\n```text\n")
        dong.append(f"Question: {r['question']}\n\n")
        for b in r["trace"]:
            if b.get("thought"):
                dong.append(f"Thought: {b['thought']}\n")
            if b.get("action"):
                dong.append(f"Action: {b['action']}\n")
            if b.get("observation"):
                dong.append(f"Observation: {b['observation']}\n")
            if b.get("final_answer"):
                dong.append(f"Final Answer: {b['final_answer']}\n")
            dong.append("\n")
        if r["dung_boi"] != "final_answer":
            dong.append(f"[GUARDRAIL] Dừng bởi: {r['dung_boi']}\n")
            dong.append(f"Safe Fallback: {r['final_answer']}\n")
        dong.append("```\n\n")
        dong.append(f"* **Telemetry**: `steps={r['steps']}` · `llm_calls={r['llm_calls']}` · "
                    f"`tool_calls={r['tool_calls']}` · `errors={r['errors']}` · "
                    f"`dung_boi={r['dung_boi']}` · `{r['elapsed']:.2f}s`\n")
        dong.append("* **Chấm điểm 0-2đ** (Role 5 điền): Factual `_` · Grounding `_` · "
                    "Tool selection `_` · Termination `_`\n")
        dong.append("\n---\n")

    with open(duong_dan, "w", encoding="utf-8") as f:
        f.write("".join(dong))
    return duong_dan


# =============================================================================
# 💬 CHẾ ĐỘ CHAT TỰ DO — phục vụ MỐC 4 (Cross-Audit)
# Nhóm bạn gõ thẳng câu bẫy vào đây để "tấn công" Agent ngay trên máy chiếu,
# thay vì phải sửa config/test_cases.json rồi chạy lại cả bộ test (tốn quota).
# =============================================================================
def run_chat_mode(provider):
    """Vòng lặp hỏi đáp trực tiếp. Mặc định chạy ReAct Agent."""
    print("\n" + "=" * 70)
    print("💬 CHẾ ĐỘ CHAT TỰ DO — dùng cho Mốc 4 (Chấm chéo / Tấn công Agent)")
    print("=" * 70)
    print("Gõ câu hỏi rồi Enter. Các lệnh đặc biệt:")
    print("   /bot <câu hỏi>   — chạy Chatbot Baseline (không tool)")
    print("   /so  <câu hỏi>   — chạy CẢ HAI để so sánh trực tiếp")
    print("   /tools           — xem lại danh sách tool đang có")
    print("   /thoat           — kết thúc phiên chat")
    print("(Không gõ lệnh gì thì mặc định chạy ReAct Agent.)\n")

    while True:
        try:
            dong = input("Bạn ➜ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not dong:
            continue

        lenh = dong.lower()
        if lenh in ("/thoat", "/exit", "/quit", "exit", "quit", "thoat"):
            break
        if lenh in ("/tools", "/tool"):
            kiem_tra_tool_registry()
            continue

        if lenh.startswith("/bot"):
            cau_hoi = dong[4:].strip()
            if not cau_hoi:
                print("⚠️ Thiếu câu hỏi. Ví dụ: /bot Chính sách đổi trả bao lâu?")
                continue
            run_baseline_chatbot(cau_hoi, provider)

        elif lenh.startswith("/so"):
            cau_hoi = dong[3:].strip()
            if not cau_hoi:
                print("⚠️ Thiếu câu hỏi. Ví dụ: /so Kiểm tra đơn ORD1001")
                continue
            b = run_baseline_chatbot(cau_hoi, provider)
            a = run_react_agent(cau_hoi, provider)
            print("\n📊 SO SÁNH NHANH")
            print(f"   Chatbot : tool_calls=0 · {b['elapsed']:.2f}s")
            print(f"   Agent   : tool_calls={a['tool_calls']} · steps={a['steps']} · "
                  f"dừng bởi={a['dung_boi']} · {a['elapsed']:.2f}s")

        else:
            run_react_agent(dong, provider)

        print()

    print("👋 Kết thúc phiên chat.")


if __name__ == "__main__":
    # --chat: bỏ qua bộ test, vào thẳng chế độ hỏi đáp trực tiếp (Mốc 4).
    che_do_chat = "--chat" in sys.argv

    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    # Smoke test Mốc 1: xác nhận tools.py của Role 2 nạp được
    kiem_tra_tool_registry()

    if che_do_chat:
        run_chat_mode(provider)
        sys.exit(0)

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

    # ---------- MỐC 3: ReAct Agent trên toàn bộ test cases ----------
    ket_qua_agent = run_react_on_all_cases(tests, provider)

    duong_dan_trace = xuat_trace_react(ket_qua_agent, provider.__class__.__name__, model_name)

    # ---------- Bảng so sánh Chatbot vs Agent ----------
    print("\n" + "=" * 70)
    print("📊 BẢNG SO SÁNH: CHATBOT BASELINE vs REACT AGENT")
    print("=" * 70)
    print(f"{'Case':<6}{'Bot tools':<11}{'Agent tools':<13}{'Steps':<7}"
          f"{'Dừng bởi':<26}{'Bot(s)':<9}{'Agent(s)':<9}")
    print("-" * 70)
    for b, a in zip(ket_qua_baseline, ket_qua_agent):
        print(f"#{a['id']:<5}{b['tool_calls']:<11}{a['tool_calls']:<13}{a['steps']:<7}"
              f"{a['dung_boi']:<26}{b['elapsed']:<9.2f}{a['elapsed']:<9.2f}")
    print("-" * 70)
    print(f"{'TỔNG':<6}{sum(b['tool_calls'] for b in ket_qua_baseline):<11}"
          f"{sum(a['tool_calls'] for a in ket_qua_agent):<13}"
          f"{sum(a['steps'] for a in ket_qua_agent):<7}{'':<26}"
          f"{sum(b['elapsed'] for b in ket_qua_baseline):<9.2f}"
          f"{sum(a['elapsed'] for a in ket_qua_agent):<9.2f}")

    print(f"\n📝 Trace ReAct đã ghi ra: {os.path.relpath(duong_dan_trace, os.getcwd())}")
    print("   ➜ Role 5 copy sang docs/trace_eval.md để chấm điểm.")
