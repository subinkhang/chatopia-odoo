from odoo import models, fields, api
import pytz
from datetime import datetime, timedelta

class ChatMessage(models.Model):
    _name = 'chatopia.message'
    _description = 'Chat Message'

    # ID do Odoo tự cấp (không cần khai báo)
    chatwoot_message_id = fields.Integer(string="Chatwoot Message ID")  # ID từ Chatwoot
    inbox_id = fields.Integer(string="Inbox ID")  # ID inbox từ Chatwoot
    chatwoot_conversation_id = fields.Integer(string="Chatwoot Conversation ID")  # ID conversation từ Chatwoot để nối
    sender = fields.Char(string="Sender")  # Tên sender, tương tự conversation
    content = fields.Text(string="Content")  # Nội dung tin nhắn
    conversation_id = fields.Many2one('chatopia.conversation', string="Conversation")  # Liên kết với conversation trong Odoo
    
    message_type = fields.Selection([('user', 'User'), ('admin', 'Admin')], string="Message Type")
    # created_at = fields.Datetime(string="Created At")
    # is_read = fields.Boolean(string="Is Read", default=False)
    
    # # Thêm để làm UI messenger
    # sender_avatar = fields.Binary(compute='_compute_sender_avatar', string="Sender Avatar")
    # display_time = fields.Char(string="Display Time", compute='_compute_display_time')
    
    # --- Phương thức Compute cho Sender Avatar ---
    # @api.depends('message_type', 'conversation_id.contact_id.image_128')
    # def _compute_sender_avatar(self):
    #     # Lấy avatar user Odoo hiện tại một lần để tối ưu
    #     # Lưu ý: self.env.user có thể không đúng trong mọi ngữ cảnh (ví dụ cron job), cần xem xét kỹ
    #     admin_avatar = self.env.user.image_128 # Lấy avatar của admin/agent (người dùng Odoo)
    #     for msg in self:
    #         if msg.message_type == 'admin':
    #             # Với tin nhắn admin, không cần hiển thị avatar (theo CSS đã làm)
    #             # nhưng nếu muốn có thể gán avatar user Odoo
    #             msg.sender_avatar = admin_avatar # Hoặc False nếu không muốn lưu trữ/tính toán
    #         elif msg.message_type == 'user' and msg.conversation_id.contact_id:
    #             # Với tin nhắn user, lấy avatar từ contact liên quan đến conversation
    #             msg.sender_avatar = msg.conversation_id.contact_avatar
    #         else:
    #             msg.sender_avatar = False # Không có avatar

    # # --- Phương thức Compute cho Display Time (Tương tự last_message_display_time) ---
    # @api.depends('created_at')
    # def _compute_display_time(self):
    #     """ Tính toán chuỗi thời gian hiển thị thân thiện cho từng tin nhắn """
    #     now_utc = datetime.now(pytz.utc)
    #     user_tz = pytz.timezone(self.env.user.tz or 'UTC')

    #     for msg in self:
    #         display_time = ""
    #         if msg.created_at:
    #             msg_time_user = msg.created_at.astimezone(user_tz)
    #             now_user = now_utc.astimezone(user_tz)
    #             delta = now_user - msg_time_user

    #             # Logic tương tự như _compute_last_message_display_time
    #             # Bạn có thể tạo một hàm helper dùng chung nếu muốn
    #             if delta < timedelta(minutes=1):
    #                 display_time = _("just now")
    #             elif delta < timedelta(hours=1):
    #                 minutes = int(delta.total_seconds() / 60)
    #                 display_time = _("%d phút") % minutes
    #             elif msg_time_user.date() == now_user.date():
    #                 display_time = msg_time_user.strftime("%H:%M")
    #             elif msg_time_user.date() == (now_user - timedelta(days=1)).date():
    #                 display_time = _("Hôm qua %H:%M") % msg_time_user.strftime("%H:%M") # Thêm giờ cho ngày hôm qua
    #             else:
    #                 display_time = msg_time_user.strftime("%d/%m/%Y %H:%M") # Hiển thị đầy đủ cho tin cũ

    #         msg.display_time = display_time