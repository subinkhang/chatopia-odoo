{
    'name': 'Chatopia',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Omnichannel, centralized chat system',
    'description': """
        Chatopia is an omnichannel, centralized chat system.
    """,
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/chatopia_mock_data.xml',
        # 'views/chatopia_menu.xml',
        'views/chatopia_views.xml',
        'views/chatopia_actions.xml',
        'views/chatopia_menuitems.xml', 
        # 'views/external_libraries.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Thêm file JS và CSS/SCSS của bạn vào đây ở bước sau
            'chatopia/static/src/js/messenger_view.js',
            'chatopia/static/src/scss/messenger_view.scss',
            # Thêm CSS của thư viện ngoài (Quan trọng!)
            # 'https://cdn.jsdelivr.net/npm/intl-tel-input@18.2.1/build/css/intlTelInput.css',
            # File JavaScript OWL Component
            # 'chatopia/static/src/js/external_libraries.js',
            # # File XML Template OWL Component
            # 'chatopia/static/src/xml/external_libraries.xml',
            'chatopia/static/src/xml/messenger_templates.xml',
        ],
        # 'web.assets_qweb': [
        #     # Khai báo file chứa các template QWeb
        # ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}