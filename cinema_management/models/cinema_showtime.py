# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class CinemaShowtime(models.Model):
    _name = 'cinema.showtime'
    _description = 'Movie Showtime'
    _order = 'start_time asc'

    name = fields.Char(string='Schedule Reference', compute='_compute_name', store=True)
    movie_id = fields.Many2one('cinema.movie', string='Movie', required=True, ondelete='restrict')
    hall_id = fields.Many2one('cinema.hall', string='Studio', required=True, ondelete='restrict')
    
    start_time = fields.Datetime(string='Start Time', required=True, default=fields.Datetime.now)
    cleaning_buffer = fields.Integer(string='Cleaning Buffer (Minutes)', default=15, 
                                     help='Studio cleaning buffer time before the next session')
    end_time = fields.Datetime(string='Estimated End Time', compute='_compute_end_time', store=True)
    
    price = fields.Float(string='Ticket Price (Rp)', required=True, default=45000.0)
    
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='scheduled', required=True)

    ticket_ids = fields.One2many('cinema.ticket', 'showtime_id', string='Sold Tickets')
    booked_seat_ids = fields.Many2many('cinema.seat', string='Booked Seats', compute='_compute_booked_seat_ids')
    booked_seats_count = fields.Integer(string='Tickets Sold', compute='_compute_booked_seats_count')
    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoices')

    @api.depends('ticket_ids', 'ticket_ids.invoice_id')
    def _compute_invoices(self):
        for rec in self:
            invoices = rec.ticket_ids.mapped('invoice_id')
            rec.invoice_count = len(invoices)

    @api.depends('ticket_ids', 'ticket_ids.state')
    def _compute_booked_seat_ids(self):
        for rec in self:
            valid_tickets = rec.ticket_ids.filtered(lambda t: t.state in ('valid', 'used'))
            rec.booked_seat_ids = valid_tickets.mapped('seat_id')

    @api.depends('ticket_ids', 'ticket_ids.state')
    def _compute_booked_seats_count(self):
        for rec in self:
            rec.booked_seats_count = len(rec.ticket_ids.filtered(lambda t: t.state in ('valid', 'used')))

    @api.depends('movie_id', 'hall_id', 'start_time')
    def _compute_name(self):
        for rec in self:
            if rec.movie_id and rec.hall_id and rec.start_time:
                time_str = fields.Datetime.to_string(rec.start_time)
                rec.name = f"[{rec.hall_id.name}] {rec.movie_id.name} ({time_str})"
            else:
                rec.name = _("Draft Showtime")

    @api.depends('start_time', 'movie_id.duration', 'cleaning_buffer')
    def _compute_end_time(self):
        for rec in self:
            if rec.start_time and rec.movie_id:
                total_minutes = (rec.movie_id.duration or 0) + (rec.cleaning_buffer or 0)
                rec.end_time = rec.start_time + timedelta(minutes=total_minutes)
            else:
                rec.end_time = rec.start_time

    @api.constrains('start_time', 'end_time', 'hall_id')
    def _check_schedule_overlap(self):
        """Memastikan tidak ada jadwal tayang yang bertabrakan di studio yang sama."""
        for rec in self:
            if not rec.start_time or not rec.end_time or not rec.hall_id:
                continue
            
            domain = [
                ('id', '!=', rec.id),
                ('hall_id', '=', rec.hall_id.id),
                ('state', 'in', ['scheduled', 'ongoing']),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time),
            ]
            overlapping = self.search(domain, limit=1)
            if overlapping:
                raise ValidationError(_(
                    "Schedule collision in %(hall)s!\n"
                    "There is already a screening of '%(movie)s' from %(start)s to %(end)s.",
                    hall=rec.hall_id.name,
                    movie=overlapping.movie_id.name,
                    start=overlapping.start_time,
                    end=overlapping.end_time,
                ))

    def action_open_booking_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/cinema/booking/{self.id}',
            'target': 'new',
        }

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.ticket_ids.mapped('invoice_id')
        return {
            'name': _('Invoices for %(name)s', name=self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
        }

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'name': _('Sold Tickets for %(name)s', name=self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'cinema.ticket',
            'view_mode': 'list,form',
            'domain': [('showtime_id', '=', self.id)],
        }
