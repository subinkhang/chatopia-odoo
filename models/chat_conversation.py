from odoo import models, fields, api, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class ChatConversation(models.Model):
    _name = 'chatopia.conversation'
    _description = 'Chat Conversation'

    name = fields.Char(string="Conversation Name")
    chatwoot_conversation_id = fields.Integer(string="Chatwoot Conversation ID")  # ID từ Chatwoot
    inbox_name = fields.Char(string="Inbox Name")  # Tên inbox
    sender_name = fields.Char(string="Sender Name")  # Tên sender, nối với contact qua x_chatwoot_id
    message_ids = fields.One2many('chatopia.message', 'conversation_id', string="Messages")  # Nối với messages
    contact_id = fields.Many2one('res.partner', string="Contact")  # Liên kết với res.partner
    message_content = fields.Text(string="Message Content")  # Trường để nhập tin nhắn
    x_chatwoot_contact_id = fields.Char(string="Chatwoot Contact ID")  # Thêm trường này
    x_chatwoot_inbox_id = fields.Integer(string="Chatwoot Inbox ID")

    def send_message_to_chatwoot(self):
        """Gửi tin nhắn đến Chatwoot."""

        # Lấy tin nhắn cuối cùng (hoặc tin nhắn đang được soạn thảo)
        if self.message_content:
            content = self.message_content
            # Tạo một bản ghi message mới (hoặc bạn có thể lấy bản ghi cuối cùng trong message_ids)
            message = self.env['chatopia.message'].create({
                'conversation_id': self.id,
                'content': content,
                'sender': self.env.user.name,
                # 'inbox_id': 123,  # Điền giá trị inbox_id phù hợp
            })

            # Lấy thông tin người dùng Odoo hiện tại
            current_user = self.env.user
            odoo_sender_name = current_user.name
            # odoo_sender_email = current_user.email #có thể dùng email

            # Lấy các giá trị từ conversation
            # contact_id = self.contact_id.id if self.contact_id else None # Không cần lấy contact_id
            chatwoot_conversation_id = self.chatwoot_conversation_id
            x_chatwoot_contact_id = self.x_chatwoot_contact_id
            #x_chatwoot_inbox_id = self.x_chatwoot_inbox_id # Không dùng

            # Tạo URL Chatwoot
            chatwoot_url = f"https://app.chatwoot.com/api/v1/accounts/114179/conversations/{chatwoot_conversation_id}/messages"  # URL Chatwoot
            webhook_url = "https://webhook.site/cc930969-497a-484b-a9d4-fb9aa68e8a1e" # URL Webhook

            # Tạo payload (thêm sender)
            payload = {
                "content": content,
                "message_type": "outgoing",
                "is_from_odoo": True
            }

            # Log payload để kiểm tra
            _logger.info(f"Payload: {payload}")

            headers = {
                "Content-Type": "application/json",
                "api_access_token": "dfXCC3am6be9wXxKVv16n6iZ"  # Thay bằng token thật
            }

            # Danh sách các URL để gửi
            urls = [chatwoot_url, webhook_url]

            # Hàm gửi tin nhắn đến một URL
            def send_to_url(url, data, headers):
                try:
                    _logger.info(f"Sending message to URL: {url}")
                    response = requests.post(url, data=json.dumps(data), headers=headers)
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    _logger.info("Request successful")
                    _logger.info(f"Response Status Code: {response.status_code}")
                    _logger.info(f"Response Text: {response.text}")
                    return response.status_code == 200, response.text
                except requests.exceptions.RequestException as e:
                    _logger.error(f"Error sending request to {url}: {e}")
                    return False, str(e)

            # Gửi tin nhắn đến tất cả các URL
            results = []
            for url in urls:
                success, message = send_to_url(url, payload, headers if url == chatwoot_url else {"Content-Type": "application/json"})  # Chỉ sử dụng headers cho Chatwoot
                results.append((url, success, message))

            # Kiểm tra kết quả
            all_successful = all(success for url, success, message in results)

            # Xử lý kết quả và ném ngoại lệ nếu cần
            if all_successful:
                # Xóa nội dung sau khi gửi thành công
                self.message_content = False
                return True
            else:
                error_messages = "\n".join([f"URL: {url}, Success: {success}, Message: {message}" for url, success, message in results])
                raise Exception(f"Gửi tin nhắn thất bại đến một số URL! \n{error_messages}")

        else:
            _logger.warning("Không có nội dung tin nhắn để gửi.")
            return False