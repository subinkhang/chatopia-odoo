from odoo import models, fields

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
    created_at = fields.Datetime(string="Created At")
    is_read = fields.Boolean(string="Is Read", default=False)
    
    