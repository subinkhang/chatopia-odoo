from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
import re # Import thư viện regex để kiểm tra ID

_logger = logging.getLogger(__name__)

class ChatConversation(models.Model):
    _name = 'chatopia.conversation'
    _description = 'Chat Conversation'

    # --- Các trường hiện có ---
    name = fields.Char(string="Conversation Name")
    chatwoot_conversation_id = fields.Integer(string="Chatwoot Conversation ID") # Giữ lại nếu cần
    inbox_name = fields.Char(string="Inbox Name")
    sender_name = fields.Char(string="Sender Name")
    message_ids = fields.One2many('chatopia.message', 'conversation_id', string="Messages")
    contact_id = fields.Many2one('res.partner', string="Contact", required=True) # Đánh dấu là bắt buộc nếu logic yêu cầu phải có Contact
    message_content = fields.Text(string="Message Content") # Trường để nhập tin nhắn gửi đi
    x_chatwoot_contact_id = fields.Char(string="Chatwoot Contact ID") # Giữ lại nếu cần
    x_chatwoot_inbox_id = fields.Integer(string="Chatwoot Inbox ID") # Giữ lại nếu cần
    last_message_content = fields.Text(string="Last Message Content")
    last_message_time = fields.Datetime(string="Last Message Time")
    avatar = fields.Binary(string="Avatar")

    # --- KHÔNG cần trường zalo_user_id nữa ---
    # zalo_user_id = fields.Char(string="Zalo User ID")

    def _extract_zalo_user_id_from_email(self):
        """Trích xuất Zalo User ID từ trường email của contact."""
        self.ensure_one()
        if not self.contact_id:
            _logger.warning(f"Cuộc hội thoại ID {self.id} không có liên kết Contact.")
            return None, _("Cuộc hội thoại này chưa được liên kết với một Liên hệ (Contact).")
        
        contact_email = self.contact_id.email
        if not contact_email:
            _logger.warning(f"Contact ID {self.contact_id.id} không có địa chỉ email.")
            return None, _("Liên hệ '%s' không có địa chỉ email được thiết lập.") % self.contact_id.display_name

        # Tách ID dựa trên định dạng "[zalo_user_id]@gmail.com"
        # Sử dụng split và kiểm tra chặt chẽ hơn
        email_parts = contact_email.split('@gmail.com')
        if len(email_parts) == 2 and email_parts[1] == '' and email_parts[0]:
            # Kiểm tra xem phần đầu có phải là chuỗi số hay không
            zalo_user_id = email_parts[0]
            if re.match(r'^\d+$', zalo_user_id): # Đảm bảo ID chỉ chứa số
                _logger.info(f"Trích xuất thành công Zalo User ID: {zalo_user_id} từ email: {contact_email}")
                return zalo_user_id, None # Trả về ID và không có lỗi
            else:
                _logger.warning(f"Phần trước '@gmail.com' trong email '{contact_email}' không phải là ID hợp lệ (chỉ chứa số).")
                return None, _("Định dạng email của liên hệ '%s' không đúng chuẩn để lấy Zalo User ID (phần trước @gmail.com phải là số). Email hiện tại: %s") % (self.contact_id.display_name, contact_email)
        else:
            _logger.warning(f"Email '{contact_email}' của Contact ID {self.contact_id.id} không đúng định dạng '[zalo_user_id]@gmail.com'.")
            return None, _("Email của liên hệ '%s' không đúng định dạng '[zalo_user_id]@gmail.com'. Email hiện tại: %s") % (self.contact_id.display_name, contact_email)


    def send_message_to_zalo(self):
        """Gửi tin nhắn đến Zalo OA, lấy User ID từ email của Contact."""
        self.ensure_one() # Đảm bảo hàm chạy trên 1 bản ghi duy nhất

        if not self.message_content:
            # Không cần log warning vì có thể chỉ là bấm nhầm nút
            raise UserError(_("Vui lòng nhập nội dung tin nhắn trước khi gửi."))

        # --- Lấy Zalo User ID từ Contact ---
        recipient_zalo_id, error_message = self._extract_zalo_user_id_from_email()

        if not recipient_zalo_id:
            # error_message đã được tạo trong hàm _extract_zalo_user_id_from_email
            raise UserError(error_message)

        # --- Lấy thông tin cần thiết ---
        content_to_send = self.message_content

        # --- Cấu hình Zalo API ---
        zalo_api_url = "https://openapi.zalo.me/v3.0/oa/message/cs"
        # Lấy token từ cấu hình hệ thống (KHUYẾN NGHỊ)
        # zalo_access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.oa.access_token')
        zalo_access_token = "ZfQ_LQbJTXUAahTTgrHu5OsIkLcs3JbjsPoXGOOc7shhhw91iX8VNkgatXAREryP_xBXDA1iRmlZ_VShWpbz1A2vx2620qCgyBpC4j8WMLcIXD9PwGv7IwsCz5hSArHk_FNKJgCrHrxHa-rsjHf_MyARvLkp6IL9qvpgLuScObx5lV9CiGLYHv37_4MtGtrimzRTBxH1O13AsyCIwsSCNx3BW0Zs2Wv2hi-aPuzRS7JSXRX_YXKaIEwMb7pB8m1fkAB1IjrbTtkxeCfbvJOAQiQAd4Yu9WW5bR6v4imET2BWlw0DeXmh7VAh_mgUFMC8_uZ3CPDA32dSZu4bg0OD1ecca1hcO2DDfFUPMk4zLrcXzvPgn6iuHvNHy0t6K5eGZEMJ8kCZ1mUFY8mS-HGY0S6hgYAR36OV5VFvUgzBVXi" # !!! THAY BẰNG ACCESS TOKEN THẬT CỦA BẠN !!!

        if not zalo_access_token:
            _logger.error("Thiếu Zalo Access Token trong cấu hình hệ thống.")
            raise UserError(_("Chưa cấu hình Zalo Access Token trong Hệ thống > Thông số kỹ thuật > Tham số hệ thống (vd: zalo.oa.access_token)."))

        # --- Chuẩn bị Payload và Headers ---
        payload = {
            "recipient": {
                "user_id": recipient_zalo_id
            },
            "message": {
                "text": content_to_send
            }
        }

        headers = {
            "Content-Type": "application/json",
            "access_token": zalo_access_token
        }

        _logger.info(f"Chuẩn bị gửi tin nhắn Zalo đến User ID: {recipient_zalo_id} (trích xuất từ contact {self.contact_id.id})")
        _logger.debug(f"Zalo Payload: {json.dumps(payload)}")

        # --- Gửi Request đến Zalo API ---
        try:
            _logger.info(f"Đang gửi request đến Zalo API: {zalo_api_url}")
            response = requests.post(zalo_api_url, data=json.dumps(payload), headers=headers, timeout=15)
            response.raise_for_status()

            response_data = response.json()
            _logger.info("Gửi request Zalo thành công.")
            _logger.info(f"Zalo Response Status Code: {response.status_code}")
            _logger.info(f"Zalo Response Body: {response_data}")

            zalo_error_code = response_data.get('error')
            zalo_error_message = response_data.get('message', '')
            if zalo_error_code is not None and zalo_error_code != 0:
                _logger.error(f"Zalo API trả về lỗi: Code={zalo_error_code}, Message='{zalo_error_message}' cho User ID: {recipient_zalo_id}")
                # Cung cấp thêm ngữ cảnh lỗi cho người dùng
                error_detail = f" (User ID: {recipient_zalo_id}, Lỗi Zalo: {zalo_error_message})"
                raise UserError(_("Zalo API báo lỗi khi gửi tin nhắn: %s%s") % (zalo_error_message, error_detail))

            # --- Xử lý sau khi gửi thành công ---
            self.env['chatopia.message'].create({
                'conversation_id': self.id,
                'content': content_to_send,
                'sender': self.env.user.name or 'Odoo User',
                'message_type': 'admin',
                'created_at': fields.Datetime.now(),
                # Cân nhắc lưu thêm zalo_message_id nếu Zalo API trả về
                # 'external_message_id': response_data.get('data', {}).get('message_id')
            })

            self.message_content = False
            _logger.info(f"Đã gửi tin nhắn thành công đến Zalo User ID: {recipient_zalo_id}")

            # (Tùy chọn) Hiển thị thông báo thành công ngắn gọn
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': _('Thành công'),
            #         'message': _('Đã gửi tin nhắn đến Zalo thành công.'),
            #         'sticky': False, # Thông báo tự biến mất
            #         'type': 'success', # Màu xanh
            #     }
            # }
            return True # Hoặc trả về True đơn giản

        except requests.exceptions.Timeout as e:
            _logger.error(f"Lỗi gửi tin nhắn Zalo (Timeout) đến User ID {recipient_zalo_id}: {e}")
            raise UserError(_("Gửi tin nhắn tới Zalo thất bại do hết thời gian chờ. Vui lòng thử lại."))
        except requests.exceptions.HTTPError as e:
            error_details = e.response.text
            status_code = e.response.status_code
            try:
                error_json = e.response.json()
                error_details = f"Code: {error_json.get('error', 'N/A')}, Message: {error_json.get('message', e.response.text)}"
            except json.JSONDecodeError:
                pass
            _logger.error(f"Lỗi gửi tin nhắn Zalo (HTTP Error {status_code}) đến User ID {recipient_zalo_id}: {error_details}")
            raise UserError(_("Gửi tin nhắn tới Zalo thất bại. Lỗi HTTP %s: %s (Kiểm tra Access Token hoặc User ID có thể không hợp lệ/không tồn tại)") % (status_code, error_details))
        except requests.exceptions.RequestException as e:
            _logger.error(f"Lỗi kết nối khi gửi tin nhắn Zalo đến User ID {recipient_zalo_id}: {e}")
            raise UserError(_("Gửi tin nhắn tới Zalo thất bại. Không thể kết nối tới Zalo API: %s") % e)
        except Exception as e:
            _logger.exception(f"Lỗi không xác định khi gửi tin nhắn Zalo đến User ID {recipient_zalo_id}:")
            raise UserError(_("Đã xảy ra lỗi không mong muốn khi gửi tin nhắn Zalo: %s") % e)