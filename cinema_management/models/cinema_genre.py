# -*- coding: utf-8 -*-
from odoo import models, fields

class CinemaGenre(models.Model):
    _name = 'cinema.genre'
    _description = 'Movie Genre'

    name = fields.Char(string='Genre Name', required=True)
    color = fields.Integer(string='Color Index')
