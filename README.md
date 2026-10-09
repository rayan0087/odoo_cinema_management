# 🎬 Odoo 20 Cinema Management System (`cinema_management`)

A modern, full-featured **Cinema Management, Showtime Scheduling, and Box Office Ticketing System** designed specifically for **Odoo 20**.

This module delivers end-to-end cinema operations—from movie cataloging, hall layout and seat matrix configuration, to a responsive, web-based interactive seat-picking Box Office Kiosk with automated customer invoicing (`account.move`), instant payment registration, and thermal slip ticket printing.

---

## 🌟 Key Highlights & Features

### 1. 🎞️ Movie Master & Catalog Management
- **Default Visual Kanban View**: Browse movies with poster covers, duration, age classification, and active release state (`Draft`, `Now Playing`, `Coming Soon`, `Archived`).
- **Dynamic Duration Converter**: Automatically converts raw duration in minutes into a clean hours & minutes display (e.g., `120 mins` ➔ `2 Jam`, `119 mins` ➔ `1 Jam 59 Menit`).
- **Color-coded Genre Tags**: Many2Many genre linkage with customizable color tags (`cinema.genre`).
- **Comprehensive Metadata**: Director, cast, synopsis, age rating (`SU`, `13+`, `17+`, `21+`), and high-resolution poster uploads.

### 2. 🏛️ Studio & Hall Layout Configurator
- **Custom Screen Positioning**: Supports screen placement at either the top (front) or bottom (rear) of the hall with custom screen branding labels.
- **Seat Generator Wizard**: Automatically generates matrix seats (e.g., rows `A` to `J` with numbers `1` to `9` ➔ `A1, A2... J9`) with custom seat types (Standard, Sweetbox/Couple, VIP Recliner).
- **Interactive Visual Preview**: In-form HTML layout preview showing rows, columns, and screen glow reflection in real time.

### 3. 🕒 Showtime Scheduling & Conflict Prevention
- **Smart End Time Calculation**: Automatically computes session end time based on movie runtime plus studio cleaning/turnaround buffer time.
- **Collision Protection**: SQL and ORM-level overlapping schedule detection preventing duplicate bookings in the same hall.
- **Smart Button "Invoices"**: Direct one-click access from the showtime form to all generated customer invoices.

### 4. 🎟️ Interactive Web Box Office & Kiosk Seat Picker
- **Separate Web Controller (`/cinema/booking`)**: Dedicated standalone Kiosk interface designed for both cashier counter terminals and customer-facing displays.
- **Live Movie & Showtime Selection**: Customers or cashiers pick a showtime and get instantly routed to the theater hall layout.
- **Real-Time Click-to-Select Seat Map**:
  - 🟢 **Green**: Available seats (click to select).
  - 🔵 **Blue**: Selected seats with instant reactive counter and live price calculation.
  - 🔴 / 🔘 **Slate/Red**: Booked/occupied seats (disabled with tooltips).
- **Zero Latency**: Vanilla JavaScript reactive UI with zero lag and instant price summation in Indonesian Rupiah (`Rp`).

### 5. 💳 Automated Invoicing & Payment Reconciliation
- **Native Odoo Integration**: Seamless connection to Odoo's core `account.move` and `account.payment` models.
- **Auto-Payment Registration**: Selecting Cash or Bank/QRIS payment methods automatically validates the customer invoice to **`Posted`** and marks it as **`Paid`** with zero remaining balance (`residual = 0`).
- **Customer Linking**: Default walk-in customer support (`Pelanggan Umum`) with support for personalized customer names.
- **Direct Invoice "Print Cinema Tickets" Button**: Cashiers can reprint thermal tickets directly from the invoice form view or navigate through the **Tickets** smart button.

### 6. 🖨️ Thermal Slip Ticket Printing
- **QWeb HTML Thermal Slip Report**: Formatted specifically for standard 58mm / 80mm POS thermal receipt printers.
- **Complete Ticket Information**: Cinema branding, movie title, age rating, studio name, date, showtime, large prominent seat code, ticket number, customer name, price, print timestamp, and unique check-in barcode/token.

### 7. 🌐 Public Movie Guide & REST JSON API
- **Public Movie Showcase**: Customer-facing web page at `/movies` displaying active now-playing movies and upcoming showtimes.
- **Headless REST API**: `/api/movies/now-playing` JSON endpoint for mobile apps or digital cinema signage boards.

---

## 🏗️ Technical Architecture & Stack

- **Platform**: Odoo 20.0 Community / Enterprise
- **Backend Language**: Python 3.12
- **Database**: PostgreSQL 18
- **Frontend Stack**: QWeb Engine (`t-out` compliant), Bootstrap 5.3, Google Material Symbols, FontAwesome 6, Vanilla JS
- **Core Dependencies**: `base`, `web`, `account`

---

## 📂 Module Structure

```text
bioskop/
├── cinema_management/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── main.py                     # Web controllers (/cinema/booking, /movies, REST API)
│   ├── data/
│   │   └── cinema_demo_data.xml        # Demo data (movies, studios, showtimes)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account_move.py             # account.move inheritance & ticket reprint actions
│   │   ├── cinema_genre.py             # Genre model
│   │   ├── cinema_hall.py              # Studio / Hall model & layout preview
│   │   ├── cinema_movie.py             # Movie master model & duration display
│   │   ├── cinema_seat.py              # Seat matrix model
│   │   ├── cinema_showtime.py          # Showtime scheduling & conflict validation
│   │   └── cinema_ticket.py            # Ticket model & barcode tokens
│   ├── report/
│   │   └── cinema_ticket_report.xml    # QWeb thermal slip printing template
│   ├── security/
│   │   └── ir.access.csv               # Model access security definitions (Odoo 20 standard)
│   ├── static/
│   │   └── description/
│   │       └── icon.png                # Top-level Cinema menu icon
│   ├── views/
│   │   ├── account_move_views.xml      # Invoice form extension (Reprint button & smart button)
│   │   ├── cinema_booking_templates.xml# Web Kiosk & interactive seat selector templates
│   │   ├── cinema_genre_views.xml      # Genre views
│   │   ├── cinema_hall_views.xml       # Studio views & seat generator action
│   │   ├── cinema_menus.xml            # Top-level & configuration menus
│   │   ├── cinema_movie_views.xml      # Movie kanban & form views
│   │   ├── cinema_showtime_views.xml   # Showtime list, calendar, & form views
│   │   ├── cinema_ticket_views.xml     # Ticket log views
│   │   └── movie_templates.xml         # Public catalog templates (/movies)
│   └── wizards/
│       ├── __init__.py
│       ├── cinema_booking_wizard.py
│       ├── cinema_booking_wizard_views.xml
│       ├── cinema_generate_seats_wizard.py
│       └── cinema_generate_seats_wizard_views.xml
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Quick Start

1. **Place the Module**:
   Clone or copy the `bioskop` directory into your Odoo `addons_path`:
   ```bash
   addons_path = /path/to/custom_addons/bioskop
   ```

2. **Update App List & Install**:
   - Log in to Odoo with Administrator privileges.
   - Activate **Developer Mode** under Settings.
   - Go to **Apps ➔ Update Apps List**.
   - Search for `Cinema Management (Bioskop)` and click **Activate**.

3. **Explore the Application**:
   - Access the top-level **Bioskop** menu.
   - View movies in the **Film** menu.
   - Launch the interactive box office by navigating to **Layar Pemesanan (Kiosk)** or visiting:
     ```
     http://your-odoo-domain:port/cinema/booking
     ```

---

## 📄 License & Attribution

Developed for cinema box office automation and seamless ERP accounting integration on **Odoo 20**.
Licensed under **LGPL-3**.
