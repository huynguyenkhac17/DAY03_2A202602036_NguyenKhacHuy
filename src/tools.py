"""
Tool Registry & Schemas
=======================

Module này định nghĩa toàn bộ các tool mà ReAct Agent có thể gọi thông qua
Function Calling.

Mỗi tool cần:
- Có type hints đầy đủ.
- Có docstring mô tả rõ chức năng, tham số và giá trị trả về.
- Trả về chuỗi (str) để Agent có thể sử dụng trực tiếp trong quá trình suy luận.

Danh sách tool được đăng ký trong AVAILABLE_TOOLS sẽ được Agent
sử dụng để tìm kiếm và thực thi khi cần.
"""

# ORDERS = {
#     "ORD1001": {
#         "status": "Đã giao",
#         "item": "Tai nghe Bluetooth",
#         "placed_date": "2026-07-20",
#         "total": "1,250,000 VNĐ",
#     },
#     "ORD1002": {
#         "status": "Đang vận chuyển",
#         "item": "Bút máy tính",
#         "placed_date": "2026-07-24",
#         "total": "320,000 VNĐ",
#     },
#     "ORD1003": {
#         "status": "Chờ thanh toán",
#         "item": "Máy sấy tóc",
#         "placed_date": "2026-07-26",
#         "total": "2,980,000 VNĐ",
#     },
# }


def get_order_status(order_id: str) -> str:
    """
    Tra cứu thông tin chi tiết của một đơn hàng.

    Tool này nhận vào mã đơn hàng và trả về các thông tin gồm:
    - Trạng thái đơn hàng
    - Tên sản phẩm
    - Ngày đặt hàng
    - Tổng giá trị đơn hàng

    Args:
        order_id (str):
            Mã đơn hàng cần tra cứu (ví dụ: "ORD1001").

    Returns:
        str:
            Chuỗi mô tả thông tin đơn hàng nếu tìm thấy.
            Nếu không tìm thấy hoặc mã không hợp lệ sẽ trả về thông báo lỗi.
    """
    if not order_id or not str(order_id).strip():
        return "LỖI: Vui lòng cung cấp mã đơn hàng."

    order_id = str(order_id).strip().upper()

    order = ORDERS.get(order_id)

    if not order:
        return (
            f"LỖI: Không tìm thấy đơn hàng '{order_id}'. "
            "Vui lòng kiểm tra lại mã đơn."
        )

    return (
        f"Đơn hàng {order_id}:\n"
        f"- Trạng thái: {order['status']}\n"
        f"- Sản phẩm: {order['item']}\n"
        f"- Ngày đặt: {order['placed_date']}\n"
        f"- Tổng tiền: {order['total']}"
    )


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo yêu cầu đổi hoặc trả hàng.

    Tool này kiểm tra tính hợp lệ của đơn hàng và tạo một yêu cầu
    đổi/trả dựa trên lý do do khách hàng cung cấp.

    Args:
        order_id (str):
            Mã đơn hàng cần đổi/trả.

        reason (str):
            Lý do đổi/trả
            (ví dụ: "Sản phẩm bị lỗi", "Không đúng mô tả"...).

    Returns:
        str:
            Thông báo xác nhận nếu yêu cầu được tạo thành công,
            hoặc thông báo lỗi nếu dữ liệu không hợp lệ.
    """
    if not order_id or not str(order_id).strip():
        return "LỖI: Vui lòng cung cấp mã đơn hàng."

    if not reason or not str(reason).strip():
        return "LỖI: Vui lòng cho biết lý do đổi/trả."

    order_id = str(order_id).strip().upper()

    if order_id not in ORDERS:
        return (
            f"LỖI: Không tìm thấy đơn hàng '{order_id}'. "
            "Vui lòng kiểm tra lại mã đơn."
        )

    return (
        f"Yêu cầu đổi/trả cho đơn hàng {order_id} đã được ghi nhận.\n"
        f"Lý do: {reason}\n"
        "Trạng thái: Đang chờ xác nhận từ bộ phận hỗ trợ."
    )


def get_return_policy() -> str:
    """
    Trả về chính sách đổi/trả của cửa hàng.

    Tool này được sử dụng khi khách hàng hỏi về quy định đổi,
    trả hoặc hoàn tiền.

    Returns:
        str:
            Chuỗi mô tả các điều kiện đổi/trả cơ bản của cửa hàng.
    """
    return (
        "Chính sách đổi/trả:\n"
        "- Đơn hàng có thể đổi/trả trong vòng 7 ngày kể từ ngày nhận hàng.\n"
        "- Sản phẩm phải còn nguyên tem, hộp và chưa qua sử dụng.\n"
        "- Nếu sản phẩm lỗi hoặc giao sai, shop sẽ hỗ trợ miễn phí "
        "vận chuyển trả hàng."
    )

AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "create_return_request": create_return_request,
    "get_return_policy": get_return_policy,
}