# -*- coding: utf-8 -*-
import json
from odoo import http, fields
from odoo.http import request

class CinemaMovieController(http.Controller):

    @http.route(['/movies', '/bioskop/movies'], type='http', auth='public', website=False)
    def list_active_movies(self, **kwargs):
        """Menampilkan halaman katalog film yang sedang tayang langsung dari model cinema.showtime."""
        now = fields.Datetime.now()
        
        # Ambil seluruh data jadwal tayang aktif (scheduled / ongoing)
        active_showtimes = request.env['cinema.showtime'].sudo().search([
            ('state', 'in', ['scheduled', 'ongoing']),
        ], order='start_time asc')

        # Kelompokkan jadwal tayang per film
        movies_map = {}
        for st in active_showtimes:
            movie = st.movie_id
            if movie.id not in movies_map:
                movies_map[movie.id] = {
                    'movie': movie,
                    'showtimes': [],
                }
            movies_map[movie.id]['showtimes'].append(st)

        movies_list = list(movies_map.values())

        return request.render('cinema_management.movie_list_page', {
            'movies_list': movies_list,
            'active_showtimes': active_showtimes,
            'total_movies': len(movies_list),
            'total_showtimes': len(active_showtimes),
            'current_time': fields.Datetime.context_timestamp(request.env['cinema.showtime'], now),
        })

    @http.route(['/api/movies/now-playing'], type='http', auth='public', methods=['GET'], csrf=False)
    def api_active_movies(self, **kwargs):
        """REST Endpoint mengembalikan JSON film aktif dan jadwal tayangnya langsung dari cinema.showtime."""
        now = fields.Datetime.now()
        
        active_showtimes = request.env['cinema.showtime'].sudo().search([
            ('state', 'in', ['scheduled', 'ongoing']),
        ], order='start_time asc')

        movies_map = {}
        for st in active_showtimes:
            movie = st.movie_id
            if movie.id not in movies_map:
                movies_map[movie.id] = {
                    'id': movie.id,
                    'name': movie.name,
                    'duration_minutes': movie.duration,
                    'age_rating': movie.age_rating,
                    'genre': movie.genre or '',
                    'director': movie.director or '',
                    'casts': movie.casts or '',
                    'synopsis': movie.synopsis or '',
                    'has_poster': bool(movie.poster),
                    'poster_url': f"/web/image/cinema.movie/{movie.id}/poster" if movie.poster else None,
                    'showtimes': [],
                }
            
            total_seats = st.hall_id.total_seats or len(st.hall_id.seat_ids)
            available_seats = max(0, total_seats - st.booked_seats_count)

            movies_map[movie.id]['showtimes'].append({
                'id': st.id,
                'hall_id': st.hall_id.id,
                'hall': st.hall_id.name,
                'hall_type': st.hall_id.hall_type,
                'start_time': fields.Datetime.to_string(st.start_time),
                'end_time': fields.Datetime.to_string(st.end_time),
                'price': st.price,
                'total_seats': total_seats,
                'booked_seats': st.booked_seats_count,
                'available_seats': available_seats,
                'booking_url': f"/cinema/booking/{st.id}",
            })

        response_body = {
            'status': 'success',
            'count': len(movies_map),
            'total_showtimes': len(active_showtimes),
            'server_time': fields.Datetime.to_string(now),
            'results': list(movies_map.values()),
        }
        return request.make_response(
            json.dumps(response_body, indent=2),
            headers=[('Content-Type', 'application/json')]
        )


class CinemaBookingController(http.Controller):

    @http.route(['/cinema/booking', '/bioskop/booking'], type='http', auth='public', website=False)
    def booking_movies_list(self, **kwargs):
        """Menampilkan daftar jadwal tayang aktif langsung dari model cinema.showtime untuk memesan tiket."""
        showtimes = request.env['cinema.showtime'].sudo().search([
            ('state', 'in', ['scheduled', 'ongoing']),
        ], order='start_time asc')
        return request.render('cinema_management.booking_select_movie', {
            'showtimes': showtimes,
        })

    @http.route('/cinema/booking/<int:showtime_id>', type='http', auth='public', website=False)
    def booking_seat_selection(self, showtime_id, **kwargs):
        """Menampilkan denah kursi interaktif untuk jadwal tayang tertentu beserta pilihan metode pembayaran bawaan Odoo."""
        showtime = request.env['cinema.showtime'].sudo().browse(showtime_id)
        if not showtime.exists() or showtime.state not in ('scheduled', 'ongoing'):
            return request.redirect('/cinema/booking')

        company_id = request.env.company.id or 1
        payment_journals = request.env['account.journal'].sudo().search([
            ('type', 'in', ['cash', 'bank']),
            ('company_id', 'in', [company_id, False]),
        ], order='type desc, name asc')

        hall = showtime.hall_id
        seats = hall.seat_ids.filtered(lambda s: s.active)
        booked_seat_ids = set(showtime.booked_seat_ids.ids)

        rows_dict = {}
        for seat in seats.sorted(key=lambda s: (s.row or '', s.col_index or s.number, s.number)):
            r = seat.row or '?'
            if r not in rows_dict:
                rows_dict[r] = []
            rows_dict[r].append(seat)

        sorted_rows = sorted(rows_dict.items(), key=lambda item: item[0])

        return request.render('cinema_management.booking_seat_selection', {
            'showtime': showtime,
            'sorted_rows': sorted_rows,
            'booked_seat_ids': booked_seat_ids,
            'payment_journals': payment_journals,
        })

    @http.route('/cinema/booking/confirm', type='http', auth='public', methods=['POST'], csrf=False)
    def booking_confirm(self, **kwargs):
        """Endpoint JSON untuk konfirmasi pesanan kursi, pembuatan invoice otomatis terbayar (Paid), dan tiket bioskop."""
        try:
            body = request.httprequest.get_data(as_text=True)
            data = json.loads(body) if body else {}
        except Exception as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': f'Format data JSON salah: {str(e)}'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        showtime_id = data.get('showtime_id')
        seat_ids = data.get('seat_ids', [])
        customer_name = (data.get('customer_name') or 'Pelanggan Umum (Walk-in)').strip()
        journal_id = data.get('journal_id')

        if not showtime_id or not seat_ids:
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Jadwal tayang atau kursi belum dipilih.'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        showtime = request.env['cinema.showtime'].sudo().browse(showtime_id)
        if not showtime.exists():
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Jadwal tayang tidak ditemukan.'}),
                headers=[('Content-Type', 'application/json')],
                status=404
            )

        # Validasi ketersediaan kursi realtime
        already_booked = set(showtime.booked_seat_ids.ids)
        conflicting = set(seat_ids) & already_booked
        if conflicting:
            conflicting_seats = request.env['cinema.seat'].sudo().browse(list(conflicting))
            names = ', '.join(conflicting_seats.mapped('name'))
            return request.make_response(
                json.dumps({'status': 'error', 'message': f'Kursi {names} sudah dipesan orang lain! Silakan pilih kursi lain.'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        seats = request.env['cinema.seat'].sudo().browse(seat_ids)

        # Cari atau buat partner pelanggan
        partner = request.env['res.partner'].sudo().search([('name', '=', customer_name)], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': customer_name,
                'customer_rank': 1,
            })

        # 1. Buat Customer Invoice di account.move
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': fields.Date.context_today(showtime),
            'invoice_line_ids': [
                (0, 0, {
                    'name': f"Tiket Bioskop: {showtime.movie_id.name} ({showtime.hall_id.name}) - Kursi {seat.name}",
                    'quantity': 1,
                    'price_unit': showtime.price,
                }) for seat in seats
            ]
        }
        invoice = request.env['account.move'].sudo().create(invoice_vals)

        # 2. Otomatis Post Invoice & Rekam Pembayaran (Register Payment) agar status langsung Lunas / Paid
        payment_method_label = "Tunai / Kas"
        try:
            invoice.action_post()
            if journal_id:
                journal = request.env['account.journal'].sudo().browse(int(journal_id))
            else:
                journal = request.env['account.journal'].sudo().search([
                    ('type', 'in', ['cash', 'bank']),
                    ('company_id', '=', invoice.company_id.id),
                ], limit=1)

            if journal and journal.exists():
                payment_method_label = f"{journal.name} ({journal.code})"
                payment_wizard = request.env['account.payment.register'].with_context(
                    active_model='account.move',
                    active_ids=invoice.ids
                ).sudo().create({
                    'journal_id': journal.id,
                })
                payment_wizard._create_payments()
        except Exception as pay_err:
            # Tetap lanjutkan jika register payment mengalami exception
            pass

        # 3. Buat record tiket bioskop (cinema.ticket)
        ticket_ids = []
        for seat in seats:
            ticket = request.env['cinema.ticket'].sudo().create({
                'showtime_id': showtime.id,
                'seat_id': seat.id,
                'partner_id': partner.id,
                'price': showtime.price,
                'invoice_id': invoice.id,
                'state': 'valid',
            })
            ticket_ids.append(ticket.id)

        ticket_ids_str = ','.join(map(str, ticket_ids))
        payment_status_text = "LUNAS (PAID)" if invoice.payment_state == 'paid' else "POSTED"
        
        return request.make_response(
            json.dumps({
                'status': 'success',
                'invoice_id': invoice.id,
                'invoice_name': invoice.name or f"INV-{invoice.id}",
                'invoice_url': f"/web#id={invoice.id}&model=account.move&view_type=form",
                'payment_state': invoice.payment_state,
                'payment_status_text': payment_status_text,
                'payment_method': payment_method_label,
                'ticket_ids': ticket_ids,
                'ticket_print_url': f"/report/html/cinema_management.report_cinema_ticket_template/{ticket_ids_str}",
                'message': f"Berhasil memesan {len(seats)} tiket! Invoice #{invoice.name or invoice.id} tercatat {payment_status_text} via {payment_method_label}.",
            }),
            headers=[('Content-Type', 'application/json')]
        )
