from flask import Flask, render_template, redirect, url_for, request, session
from flask_db2 import DB2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
import os
import process

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['DB2_DATABASE'] = os.getenv('DB2_DATABASE')
app.config['DB2_HOSTNAME'] = os.getenv('DB2_HOSTNAME')
app.config['DB2_PORT'] = os.getenv('DB2_PORT')
app.config['DB2_PROTOCOL'] = os.getenv('DB2_PROTOCOL')
app.config['DB2_USER'] = os.getenv('DB2_USER')
app.config['DB2_PASSWORD'] = os.getenv('DB2_PASSWORD')

db = DB2(app)


@app.route('/')
def index():
    cur = db.connection.cursor()
    cur.execute('select * from fahrt')
    rides = cur.fetchall()
    ride_list = process.process_list(rides)

    cur.close()
    del cur
    return render_template('index.html', rides=ride_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = db.connection.cursor()
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        if email is not None:
            cur.execute("select bid,name,email from benutzer where email= ?", (email,))
            result = cur.fetchone()
            loggedinUser = []
            if result is not None:
                for item in result:
                    loggedinUser.append(item)
            if result:
                session["ses_user"] = loggedinUser
                session['logged_in'] = True
                return redirect(url_for("mainView"))
            else:
                session['logged_in'] = False
                message = "Email Is Not Valid"
    cur.close()
    del cur
    return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    cur = db.connection.cursor()
    message = ''
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        cur.execute("select * from benutzer where email=?", (email,))
        result = cur.fetchall()

        if result:
            message = 'You are already registered to our site'
        else:
            cur.execute("insert into benutzer (email, name) values (?,?)", (email, name,))
            return redirect(url_for("login"))
    cur.close()
    del cur
    return render_template('register.html', message=message)


@app.route('/logout')
def logout():
    session.pop("ses_user", None)
    return redirect(url_for("login"))


@app.route('/main-view', methods=['GET', 'POST'])
def mainView():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        cur.execute(
            "select startort,zielort,status, transportmittel.icon,fid from fahrt join reservieren on fahrt.fid = reservieren.fahrt join transportmittel on fahrt.transportmittel = transportmittel.tid where reservieren.kunde =? ",
            (user[0],))
        result = cur.fetchall()
        booked_trips = process.process_list(result)
        cur.execute(
            "select startort,zielort,status,fahrtkosten,transportmittel.icon,fid from fahrt join transportmittel on fahrt.transportmittel = transportmittel.tid where  maxPlaetze>0")
        result = cur.fetchall()
        availabe_rides = process.process_list(result)

        cur.close()
        del cur
        return render_template('main_view.html', booked_trips=booked_trips, availabe_rides=availabe_rides)
    else:
        return redirect(url_for("login"))


@app.route('/new-drive', methods=['GET', 'POST'])
def newDrive():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        message = ''

        if request.method == "POST":
            start_from = request.form["from"]
            destination = request.form["to"]
            max_capacity = int(request.form["maxCapacity"])
            cost = int(request.form["cost"])
            transport = request.form["transport"]
            description = request.form["description"]

            date_time = request.form["dateTime"]
            [date, time] = date_time.split('T')
            formated_date_time = date + ' ' + time + ':' + '00'
            cur_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if start_from is not None and destination is not None and max_capacity in (
                    1, 2, 3, 4, 5, 6, 7, 8, 9,
                    10) and (cost > 0) and transport is not None and date_time is not None and len(description) <= 50:
                if cur_date_time > formated_date_time:
                    message = ['Previous date is not allowed']
                else:
                    cur.execute(
                        'INSERT INTO fahrt (startort, zielort, fahrtdatumzeit, maxPlaetze, fahrtkosten, anbieter, transportmittel, beschreibung)  VALUES (?,?,?,?,?,?,?,?)',
                        (start_from, destination, formated_date_time, max_capacity, cost, user[0], transport,
                         description))
                    return redirect(url_for("mainView"))
            else:
                message = ['All asterisk (*) fileds and required',
                           'The allowed value for Maximum Capacity is between 1 and 10',
                           'Cost have to be a greater than 0',
                           'Length of description can not be greater than 50']
        cur.close()
        del cur
        return render_template('new_drive.html', message=message)
    else:
        return redirect(url_for("login"))


@app.route('/view-drive/<fid>', methods=['GET', 'POST'])
def viewDrive(fid):
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        cur.execute(
            "select fahrt.fid,fahrt.startort,fahrt.zielort,fahrt.fahrtdatumzeit,fahrt.maxPlaetze,fahrt.fahrtkosten,fahrt.status,fahrt.beschreibung,benutzer.bid, benutzer.email, transportmittel.icon from fahrt join benutzer on fahrt.anbieter=benutzer.bid join transportmittel on fahrt.transportmittel = transportmittel.tid where fahrt.fid=?",
            (fid,))
        result = cur.fetchone()
        trip_details = process.make_single_list(result)

        cur.execute('select * from reservieren where kunde = ? and fahrt = ?', (user[0], fid))
        result = cur.fetchone()
        already_booked = process.make_single_list(result)

        cur.execute('select sum(anzPlaetze) from reservieren r where r.fahrt = ?', (fid,))
        result = cur.fetchone()
        total_reserved = process.make_single_list(result)

        cur.execute(
            "select benutzer.email,bewertung.textnachricht,bewertung.rating from bewertung join benutzer on bewertung.benutzer=benutzer.bid  where bewertung.fahrt = ?",
            (fid,))
        result = cur.fetchall()
        all_ratings = process.process_list(result)

        cur.execute(
            "select cast(avg(cast((bewertung.rating) as decimal(4,2))) as dec(4,2)) as average  from bewertung where bewertung.fahrt = ?"
            , (fid,))
        average_rating = cur.fetchone()

        if not total_reserved[0]:
            available_seat = trip_details[4]
        else:
            available_seat = trip_details[4] - total_reserved[0]

        error = ''
        success = ''
        if request.method == "POST":
            seat = int(request.form['seat'])
            if trip_details[8] == user[0]:
                error = "You can't book your own trip"
            elif trip_details[6] != 'offen':
                error = "This trip has been closed"
            elif seat not in (1, 2) and seat > int(trip_details[4]):
                error = "Maximum 2 seats can be booked and you can't book more than the availabe seats"
            elif len(already_booked) > 0:
                error = 'Multipule bookings for same trip is not allowed'
            else:
                cur.execute('insert into reservieren (kunde, fahrt, anzPlaetze) values (?,?,?)', (user[0], fid, seat))
                if cur.rowcount > 0:
                    error = ''
                    success = 'Booking Successfull'
                else:
                    error = 'Something went wrong. Booking failed'

            # Updating availabLe seat after booking
            cur.execute(
                "select fahrt.fid,fahrt.startort,fahrt.zielort,fahrt.fahrtdatumzeit,fahrt.maxPlaetze,fahrt.fahrtkosten,fahrt.status,fahrt.beschreibung,benutzer.bid, benutzer.email, transportmittel.icon from fahrt join benutzer on fahrt.anbieter=benutzer.bid join transportmittel on fahrt.transportmittel = transportmittel.tid where fahrt.fid=?",
                (fid,))
            result = cur.fetchone()
            trip_details = process.make_single_list(result)

            cur.execute('select sum(anzPlaetze) from reservieren r where r.fahrt = ?', (fid,))
            result = cur.fetchone()
            total_reserved = process.make_single_list(result)

            if not total_reserved[0]:
                available_seat = trip_details[4]
            else:
                available_seat = trip_details[4] - total_reserved[0]
        cur.close()
        del cur
        return render_template('view_drive.html', trip_details=trip_details, availabe_seat=available_seat, uid=user[0],
                               error=error, success=success, all_ratings=all_ratings, average_rating=average_rating)
    else:
        return redirect(url_for("login"))


@app.route('/delete-trip/<fid>', methods=['GET', 'POST'])
def deleteTrip(fid):
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        message = ''

        cur.execute('select * from fahrt where fid=? and anbieter=?', (fid, user[0]))
        result = cur.fetchall()
        delete_require = process.process_list(result)

        if not delete_require:
            message = 'You cant delete this trip because you are not the creator'
        else:
            if request.method == 'POST':
                cur.execute("delete from bewertung where fahrt=?", (fid,)),
                cur.execute("delete from reservieren where fahrt=?", (fid,)),
                cur.execute("delete from fahrt where fid=? and anbieter=?", (fid, user[0]))
                return redirect(url_for("mainView"))
        cur.close()
        del cur
        return render_template('delete_trip.html', message=message, delete_require=delete_require, fid=fid)

    else:
        return redirect(url_for("login"))


@app.route('/new-rating/<fid>', methods=['GET', 'POST'])
def newRating(fid):
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        message = ''

        cur.execute('select * from bewertung where fahrt=? and benutzer=?', (fid, user[0]))
        result = cur.fetchall()
        already_rated = process.make_single_list(result)

        cur.execute('select fid , anbieter from fahrt where fid=? and anbieter=?', (fid, user[0]))
        result = cur.fetchall()
        creator_trip = process.process_list(result)

        if creator_trip:
            message = 'You can not rate your own trip.'
        else:
            if already_rated:
                message = 'Multiple ratings are not allowed at the same trip.'
            else:
                if request.method == 'POST':
                    rating = int(request.form["rating"])
                    review_description = request.form["review"]
                    if rating is not None and review_description is not None and len(review_description) <= 50:
                        cur.execute("INSERT INTO bewertung(rating,textnachricht,fahrt,benutzer) VALUES(?,?,?,?)",
                                    (rating, review_description, fid, user[0]))
                        return redirect(url_for("viewDrive", fid=fid))
                    else:
                        message = 'All asterisk (*) fields and required'

        cur.close()
        del cur
        return render_template('new_rating.html', message=message, already_rated=already_rated,
                               creator_trip=creator_trip)

    else:
        return redirect(url_for("login"))


@app.route('/view-search', methods=['GET', 'POST'])
def viewSearch():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        error = ""
        searched_result = []
        searched = False

        if request.method == "POST":
            start_away = request.form["start"]
            end_destination = request.form["end"]
            date = request.form["date"]
            if start_away or end_destination or date:
                searched = True
                formated_date = f"{date}%"
                start = f"%{start_away}%".upper()
                end = f"%{end_destination}%".upper()
                cur.execute(
                    f"select startort,zielort, fahrtkosten, fahrtdatumzeit, transportmittel.icon from fahrt join transportmittel on fahrt.transportmittel = transportmittel.tid  where upper(startort) like ? and upper(zielort) like? and fahrtdatumzeit like ?",
                    (start, end, formated_date)
                )
                result = cur.fetchall()
                searched_result = process.process_list(result)
            else:
                error = 'Please write something to search'
        cur.close()
        del cur
        return render_template('view_search.html', error=error, searched=searched,
                               searched_result=searched_result)

    else:
        return redirect(url_for("login"))

@app.route('/bonus', methods=['GET', 'POST'])
def bonus():
    if "ses_user" in session:
        user = session["ses_user"]
        cur = db.connection.cursor()
        cur.execute(
            "select cast(avg(cast((bewertung.rating) as decimal(4,2))) as decimal(4,2)) as avgrating,bewertung.benutzer from bewertung join benutzer on benutzer.bid=bewertung.benutzer group by benutzer order by avgrating  desc fetch first 1 rows only")
        highest_rated_driver = cur.fetchone()
        highest_rated_driver_list = process.make_single_list(highest_rated_driver)
        if highest_rated_driver_list:
            cur.execute(
                "select fahrt.fid, fahrt.startort, fahrt.zielort, benutzer.email, transportmittel.icon from fahrt join benutzer on fahrt.anbieter=benutzer.bid join transportmittel on fahrt.transportmittel=transportmittel.tid where fahrt.status='offen' and fahrt.anbieter=?",
                (highest_rated_driver_list[1],))
            best_rides = cur.fetchall()
            bestRides_list = process.process_list(best_rides)
        cur.close()
        del cur
        return render_template('bonus.html', best_rides=best_rides,bestRides_list=bestRides_list, highest_rated_driver=highest_rated_driver_list)

    else:
        return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True)