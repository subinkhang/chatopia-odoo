from odoo import models, fields

class ChatConversation(models.Model):
    _name = 'chatopia.conversation'
    _description = 'Chat Conversation'
    
    name = fields.Char(string="Conversation Name")
    chatwoot_conversation_id = fields.Integer(string="Chatwoot Conversation ID")  # ID từ Chatwoot
    inbox_name = fields.Char(string="Inbox Name")  # Tên inbox
    sender_name = fields.Char(string="Sender Name")  # Tên sender, nối với contact qua x_chatwoot_id
    message_ids = fields.One2many('chatopia.message', 'conversation_id', string="Messages")  # Nối với messages
    contact_id = fields.Many2one('res.partner', string="Contact")  # Liên kết với res.partner