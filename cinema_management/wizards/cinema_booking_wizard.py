# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CinemaBookingWizard(models.TransientModel):
    _name = 'cinema.booking.wizard'
    _description = 'Offline Cinema Booking Wizard'

    showtime_id = fields.Many2one('cinema.showtime', string='Showtime', required=True)
    movie_id = fields.Many2one('cinema.movie', related='showtime_id.movie_id', readonly=True)
    hall_id = fields.Many2one('cinema.hall', related='showtime_id.hall_id', readonly=True)
    price = fields.Float(string='Price per Ticket', related='showtime_id.price', readonly=True)
    
    partner_id = fields.Many2one('res.partner', string='Customer / Audience', required=True, 
                                 default=lambda self: self._default_partner_id())

    line_ids = fields.One2many('cinema.booking.seat.line', 'wizard_id', string='Studio Seat Status')
    selected_seat_ids = fields.Many2many('cinema.seat', string='Selected Seats', 
                                         compute='_compute_selected_seats', store=True)
    seat_count = fields.Integer(string='Number of Tickets', compute='_compute_totals')
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals')
    
    seat_map_html = fields.Html(string='Interactive Seat & Screen Layout', compute='_compute_seat_map_html')

    @api.model
    def _default_partner_id(self):
        partner = self.env['res.partner'].search([('name', '=', 'Walk-in Customer')], limit=1)
        if not partner:
            partner = self.env['res.partner'].search([('name', '=', 'Pelanggan Umum (Walk-in)')], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': 'Walk-in Customer',
                'customer_rank': 1,
            })
        return partner.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        showtime_id = res.get('showtime_id') or self.env.context.get('default_showtime_id')
        if showtime_id:
            showtime = self.env['cinema.showtime'].browse(showtime_id)
            booked_seat_ids = set(showtime.booked_seat_ids.ids)
            lines = []
            seats = showtime.hall_id.seat_ids.filtered(lambda s: s.active)
            for seat in seats.sorted(key=lambda s: (s.row or '', s.col_index or s.number, s.number)):
                is_booked = seat.id in booked_seat_ids
                lines.append((0, 0, {
                    'seat_id': seat.id,
                    'is_booked': is_booked,
                    'is_selected': False,
                }))
            res['line_ids'] = lines
        return res

    @api.depends('line_ids.is_selected')
    def _compute_selected_seats(self):
        for rec in self:
            selected = rec.line_ids.filtered(lambda l: l.is_selected and not l.is_booked)
            rec.selected_seat_ids = selected.mapped('seat_id')

    @api.depends('selected_seat_ids', 'price')
    def _compute_totals(self):
        for rec in self:
            rec.seat_count = len(rec.selected_seat_ids)
            rec.total_amount = rec.seat_count * rec.price

    @api.depends('line_ids', 'line_ids.is_selected', 'line_ids.is_booked')
    def _compute_seat_map_html(self):
        for wizard in self:
            if not wizard.hall_id:
                wizard.seat_map_html = False
                continue

            lines = wizard.line_ids
            rows = {}
            for line in lines.sorted(key=lambda l: (l.row or '', l.seat_id.col_index or l.number, l.number)):
                r = line.row or '?'
                if r not in rows:
                    rows[r] = []
                rows[r].append(line)

            screen_pos = wizard.hall_id.screen_position or 'top'
            screen_label = wizard.hall_id.screen_label or _("🎬 C I N E M A  S C R E E N")

            screen_html = f'''
                <div style="margin: 0 auto 20px auto; max-width: 500px; text-align: center;">
                    <div style="background: linear-gradient(180deg, #38bdf8 0%, rgba(56, 189, 248, 0.05) 100%); height: 16px; border-radius: 8px 8px 0 0; box-shadow: 0 4px 20px rgba(56, 189, 248, 0.6);"></div>
                    <div style="color: #94a3b8; font-size: 12px; font-weight: bold; letter-spacing: 3px; padding-top: 6px;">{screen_label}</div>
                </div>
            '''

            html = [
                '<div style="background-color: #0f172a; border-radius: 14px; padding: 24px; text-align: center; color: white; font-family: sans-serif;">',
            ]

            if screen_pos == 'top':
                html.append(screen_html)

            html.append('  <div style="display: inline-block; margin: 15px auto;">')
            for row_letter, seat_lines in sorted(rows.items()):
                html.append('    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 8px;">')
                html.append(f'      <span style="width: 24px; font-weight: bold; color: #94a3b8;">{row_letter}</span>')
                for line in seat_lines:
                    if line.is_booked:
                        bg = '#475569'
                        cursor = 'not-allowed'
                        title = _("%(name)s (Booked)", name=line.seat_name)
                        border = '1px solid #334155'
                    elif line.is_selected:
                        bg = '#38bdf8'
                        cursor = 'pointer'
                        title = _("%(name)s (Selected)", name=line.seat_name)
                        border = '2px solid #ffffff'
                    else:
                        bg = '#10b981'
                        cursor = 'pointer'
                        title = _("%(name)s (Available)", name=line.seat_name)
                        border = '1px solid transparent'

                    html.append(
                        f'      <span style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 34px; '
                        f'background: {bg}; border: {border}; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: {cursor}; color: white;" '
                        f'title="{title}">{line.seat_name}</span>'
                    )
                html.append(f'      <span style="width: 24px; font-weight: bold; color: #94a3b8;">{row_letter}</span>')
                html.append('    </div>')

            html.append('  </div>')

            if screen_pos == 'bottom':
                html.append(screen_html)

            html.append('</div>')
            wizard.seat_map_html = "\n".join(html)

    def action_confirm_booking(self):
        self.ensure_one()
        
        selected_seats = self.selected_seat_ids
        if not selected_seats:
            raise UserError(_("Please select at least 1 available seat to continue booking!"))

        already_booked = self.env['cinema.ticket'].search([
            ('showtime_id', '=', self.showtime_id.id),
            ('seat_id', 'in', selected_seats.ids),
            ('state', 'in', ('valid', 'used'))
        ])
        if already_booked:
            seat_names = ", ".join(already_booked.mapped('seat_name'))
            raise UserError(_("The following seats have just been booked by another transaction: %(seats)s", seats=seat_names))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [
                (0, 0, {
                    'name': _("Cinema Ticket: %(movie)s (%(hall)s) - Seat %(seat)s", 
                              movie=self.movie_id.name, hall=self.hall_id.name, seat=seat.name),
                    'quantity': 1,
                    'price_unit': self.price,
                }) for seat in selected_seats
            ]
        }
        invoice = self.env['account.move'].create(invoice_vals)

        for seat in selected_seats:
            self.env['cinema.ticket'].create({
                'showtime_id': self.showtime_id.id,
                'seat_id': seat.id,
                'partner_id': self.partner_id.id,
                'price': self.price,
                'invoice_id': invoice.id,
                'state': 'valid',
            })

        return {
            'name': _('Customer Invoice Ticket Booking'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CinemaBookingSeatLine(models.TransientModel):
    _name = 'cinema.booking.seat.line'
    _description = 'Wizard Seat Status Line'

    wizard_id = fields.Many2one('cinema.booking.wizard', string='Wizard', ondelete='cascade')
    seat_id = fields.Many2one('cinema.seat', string='Seat', required=True)
    seat_name = fields.Char(string='Seat No', related='seat_id.name')
    row = fields.Char(string='Row', related='seat_id.row')
    number = fields.Integer(string='Number', related='seat_id.number')
    seat_type = fields.Selection(related='seat_id.seat_type', string='Type')
    is_booked = fields.Boolean(string='Booked', default=False)
    is_selected = fields.Boolean(string='Select This Seat', default=False)

    def action_toggle_select(self):
        self.ensure_one()
        if not self.is_booked:
            self.is_selected = not self.is_selected
        return {'type': 'ir.actions.client', 'tag': 'reload'}
