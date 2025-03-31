/** @odoo-module */

import { registry } from "@web/core/registry";
// Thêm onMounted và useRef từ owl
const { Component, onWillStart, onMounted, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets";

export class ExternalLibraries extends Component {
    setup() {
        // Sử dụng useRef để tham chiếu đến input element trong template
        this.inputRef = useRef("phoneInput");

        onWillStart(async () => {
            // Load cả JS và CSS. Chờ cả hai hoàn thành.
            await Promise.all([
                loadJS("https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/js/intlTelInput.min.js"),
                // Load CSS đã được khai báo trong manifest, nhưng load ở đây đảm bảo thứ tự nếu cần
                // Hoặc bạn có thể bỏ qua loadCSS ở đây nếu đã khai báo trong manifest và không cần chờ đợi cụ thể
                // loadCSS("https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/css/intlTelInput.css")
            ]);
        });

        onMounted(() => {
            // Khởi tạo thư viện sau khi component đã được gắn vào DOM
            if (this.inputRef.el) {
                // window.intlTelInput là cách thư viện này thường đăng ký global
                window.intlTelInput(this.inputRef.el, {
                    // Các tùy chọn của intl-tel-input (ví dụ)
                    utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/js/utils.js",
                    initialCountry: "auto",
                    geoIpLookup: callback => {
                      fetch("https://ipapi.co/json")
                        .then(res => res.json())
                        .then(data => callback(data.country_code))
                        .catch(() => callback("us"));
                    },
                });
                console.log("intl-tel-input initialized!");
            } else {
                console.error("Phone input element not found!");
            }
        });
    }
}

ExternalLibraries.template = "custom_owl_module.ExternalLibraries"; // Cập nhật tên template nếu cần

registry.category("actions").add("owl.ExternalLibraries", ExternalLibraries); // Giữ nguyên key này nếu action XML dùng nó