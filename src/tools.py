"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

def get_order_status(order_id: str) -> str:
    """
    Tra cứu trạng thái và thông tin chi tiết của một đơn hàng.

    Args:
        order_id (str): Mã đơn hàng cần tra cứu (ví dụ: ORD1001)

    Returns:
        str: Thông tin trạng thái đơn hàng hoặc thông báo lỗi nếu không tìm thấy
    """
    if not order_id or not str(order_id).strip():
        return "LỖI: Vui lòng cung cấp mã đơn hàng."

    order_id = str(order_id).strip().upper()
    orders = {
        "ORD1001": {
            "status": "Đã giao",
            "item": "Tai nghe Bluetooth",
            "placed_date": "2026-07-20",
            "total": "1,250,000 VNĐ",
        },
        "ORD1002": {
            "status": "Đang vận chuyển",
            "item": "Bút máy tính",
            "placed_date": "2026-07-24",
            "total": "320,000 VNĐ",
        },
        "ORD1003": {
            "status": "Chờ thanh toán",
            "item": "Máy sấy tóc",
            "placed_date": "2026-07-26",
            "total": "2,980,000 VNĐ",
        },
    }

    order = orders.get(order_id)
    if not order:
        return f"LỖI: Không tìm thấy đơn hàng '{order_id}'. Vui lòng kiểm tra lại mã đơn."

    return (
        f"Đơn hàng {order_id}:\n"
        f"- Trạng thái: {order['status']}\n"
        f"- Sản phẩm: {order['item']}\n"
        f"- Ngày đặt: {order['placed_date']}\n"
        f"- Tổng tiền: {order['total']}"
    )


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo yêu cầu đổi/trả cho một đơn hàng đã giao.

    Args:
        order_id (str): Mã đơn hàng cần đổi/trả
        reason (str): Lý do đổi/trả (ví dụ: sản phẩm lỗi, không đúng mô tả)

    Returns:
        str: Thông báo xác nhận hoặc lỗi nếu đơn hàng không hợp lệ
    """
    if not order_id or not str(order_id).strip():
        return "LỖI: Vui lòng cung cấp mã đơn hàng."
    if not reason or not str(reason).strip():
        return "LỖI: Vui lòng cho biết lý do đổi/trả."

    order_id = str(order_id).strip().upper()
    if order_id != "ORD1001":
        return f"LỖI: Chỉ hỗ trợ tạo yêu cầu đổi/trả cho đơn hàng ORD1001 trong demo này."

    return (
        f"Yêu cầu đổi/trả cho đơn hàng {order_id} đã được ghi nhận.\n"
        f"Lý do: {reason}\n"
        f"Trạng thái: Đang chờ xác nhận từ bộ phận hỗ trợ"
    )


def get_return_policy() -> str:
    """
    Trả về chính sách đổi/trả cơ bản cho khách hàng.

    Returns:
        str: Chính sách đổi/trả ngắn gọn
    """
    return (
        "Chính sách đổi/trả:\n"
        "- Đơn hàng có thể đổi/trả trong vòng 7 ngày kể từ ngày nhận hàng.\n"
        "- Sản phẩm phải còn nguyên tem, hộp và chưa qua sử dụng.\n"
        "- Nếu sản phẩm lỗi hoặc giao sai, shop sẽ hỗ trợ miễn phí vận chuyển trả hàng."
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "create_return_request": create_return_request,
    "get_return_policy": get_return_policy,
}
