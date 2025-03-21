from odoo import models, fields

class ChatMessage(models.Model):
    _name = 'chatopia.message'
    _description = 'Chat Message'

    conversation_id = fields.Many2one('chatopia.conversation', string='Conversation')
    sender = fields.Char(string='Sender')
    content = fields.Text(string='Content')