/** @odoo-module */

// --- Import các thành phần cần thiết ---
import { Component, useState, onWillStart, onMounted, useRef, onPatched } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

// --- Định nghĩa và export class component ---
export class ChatopiaMessengerView extends Component {
    setup() {
        // --- Services ---
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.userService = useService("user"); // <<< Đã thêm user service
        // this.busService = useService("bus_service");

        // --- State ---
        this.state = useState({
            conversations: [],
            messages: [],
            activeConversationId: null,
            activeConversationInfo: null,
            isLoadingConversations: true,
            isLoadingMessages: false,
            // messageContent không cần thiết nếu dùng ref
        });

        // --- Refs ---
        this.messageInputRef = useRef("messageInput");
        this.messageWindowRef = useRef("messageWindow");

        // --- Lifecycle Hooks ---
        onWillStart(async () => {
            await this._loadConversations();
        });

        onMounted(() => {
            console.log("Chatopia Messenger Mounted (ESM)");
            // this._setupBusListeners();
        });

        onPatched(() => {
            this._scrollToBottom();
        });
    }

    // --- Các phương thức tùy chỉnh ---

    async _loadConversations() {
        this.state.isLoadingConversations = true;
        try {
            // Sử dụng this.userService.context
            const convData = await this.orm.call(
                'chatopia.conversation',
                'get_conversations_data',
                [[]],
                { context: this.userService.context } // <<< Đã sửa
            );
            this.state.conversations = convData.map(conv => ({
                ...conv,
                // avatar_src: conv.contact_avatar ? `data:image/png;base64,${conv.contact_avatar}` : '/web/static/src/img/placeholder.png',
            }));
        } catch (error) {
            console.error("Error loading conversations:", error);
            this.notification.add(_t("Failed to load conversations."), { type: 'danger' });
        } finally {
            this.state.isLoadingConversations = false;
        }
    }

    async _selectConversation(convId) {
        if (this.state.activeConversationId === convId || this.state.isLoadingMessages) { return; }
        this.state.activeConversationId = convId;
        this.state.isLoadingMessages = true;
        this.state.messages = [];
        this.state.activeConversationInfo = this.state.conversations.find(c => c.id === convId);
        try {
            // Sử dụng this.userService.context
            const messageData = await this.orm.call(
                'chatopia.conversation',
                'get_messages_data',
                [[convId]],
                { context: this.userService.context } // <<< Đã sửa
            );
            this.state.messages = messageData.map(msg => ({
                ...msg,
                // sender_avatar_src: msg.sender_avatar ? `data:image/png;base64,${msg.sender_avatar}` : '/web/static/src/img/placeholder.png',
            }));
            const convIndex = this.state.conversations.findIndex(c => c.id === convId);
            // if (convIndex !== -1) { this.state.conversations[convIndex].unread_count = 0; }
        } catch (error) {
            console.error(`Error loading messages for conversation ${convId}:`, error);
            this.notification.add(_t("Failed to load messages."), { type: 'danger' });
            this.state.activeConversationId = null;
            this.state.activeConversationInfo = null;
        } finally {
            this.state.isLoadingMessages = false;
        }
    }

    _handleInputKeyup(ev) {
        if (ev.key === 'Enter' && !ev.shiftKey && this.messageInputRef.el && this.messageInputRef.el.value.trim()) {
            ev.preventDefault();
            this._sendMessage();
        }
    }

    async _sendMessage() {
        if (!this.messageInputRef.el) return;
        const content = this.messageInputRef.el.value.trim();
        const convId = this.state.activeConversationId;
        if (!content || !convId || this.state.isLoadingMessages) { return; }

        const tempId = `temp_${Date.now()}`;
        this.state.messages.push({
            id: tempId, content: content, message_type: 'admin',
            // sender_avatar_src: '', display_time: _t("Sending..."), isOptimistic: true,
        });
        this.messageInputRef.el.value = '';

        try {
            // Sử dụng this.userService.context
            const newMessageData = await this.orm.call(
                'chatopia.conversation',
                'post_message',
                [[convId], content],
                { context: this.userService.context } // <<< Đã sửa
            );

            const messageIndex = this.state.messages.findIndex(m => m.id === tempId);
            if (messageIndex > -1) {
                this.state.messages.splice(messageIndex, 1, {
                    ...newMessageData,
                    // sender_avatar_src: newMessageData.sender_avatar ? `data:image/png;base64,${newMessageData.sender_avatar}` : '/web/static/src/img/placeholder.png',
                });
            } else {
                this.state.messages.push({
                    ...newMessageData,
                    // sender_avatar_src: newMessageData.sender_avatar ? `data:image/png;base64,${newMessageData.sender_avatar}` : '/web/static/src/img/placeholder.png',
                });
            }

            // const convIndex = this.state.conversations.findIndex(c => c.id === convId);
            // if (convIndex !== -1 && newMessageData) {
            //     this.state.conversations[convIndex].last_message_preview = newMessageData.content;
            //     this.state.conversations[convIndex].last_message_display_time = newMessageData.display_time;
            // }
        } catch (error) {
            console.error(`Error sending message to conversation ${convId}:`, error);
            this.notification.add(_t("Failed to send message."), { type: 'danger' });
            this.state.messages = this.state.messages.filter(m => m.id !== tempId);
        }
    }

    _scrollToBottom() {
        if (this.messageWindowRef.el) {
            this.messageWindowRef.el.scrollTop = this.messageWindowRef.el.scrollHeight;
        }
    }

    // --- Các hàm bus ---
    _setupBusListeners() { /* ... */ }
    _handleIncomingMessage(messageData) { /* ... */ }
    _handleConvUpdate(convData) { /* ... */ }

} // --- Kết thúc class ---

// --- Gán template ---
ChatopiaMessengerView.template = 'chatopia.MessengerView';

// --- Đăng ký action ---
registry.category("actions").add("chatopia_messenger_view", ChatopiaMessengerView);