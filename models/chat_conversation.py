from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
import requests
import json
import logging
import re # Import thư viện regex để kiểm tra ID
import pytz
from datetime import datetime, timedelta

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
    contact_id = fields.Many2one('res.partner', string="Contact") # Đánh dấu là bắt buộc nếu logic yêu cầu phải có Contact
    message_content = fields.Text(string="Message Content") # Trường để nhập tin nhắn gửi đi
    x_chatwoot_contact_id = fields.Char(string="Chatwoot Contact ID") # Giữ lại nếu cần
    x_chatwoot_inbox_id = fields.Integer(string="Chatwoot Inbox ID") # Giữ lại nếu cần
    # last_message_content = fields.Text(string="Last Message Content")
    # last_message_time = fields.Datetime(string="Last Message Time")
    # avatar = fields.Binary(string="Avatar")
    
    # # Thêm để làm UI messenger
    # unread_count = fields.Integer(string="Unread Messages", compute='_compute_unread_count', store=True)
    # contact_avatar = fields.Binary(related='contact_id.image_128', string="Contact Avatar", readonly=True)
    # last_message_preview = fields.Text(related='last_message_content', string="Last Message Preview", readonly=True)
    # last_message_display_time = fields.Char(string="Last Message Display Time", compute='_compute_last_message_display_time')

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
        
    
    # --- Phương thức Compute cho Display Name ---
    # @api.depends('sender_name', 'contact_id', 'contact_id.name')
    # def _compute_display_name(self):
    #     for conv in self:
    #         conv.name = conv.contact_id.name if conv.contact_id else conv.sender_name or 'Unknown Conversation'

    # # --- Phương thức Compute cho Unread Count ---
    # @api.depends('message_ids.is_read', 'message_ids.message_type')
    # def _compute_unread_count(self):
    #     # Cần user hiện tại để biết tin nhắn nào là "đến" mình
    #     current_user_partner_id = self.env.user.partner_id.id
    #     for conv in self:
    #         # Đếm tin nhắn từ 'user' (không phải 'admin') và chưa đọc (is_read=False)
    #         # Logic is_read có thể cần phức tạp hơn tùy vào cách bạn đánh dấu đã đọc
    #         conv.unread_count = self.env['chatopia.message'].search_count([
    #             ('conversation_id', '=', conv.id),
    #             ('message_type', '=', 'user'), # Chỉ đếm tin nhắn của người dùng (không phải admin)
    #             ('is_read', '=', False) # Chỉ đếm tin chưa đọc
    #             # Thêm điều kiện check người nhận nếu cần thiết
    #         ])

    # # --- Phương thức Compute cho Last Message Info ---
    # @api.depends('message_ids.created_at', 'message_ids.content')
    # def _compute_last_message_info(self):
    #     for conv in self:
    #         # Tìm tin nhắn cuối cùng trong conversation này
    #         last_message = self.env['chatopia.message'].search([
    #             ('conversation_id', '=', conv.id)
    #         ], order='created_at desc', limit=1)

    #         if last_message:
    #             _logger.info(f"Conv {conv.id}: Found last message {last_message.id} at {last_message.created_at}")
    #             conv.last_message_time = last_message.created_at
    #             conv.last_message_content = html2plaintext(last_message.content or '')[:100] # Giữ nguyên giới hạn
    #         else:
    #             _logger.warning(f"Conv {conv.id}: No last message found.") # Log nếu không tìm thấy
    #             conv.last_message_time = False
    #             conv.last_message_content = ''

    # # --- Phương thức Compute cho Last Message Display Time ---
    # @api.depends('last_message_time')
    # def _compute_last_message_display_time(self):
    #     """ Tính toán chuỗi thời gian hiển thị thân thiện """
    #     now_utc = datetime.now(pytz.utc)
    #     user_tz = pytz.timezone(self.env.user.tz or 'UTC') # Lấy timezone của user

    #     for conv in self:
    #         display_time = ""
    #         if conv.last_message_time:
    #             last_time_user = conv.last_message_time.astimezone(user_tz)
    #             now_user = now_utc.astimezone(user_tz)
    #             delta = now_user - last_time_user

    #             if delta < timedelta(minutes=1):
    #                 display_time = _("just now")
    #             elif delta < timedelta(hours=1):
    #                 minutes = int(delta.total_seconds() / 60)
    #                 display_time = _("%d phút") % minutes # Ví dụ: "5 phút"
    #             elif last_time_user.date() == now_user.date():
    #                 display_time = last_time_user.strftime("%H:%M") # Ví dụ: "14:30"
    #             elif last_time_user.date() == (now_user - timedelta(days=1)).date():
    #                 display_time = _("Hôm qua")
    #             else:
    #                 # Hiển thị ngày/tháng cho tin nhắn cũ hơn
    #                 display_time = last_time_user.strftime("%d/%m") # Ví dụ: "20/05"
    #                 # Hoặc "%d thg %m" -> "20 thg 5"
    #                 # Hoặc "%d/%m/%Y" nếu muốn cả năm

    #         conv.last_message_display_time = display_time
            
            
    @api.model # Dùng @api.model vì không cần self cụ thể, thao tác trên env
    def get_conversations_data(self, domain=None, fields_list=None):
        _logger.info("RPC: get_conversations_data called")
        try:
            # Chỉ yêu cầu đọc các trường hiện có và cần thiết ban đầu
            required_fields = ['id', 'name'] # Chỉ cần ID và Name (đã gán trong mock)

            conversations = self.search(domain or [])
            conv_data = conversations.read(required_fields)

            _logger.info(f"RPC: get_conversations_data returning {len(conv_data)} conversations.")
            _logger.warning(f"RPC: get_conversations_data PRE-RETURN data: {conv_data}")
            return conv_data
        except AccessError as ae:
            _logger.error(f"RPC: get_conversations_data AccessError: {ae}", exc_info=True)
            raise
        except Exception as e:
            _logger.error(f"RPC: get_conversations_data failed: {e}", exc_info=True)
            raise UserError(_("Could not load conversation list. Please try again."))

    @api.model
    def get_messages_data(self, conversation_id):
        """
        Lấy danh sách tin nhắn cho một cuộc trò chuyện cụ thể và đánh dấu đã đọc.
        Được gọi từ JavaScript qua ORM.
        """
        _logger.info(f"RPC: get_messages_data called for conversation_id: {conversation_id}")
        if not conversation_id:
            return []

        try:
            conversation = self.browse(conversation_id)
            conversation.ensure_one() # Đảm bảo conversation tồn tại

            # Các trường cần thiết cho frontend message view
            message_fields = [
                'id',
                'content',
                'message_type',
                'sender_avatar', # Computed
                'display_time',  # Computed
                'created_at',    # Để sắp xếp nếu cần (mặc dù _order đã có)
                'is_read',       # Để xử lý logic đánh dấu đã đọc
            ]

            # Đọc tin nhắn, sắp xếp theo thời gian tạo tăng dần (mặc định từ _order)
            messages = conversation.message_ids.read(message_fields)

            # --- Đánh dấu các tin nhắn chưa đọc từ 'user' là đã đọc ---
            messages_to_mark_read = conversation.message_ids.filtered(
                lambda m: m.message_type == 'user' and not m.is_read
            )
            if messages_to_mark_read:
                _logger.info(f"Marking {len(messages_to_mark_read)} messages as read for conv {conversation_id}")
                messages_to_mark_read.write({'is_read': True})
                # Trigger tính toán lại unread_count cho conversation này
                # Odoo thường tự động làm, nhưng có thể cần gọi self.env.invalidate_all() hoặc cơ chế khác nếu không cập nhật ngay
                # self.env.add_to_compute(self._fields['unread_count'], conversation)


            _logger.info(f"RPC: get_messages_data returning {len(messages)} messages for conv {conversation_id}.")
            return messages

        except AccessError as ae:
             _logger.error(f"RPC: get_messages_data AccessError for conv {conversation_id}: {ae}", exc_info=True)
             raise
        except Exception as e:
            _logger.error(f"RPC: get_messages_data failed for conv {conversation_id}: {e}", exc_info=True)
            raise UserError(_("Không thể tải tin nhắn. Vui lòng thử lại."))

    @api.model
    def post_message(self, conversation_id, message_content):
        """
        Tạo tin nhắn mới từ admin (Odoo user) và gửi đi (nếu cần).
        Được gọi từ JavaScript qua ORM.
        """
        _logger.info(f"RPC: post_message called for conversation_id: {conversation_id} with content: '{message_content[:50]}...'")
        if not conversation_id or not message_content:
            raise UserError(_("Thiếu thông tin cuộc trò chuyện hoặc nội dung tin nhắn."))

        try:
            conversation = self.browse(conversation_id)
            conversation.ensure_one()

            # Tạo record tin nhắn mới
            message_vals = {
                'conversation_id': conversation_id,
                'content': message_content,
                'message_type': 'admin', # Tin nhắn từ Odoo user là admin/agent
                'is_read': True, # Tin nhắn mình gửi thì coi như đã đọc
                # 'created_at': fields.Datetime.now(), # Odoo tự xử lý default
                # Sender sẽ là user Odoo hiện tại (có thể không cần lưu tường minh nếu dùng message_type)
            }
            new_message = self.env['chatopia.message'].create(message_vals)
            _logger.info(f"Created new message with id: {new_message.id}")

            # --- !!! QUAN TRỌNG: Gọi API gửi tin nhắn ra bên ngoài (Zalo, Messenger,...) ---
            # Đây là nơi bạn cần tích hợp logic gọi API của nền tảng tương ứng
            try:
                # Ví dụ gọi một phương thức khác để gửi (bạn cần tự định nghĩa phương thức này)
                # self._send_message_via_external_api(conversation, new_message.content)
                _logger.info(f"Placeholder: Message {new_message.id} content would be sent via external API here.")
                pass # Bỏ qua nếu chưa tích hợp
            except Exception as api_error:
                # Xử lý lỗi nếu không gửi được ra ngoài
                _logger.error(f"Failed to send message {new_message.id} via external API: {api_error}", exc_info=True)
                # Có thể bạn muốn báo lỗi cho user hoặc không xóa tin nhắn đã tạo trong Odoo
                # raise UserError(_("Gửi tin nhắn ra bên ngoài thất bại: %s") % api_error)


            # --- Thông báo real-time qua Odoo Bus (nếu dùng) ---
            # channel_name = f'chatopia_conversation_{conversation_id}' # Hoặc kênh chung
            # message_data_for_bus = {
            #     'id': new_message.id,
            #     'content': new_message.content,
            #     'message_type': new_message.message_type,
            #     'sender_avatar': new_message.sender_avatar, # Cần tính toán nếu muốn gửi avatar admin
            #     'display_time': new_message.display_time, # Cần tính toán
            #     'created_at': new_message.created_at.isoformat(), # Chuẩn ISO cho JS
            #     'conversation_id': conversation_id,
            # }
            # try:
            #      self.env['bus.bus']._sendone(channel_name, 'chatopia_new_message', message_data_for_bus)
            #      _logger.info(f"Sent bus notification for new message {new_message.id} on channel {channel_name}")
            # except Exception as bus_error:
            #      _logger.error(f"Failed to send bus notification for message {new_message.id}: {bus_error}", exc_info=True)


            # --- Trả về dữ liệu tin nhắn mới tạo cho frontend ---
            # Đọc các trường cần thiết mà frontend mong đợi
            message_fields_to_return = [
                 'id', 'content', 'message_type', 'sender_avatar', 'display_time', 'created_at'
            ]
            # Cần đảm bảo các trường computed (sender_avatar, display_time) được tính toán
            new_message_data = new_message.read(message_fields_to_return)[0]

            # Định dạng lại Datetime thành chuỗi ISO nếu cần cho JS
            if isinstance(new_message_data.get('created_at'), fields.datetime):
                 new_message_data['created_at'] = new_message_data['created_at'].isoformat() + 'Z' # Thêm Z cho UTC

            _logger.info(f"RPC: post_message successful for conv {conversation_id}.")
            return new_message_data

        except AccessError as ae:
             _logger.error(f"RPC: post_message AccessError for conv {conversation_id}: {ae}", exc_info=True)
             raise
        except Exception as e:
            _logger.error(f"RPC: post_message failed for conv {conversation_id}: {e}", exc_info=True)
            raise UserError(_("Không thể gửi tin nhắn. Vui lòng thử lại."))