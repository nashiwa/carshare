This is a Flask-based ride-sharing web application that allows users to register, log in, and book or offer rides. It integrates with an IBM DB2 database to manage users, trips, reservations, and reviews.

# Key Features:
- **User Authentication**: Users can register and log in with their email. Sessions are maintained to keep users logged in.
- **Trip Management**: Users can create, view, and delete trips, specifying details like start location, destination, time, transport type, and cost.
- **Booking**: Users can book available seats on trips. Multiple bookings for the same trip are restricted, and users can’t book their own trips.
- **Reviews and Ratings**: After a trip, users can rate and review the trip, providing feedback to other users.
- **Search Functionality**: Users can search for available trips based on start and end locations or by date.
- **Top-Rated Driver**: The app highlights the highest-rated driver and their available trips.

# Technologies Used:
- **Flask**: For routing, session management, and rendering HTML templates.
- **DB2**: IBM DB2 database for storing users, trips, reservations, and ratings.
- **HTML/CSS**: Used for the front-end pages like registration, login, and trip management.
- **Environment Variables**: `.env` file is used to store sensitive data like database credentials and secret keys.

# Setup Instructions:
1. Clone the repository.
2. Install the required Python packages from `requirements.txt`.
3. Set up the `.env` file with your DB2 credentials and Flask secret key.
4. Run the application using `python app.py`.

