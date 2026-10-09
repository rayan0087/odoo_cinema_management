# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CinemaHall(models.Model):
    _name = 'cinema.hall'
    _description = 'Studio / Cinema Hall'

    name = fields.Char(string='Studio Name', required=True)
    hall_type = fields.Selection([
        ('regular', 'Regular'),
        ('premiere', 'Premiere / VIP'),
        ('imax', 'IMAX'),
    ], string='Studio Type', default='regular', required=True)

    screen_position = fields.Selection([
        ('top', 'Screen at Top (Front)'),
        ('bottom', 'Screen at Bottom (Back)'),
    ], string='Screen Position', default='top', required=True)

    screen_label = fields.Char(string='Screen Label', default='🎬 C I N E M A  S C R E E N')

    seat_ids = fields.One2many('cinema.seat', 'hall_id', string='Seats')
    total_seats = fields.Integer(string='Seat Capacity', compute='_compute_total_seats', store=True)
    active = fields.Boolean(string='Active', default=True)

    layout_preview_html = fields.Html(string='Seat & Screen Layout Preview', compute='_compute_layout_preview_html')

    @api.depends('seat_ids', 'seat_ids.active')
    def _compute_total_seats(self):
        for hall in self:
            hall.total_seats = len(hall.seat_ids.filtered(lambda s: s.active))

    @api.depends('seat_ids', 'seat_ids.row', 'seat_ids.number', 'seat_ids.col_index', 'seat_ids.seat_type', 'seat_ids.active', 'screen_position', 'screen_label')
    def _compute_layout_preview_html(self):
        for hall in self:
            seats = hall.seat_ids.filtered(lambda s: s.active)
            rows = {}
            for s in seats.sorted(key=lambda x: (x.row or '', x.col_index or x.number, x.number)):
                r = s.row or '?'
                if r not in rows:
                    rows[r] = []
                rows[r].append(s)

            label = hall.screen_label or _("🎬 C I N E M A  S C R E E N")
            screen_html = f'''
                <div style="margin: 15px auto; max-width: 600px; text-align: center;">
                    <div style="background: linear-gradient(180deg, #38bdf8 0%, rgba(56, 189, 248, 0.1) 100%); height: 16px; border-radius: 8px 8px 0 0; box-shadow: 0 4px 20px rgba(56, 189, 248, 0.5);"></div>
                    <div style="color: #94a3b8; font-size: 13px; font-weight: bold; letter-spacing: 3px; padding-top: 6px;">{label}</div>
                </div>
            '''

            html = [
                '<div style="background-color: #0f172a; border-radius: 12px; padding: 24px; text-align: center; color: white; font-family: sans-serif;">',
            ]
            if hall.screen_position == 'top':
                html.append(screen_html)

            html.append('<div style="display: inline-block; margin: 15px auto;">')
            for row_letter, seat_list in sorted(rows.items()):
                html.append(f'<div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 8px;">')
                html.append(f'<span style="width: 24px; font-weight: bold; color: #94a3b8;">{row_letter}</span>')
                for s in seat_list:
                    color = '#10b981' if s.seat_type == 'standard' else '#f59e0b' if s.seat_type == 'sweetbox' else '#8b5cf6'
                    seat_name = s.name or f"{s.row}{s.number}"
                    html.append(
                        f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 32px; '
                        f'background: {color}; border-radius: 6px; font-size: 11px; font-weight: bold;" title="{seat_name} ({s.seat_type})">{seat_name}</span>'
                    )
                html.append(f'<span style="width: 24px; font-weight: bold; color: #94a3b8;">{row_letter}</span>')
                html.append('</div>')
            html.append('</div>')

            if hall.screen_position == 'bottom':
                html.append(screen_html)

            html.append('</div>')
            hall.layout_preview_html = "\n".join(html)

    def action_open_generate_seats_wizard(self):
        self.ensure_one()
        return {
            'name': _('Generate Seats: %(hall)s', hall=self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'cinema.generate.seats.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_hall_id': self.id,
            }
        }
