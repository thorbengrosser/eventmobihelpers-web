# EventMobi Helpers Web App

This web application provides several tools to manage EventMobi events using the EventMobi API. The tools available include deleting sessions within a specific group, adding people to groups by email, managing chat settings for people in groups, and editing session information manually.

## Features

1. **Delete Sessions in a Group**: 
   - Allows users to delete all sessions within a specific track of an event.
   
2. **Add People to Group by Email**: 
   - Enables users to add people to a specific group by providing a list of email addresses.
   
3. **Manage Chat Settings**:
   - Users can enable or disable the chat feature for a group of people within an event.
   - Manage attendee settings and chat preferences

4. **Mass Delete Sessions**:
   - Allows users to delete multiple sessions by providing a list of session IDs.

5. **Expert Session Editor**:
   - Allows users to manually edit session information, including chat settings, AAQ settings, and more.

## Prerequisites

- Python 3.x
- Flask
- Requests library
- Flask-Login (for authentication)
- Flask-WTF (for forms)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/thorbengrosser/eventmobihelpers-web.git
    cd eventmobi-helpers-web
    ```

2. Create a virtual environment and activate it:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your EventMobi API credentials:
     ```
     EVENTMOBI_API_KEY=your_api_key
     EVENTMOBI_API_SECRET=your_api_secret
     ```

5. Run the application:

    ```bash
    python run.py
    ```

6. Open your web browser and navigate to `http://127.0.0.1:5000`.

## Deployment

For deploying this application on a server (e.g., using Apache with mod_wsgi), follow these steps:

1. **Ensure the server has Python 3.x installed**.
   
2. **Create a virtual environment** on the server and install the required packages using the `requirements.txt` file.

3. **Set up environment variables** on your production server.

4. **Set up Apache** to serve the Flask application by configuring `mod_wsgi`. The WSGI entry point should be defined in a `wsgi.py` file:

    ```python
    from app import create_app

    app = create_app()

    if __name__ == "__main__":
        app.run()
    ```

5. **Configure Apache** to point to the `wsgi.py` file and set up the necessary directory permissions.

6. **Set up automatic deployment** by configuring a Git post-receive hook or using a continuous deployment tool.

## Folder Structure

```plaintext
eventmobi-helpers-web/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── api_client.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── extensions.py
│   ├── models.py
│   ├── session.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── delete_sessions_group/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── add_people_to_group/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── manage_chat/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── mass_delete_sessions/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── expert_session_editor/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── base_form.html
│   │   ├── index.html
│   │   ├── auth/
│   │   ├── main/
│   │   ├── delete_sessions_group/
│   │   ├── add_people_to_group/
│   │   ├── manage_chat/
│   │   ├── mass_delete_sessions/
│   │   └── expert_session_editor/
│   └── static/
│       └── css/
│           └── styles.css
├── instance/
├── venv/
├── wsgi.py
├── run.py
├── requirements.txt
├── config.py
└── README.md
```

## Customization

- **CSS Customization**: Modify the CSS file located at `static/css/styles.css`.
- **Template Customization**: Templates are located in the `app/templates/` directory and can be modified to fit your needs.
- **API Configuration**: Update the API settings in `config.py` and environment variables.

## Security

- The application uses Flask-Login for authentication
- API credentials are stored securely using environment variables
- CSRF protection is enabled for all forms
- Session management is handled securely

## License

This project is licensed under the MIT License.
