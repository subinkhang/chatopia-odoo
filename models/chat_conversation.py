from odoo import models, fields

class ChatConversation(models.Model):
    _name = 'chatopia.conversation'
    _description = 'Chat Conversation'

    name = fields.Char(string='Conversation Name')
    inbox = fields.Char(string='Inbox')
    message_ids = fields.One2many('chatopia.message', 'conversation_id', string='Messages')