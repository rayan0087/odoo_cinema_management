# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CinemaMovie(models.Model):
    _name = 'cinema.movie'
    _description = 'Cinema Movie'
    _order = 'release_date desc, id desc'

    name = fields.Char(string='Movie Title', required=True, index=True)
    poster = fields.Binary(string='Movie Poster', attachment=True)
    duration = fields.Integer(string='Duration (Minutes)', required=True, default=120)
    duration_display = fields.Char(string='Duration', compute='_compute_duration_display', store=True)
    
    genre_ids = fields.Many2many('cinema.genre', 'cinema_movie_genre_rel', 'movie_id', 'genre_id', string='Genres')
    genre = fields.Char(string='Genre (Text)', compute='_compute_genre_text', store=True)
    
    director = fields.Char(string='Director')
    casts = fields.Text(string='Casts / Actors')
    synopsis = fields.Text(string='Synopsis')
    
    age_rating = fields.Selection([
        ('SU', 'General Audiences (SU)'),
        ('13+', 'Teens (13+)'),
        ('17+', 'Adults (17+)'),
        ('21+', 'Mature (21+)')
    ], string='Age Rating', default='13+', required=True)

    release_date = fields.Date(string='Release Date')
    end_date = fields.Date(string='End Date')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('now_playing', 'Now Playing'),
        ('coming_soon', 'Coming Soon'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True)

    active = fields.Boolean(string='Active', default=True)
    showtime_ids = fields.One2many('cinema.showtime', 'movie_id', string='Showtimes')
    showtime_count = fields.Integer(string='Showtime Count', compute='_compute_showtime_count')

    @api.depends('duration')
    def _compute_duration_display(self):
        for record in self:
            if record.duration:
                hours = record.duration // 60
                minutes = record.duration % 60
                if hours > 0 and minutes > 0:
                    record.duration_display = _("%(hours)dh %(minutes)dm", hours=hours, minutes=minutes)
                elif hours > 0:
                    record.duration_display = _("%(hours)dh", hours=hours)
                else:
                    record.duration_display = _("%(minutes)dm", minutes=minutes)
            else:
                record.duration_display = "-"

    @api.depends('genre_ids')
    def _compute_genre_text(self):
        for record in self:
            record.genre = ", ".join(record.genre_ids.mapped('name')) if record.genre_ids else ""

    @api.depends('showtime_ids')
    def _compute_showtime_count(self):
        for record in self:
            record.showtime_count = len(record.showtime_ids)

    def action_set_now_playing(self):
        self.write({'state': 'now_playing'})

    def action_set_coming_soon(self):
        self.write({'state': 'coming_soon'})

    def action_set_archived(self):
        self.write({'state': 'archived'})
