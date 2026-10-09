# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import uuid

class CinemaTicket(models.Model):
    _name = 'cinema.ticket'
    _inherit = ['slip.print.mixin']
    _description = 'Cinema Ticket'
    _order = 'id desc'

    name = fields.Char(string='Ticket Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    showtime_id = fields.Many2one('cinema.showtime', string='Showtime', required=True, ondelete='restrict')
    movie_id = fields.Many2one('cinema.movie', string='Movie', related='showtime_id.movie_id', store=True)
    hall_id = fields.Many2one('cinema.hall', string='Studio', related='showtime_id.hall_id', store=True)
    seat_id = fields.Many2one('cinema.seat', string='Seat', required=True, ondelete='restrict')
    seat_name = fields.Char(string='Seat No', related='seat_id.name', store=True)
    
    partner_id = fields.Many2one('res.partner', string='Customer / Audience', required=True)
    price = fields.Float(string='Ticket Price', required=True)
    invoice_id = fields.Many2one('account.move', string='Customer Invoice', ondelete='set null')
    booking_time = fields.Datetime(string='Booking Time', default=fields.Datetime.now, required=True)
    barcode_token = fields.Char(string='Barcode / Token', required=True, copy=False, default=lambda self: str(uuid.uuid4())[:8].upper())
    
    state = fields.Selection([
        ('valid', 'Valid / Active'),
        ('used', 'Used (Check-in)'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='valid', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) in (_('New'), 'Baru', 'New'):
                token = vals.get('barcode_token') or str(uuid.uuid4())[:8].upper()
                vals['barcode_token'] = token
                vals['name'] = f"TKT-{token}"
        return super().create(vals_list)

    def action_check_in(self):
        self.write({'state': 'used'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_print_ticket(self):
        self.ensure_one()
        return self.action_print_slip('cinema_management.action_report_cinema_ticket')
