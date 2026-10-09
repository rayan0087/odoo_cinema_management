# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    ticket_ids = fields.One2many('cinema.ticket', 'invoice_id', string='Cinema Tickets')
    ticket_count = fields.Integer(string='Ticket Count', compute='_compute_ticket_count', store=True)

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    def action_print_cinema_tickets(self):
        self.ensure_one()
        if not self.ticket_ids:
            raise UserError(_("There are no cinema tickets associated with this invoice."))
        return self.env.ref('cinema_management.action_report_cinema_ticket').action_open_slip_preview(self.ticket_ids)

    def action_view_cinema_tickets(self):
        self.ensure_one()
        action = {
            'name': _('Cinema Tickets: %(name)s', name=self.name or self.id),
            'type': 'ir.actions.act_window',
            'res_model': 'cinema.ticket',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.ticket_ids.ids)],
        }
        if len(self.ticket_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.ticket_ids.id
        return action
