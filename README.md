# Sahyog Setu 🤝

**Sahyog Setu** ("bridge of cooperation") is a Flask-based community support platform that connects people in need with volunteers. It makes it easy to share help, manage requests, and build a stronger community.

## Features

- Post a help request describing what you need
- Volunteers can browse requests and offer help
- Manage and track the status of requests
- Simple, lightweight web interface built with Flask and Jinja templates

> Edit this list to match exactly what your app does (login, categories, dashboard, etc.).

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, Jinja2 templates
- **Database:** SQLite (stored in the `instance/` folder)

## Project Structure

```
Hakathon_02/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── instance/           # Local database / instance config
└── templates/          # HTML templates (Jinja2)
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/amit26717-cmd/Hakathon_02.git
cd Hakathon_02

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Usage

1. Open the app in your browser.
2. Register / log in (if enabled).
3. People in need can create a help request.
4. Volunteers can view requests and offer help.

## Screenshots

_Add screenshots of your app here._

## Future Improvements

- Notifications for new requests
- Location-based matching of volunteers
- Admin dashboard

## Contributing

Contributions are welcome. Fork the repo, create a branch, and open a pull request.

## Team

Built for a hackathon by **amit26717-cmd** and team.

## License

This project is open source. Add a license of your choice (e.g., MIT).
