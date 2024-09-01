
# EventMobi Helpers Web App

This web application provides several tools to manage EventMobi events using the EventMobi API. The available tools include deleting sessions within a specific group, adding people to groups by email, managing chat settings for people in groups, and mass deleting sessions based on a list of session IDs.

## Features

1. **Delete Sessions in a Group**: 
   - Allows users to delete all sessions within a specific track of an event.
   
2. **Add People to Group by Email**: 
   - Enables users to add people to a specific group by providing a list of email addresses.
   
3. **Manage Chat Settings**:
   - Users can enable or disable the chat feature for a group of people within an event.
   
4. **Mass Delete Sessions**:
   - Users can delete multiple sessions by providing a list of session IDs.

## Prerequisites

- Python 3.x
- Flask
- Requests library
- Flask-WTF
- aiohttp

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

4. Run the application:

    ```bash
    python run.py
    ```

5. Open your web browser and navigate to `http://127.0.0.1:5000`.

## Deployment

For deploying this application on a server (e.g., using Apache with mod_wsgi), follow these steps:

1. **Ensure the server has Python 3.x installed**.
   
2. **Create a virtual environment** on the server and install the required packages using the `requirements.txt` file.

3. **Set up Apache to serve the Flask application** by configuring `mod_wsgi`. The WSGI entry point should be defined in a `wsgi.py` file:

    \`\`\`python
    from app import create_app

    app = create_app()

    if __name__ == "__main__":
        app.run()
    ```

4. **Configure Apache** to point to the `wsgi.py` file and set up the necessary directory permissions.

5. **Set up automatic deployment** by configuring a Git post-receive hook or using a continuous deployment tool.

## Folder Structure

```plaintext
eventmobi-helpers-web/
├── app/
│   ├── __init__.py
│   ├── main/
│   │   ├── __init__.py
│   │   ├── routes.py
│   ├── delete_sessions_group/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   ├── services.py
│   ├── add_people_to_group/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   ├── services.py
│   ├── manage_chat/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   ├── services.py
│   ├── mass_delete_sessions/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   ├── services.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── delete_sessions_group/
│   │   │   ├── api_key.html
│   │   │   ├── select_event.html
│   │   │   ├── select_track.html
│   │   ├── add_people_to_group/
│   │   │   ├── api_key.html
│   │   │   ├── select_event.html
│   │   │   ├── select_group.html
│   │   ├── manage_chat/
│   │   │   ├── api_key.html
│   │   │   ├── select_event.html
│   │   │   ├── select_group.html
│   │   ├── mass_delete_sessions/
│   │   │   ├── api_key.html
│   │   │   ├── select_event.html
│   │   │   ├── delete_sessions.html
├── static/
│   ├── css/
│   │   ├── styles.css
├── venv/
├── wsgi.py
├── run.py
├── requirements.txt
├── README.md
```

## Customization

- **CSS Customization**: Modify the CSS file located at `static/css/styles.css`.
- **Template Customization**: Templates are located in the `app/templates/` directory and can be modified to fit your needs.

## License

This project is licensed under the MIT License.
