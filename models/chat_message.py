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
    
    # def send_message_to_chatwoot(self):
        # Lấy các giá trị từ conversation
        conversation = self.conversation_id
        contact_id = conversation.contact_id.id if conversation.contact_id else None
        sender_name = conversation.sender_name
        chatwoot_conversation_id = conversation.chatwoot_conversation_id
        inbox_name = conversation.inbox_name

        # Lấy giá trị từ message
        content = self.content
        inbox_id = self.inbox_id # Lấy inbox_id từ message

        # Tạo payload
        payload = {
            "content": content,
            "message_type": "outgoing",
            "contact_id": contact_id,
            "sender_name": sender_name,
            "chatwoot_conversation_id": chatwoot_conversation_id,
            "inbox_id": inbox_id,
            "inbox_name": inbox_name,
        }

        # Log payload để kiểm tra
        _logger.info(f"Payload: {payload}")

        # URL Webhook.site để test
        webhook_url = "	https://webhook.site/cc930969-497a-484b-a9d4-fb9aa68e8a1e"  # Thay 'your-unique-url' bằng URL webhook.site của bạn
        use_webhook = True  # Cờ để bật/tắt sử dụng webhook

        # URL Chatwoot thật
        chatwoot_url = f"https://app.chatwoot.com/api/v1/accounts/114179/conversations/{chatwoot_conversation_id}/messages"

        headers = {
            "Content-Type": "application/json",
            "api_access_token": "vXLWbfuSdPQUmGBTx6LRQXp5"  # Thay bằng token thật
        }
        try:
            if use_webhook:
                _logger.info("Using webhook.site for testing...")
                response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                _logger.info("Request to webhook.site successful")
                _logger.info(f"Webhook Response Status Code: {response.status_code}")
                _logger.info(f"Webhook Response Text: {response.text}")

            else:
                # Sử dụng URL Chatwoot ban đầu
                response = requests.post(chatwoot_url, data=json.dumps(payload), headers=headers)
                response.raise_for_status()
                _logger.info("Request to Chatwoot successful")

            if response.status_code == 200:
                return True
            else:
                raise Exception(f"Gửi tin nhắn thất bại! Mã lỗi: {response.status_code}, Nội dung: {response.text}")

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error sending request: {e}")
            raise Exception(f"Gửi tin nhắn thất bại! Lỗi: {e}")