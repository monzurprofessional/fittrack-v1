# FitTrack Gym Management System

Simple Flask + MySQL gym management system using raw SQL only.

## Setup

1. Create a MySQL database in MAMP, for example `fittrack`.
2. Copy `.env.example` to `.env` and update your local MySQL credentials.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Import the database:

```bash
mysql -u YOUR_USER -p YOUR_DATABASE_NAME < database.sql
```

If MAMP uses port `8889`, add `--port=8889`.

5. Run the app:

```bash
flask --app app run --debug
```

## Demo Logins

Admin:
- username: `admin1`
- password: `admin123`

Members:
- username: `member1`
- password: `pass123`

Trainers:
- username: `trainer1`
- password: `pass123`

## Notes


- The app uses raw SQL through `mysql-connector-python`; no ORM is used.
- Update database connection values in `.env`.
