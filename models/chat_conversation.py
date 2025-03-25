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
    
    message_content = fields.Text(string="Message Content")
    # message_to_send= fields.Html(string='Message to Send')

    def send_message_to_chatwoot(self):
        # Giả sử bạn đã có account_id và api_access_token
        chatwoot_url = f"https://app.chatwoot.com/api/v1/accounts/114179/conversations/1/messages"
        # chatwoot_url = f"https://app.chatwoot.com/public/api/v1/inboxes/vXLWbfuSdPQUmGBTx6LRQXp5/contacts/47167d3a-95ab-426e-a0d8-67e7dea74a80/conversations/20/messages"

        headers = {
            "Content-Type": "application/json",
            "api_access_token": "vXLWbfuSdPQUmGBTx6LRQXp5"  # Thay bằng token thật
        }
        payload = {
            "content": self.message_content,
            "message_type": "outgoing"
        }
        response = requests.post(chatwoot_url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            # Xóa nội dung sau khi gửi thành công (tùy chọn)
            self.message_content = False
            return True
        else:
            raise Exception(f"Gửi tin nhắn thất bại! Mã lỗi: {response.status_code}, Nội dung: {response.text}")