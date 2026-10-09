# -*- coding: utf-8 -*-
{
    'name': 'Cinema Management (Bioskop)',
    'version': '1.0.0',
    'category': 'Sales/Cinema',
    'summary': 'Manajemen Pemesanan Tiket Bioskop, Jadwal Tayang, dan Katalog Film',
    'description': """
        Modul Bioskop Odoo 20:
        - Manajemen Master Film & Studio/Hall
        - Penjadwalan Tayang (Showtime) dengan validasi durasi & buffer
        - Katalog Film Aktif via Web Controller (/movies) & REST JSON API (/api/movies/now-playing)
        - Manajemen Kursi & Tiket
        - Wizard Pemesanan Tiket Visual (Layar & Kursi Interaktif)
        - Integrasi Otomatis Customer Invoice (account.move)
        - Cetak Tiket Fisik (Thermal Slip Report)
    """,
    'author': 'Developer',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'account', 'base_print_slip'],
    'data': [
        'security/ir.access.csv',
        'report/cinema_ticket_report.xml',
        'wizards/cinema_generate_seats_wizard_views.xml',
        'wizards/cinema_booking_wizard_views.xml',
        'views/cinema_genre_views.xml',
        'views/cinema_movie_views.xml',
        'views/cinema_hall_views.xml',
        'views/cinema_ticket_views.xml',
        'views/account_move_views.xml',
        'views/cinema_showtime_views.xml',
        'views/cinema_menus.xml',
        'views/movie_templates.xml',
        'views/cinema_booking_templates.xml',
        'data/cinema_demo_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
