# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import string

class CinemaGenerateSeatsWizard(models.TransientModel):
    _name = 'cinema.generate.seats.wizard'
    _description = 'Studio Seat Generator Wizard'

    hall_id = fields.Many2one('cinema.hall', string='Target Studio', required=True)
    row_from = fields.Selection([
        (c, c) for c in string.ascii_uppercase
    ], string='From Row', default='A', required=True)
    
    row_to = fields.Selection([
        (c, c) for c in string.ascii_uppercase
    ], string='To Row', default='J', required=True)
    
    number_from = fields.Integer(string='From Number', default=1, required=True)
    number_to = fields.Integer(string='To Number', default=9, required=True)
    
    seat_type = fields.Selection([
        ('standard', 'Standard'),
        ('sweetbox', 'Sweetbox / Couple'),
        ('vip', 'VIP Recliner'),
    ], string='Seat Type', default='standard', required=True)

    mode = fields.Selection([
        ('append', 'Append to Existing Seats'),
        ('replace', 'Delete Existing Seats & Recreate'),
    ], string='Creation Mode', default='append', required=True)

    def action_generate_seats(self):
        self.ensure_one()
        
        ord_from = ord(self.row_from)
        ord_to = ord(self.row_to)
        if ord_from > ord_to:
            raise UserError(_("'From Row' (%(f)s) cannot be greater than 'To Row' (%(t)s).", f=self.row_from, t=self.row_to))

        if self.number_from <= 0 or self.number_to <= 0:
            raise UserError(_("Seat numbers must be positive integers."))
        if self.number_from > self.number_to:
            raise UserError(_("'From Number' (%(f)d) cannot be greater than 'To Number' (%(t)d).", f=self.number_from, t=self.number_to))

        hall = self.hall_id
        if self.mode == 'replace':
            hall.seat_ids.unlink()

        existing_seats = set(hall.seat_ids.mapped('name'))
        new_seats_vals = []

        for row_ascii in range(ord_from, ord_to + 1):
            row_letter = chr(row_ascii)
            for num in range(self.number_from, self.number_to + 1):
                seat_code = f"{row_letter}{num}"
                if seat_code not in existing_seats:
                    new_seats_vals.append({
                        'hall_id': hall.id,
                        'row': row_letter,
                        'number': num,
                        'seat_type': self.seat_type,
                    })

        if new_seats_vals:
            self.env['cinema.seat'].create(new_seats_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Seats Generated Successfully!'),
                'message': _('Successfully generated %(count)d seats for %(hall)s.', count=len(new_seats_vals), hall=hall.name),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
