# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CinemaSeat(models.Model):
    _name = 'cinema.seat'
    _description = 'Studio Seat'
    _order = 'hall_id, row, col_index, number'

    name = fields.Char(string='Seat Number', compute='_compute_name', store=True)
    hall_id = fields.Many2one('cinema.hall', string='Studio', required=True, ondelete='cascade')
    row = fields.Char(string='Row', required=True, default='A', help='Example: A, B, C')
    number = fields.Integer(string='Seat Number', required=True, default=1)
    col_index = fields.Integer(string='Column Position', default=1, 
                               help='Used to organize horizontal layout position (left to right)')
    
    seat_type = fields.Selection([
        ('standard', 'Standard'),
        ('sweetbox', 'Sweetbox / Couple'),
        ('vip', 'VIP Recliner'),
    ], string='Seat Type', default='standard', required=True)

    active = fields.Boolean(string='Active', default=True)

    @api.depends('row', 'number')
    def _compute_name(self):
        for seat in self:
            if seat.row and seat.number:
                seat.name = f"{seat.row}{seat.number}"
            else:
                seat.name = _("New Seat")
