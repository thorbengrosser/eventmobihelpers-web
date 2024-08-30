# EventMobi Helpers Web App

This web application provides several tools to manage EventMobi events using the EventMobi API. The tools available include deleting sessions within a specific group, adding people to groups by email, and managing chat settings for people in groups.

## Features

1. **Delete Sessions in a Group**: 
   - Allows users to delete all sessions within a specific track of an event.
   
2. **Add People to Group by Email**: 
   - Enables users to add people to a specific group by providing a list of email addresses.
   
3. **Manage Chat Settings**:
   - Users can enable or disable the chat feature for a group of people within an event.

## Prerequisites

- Python 3.x
- Flask
- Requests library

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
├── static/
│   ├── css/
│   │   ├── styles.css
├── venv/
├── run.py
├── requirements.txt
├── README.md
```
## Customization

The CSS file can be customized by modifying static/css/styles.css.
Templates are located in the app/templates/ directory and can be customized as needed.

## License
This project is licensed under the MIT License.

