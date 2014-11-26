import os , re
from datetime import date
import sqlite3
from jinja2 import evalcontextfilter, Markup, escape
from flask import Flask, request, session, g, redirect, url_for, abort, \
render_template, flash

app = Flask(__name__)
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE= os.path.join(app.root_path, "sql" ,"shr.db"),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('SHR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('sql/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

t = date.today()
cur_mo = t.month
cur_year = t.year
cur_day = t.day

def get_num_days(month):
    if (month==2 and (cur_year % 4)==0):
        m_days=29
    elif (month==2):
        m_days=28
    elif (((month % 2)==0) and (month<7)):
        m_days = 30
    elif (((month % 2)!=0) and (month<=7)):
        m_days = 31
    elif (((month % 2)==0) and (month>=8)):
        m_days = 31
    elif (((month % 2)!=0) and (month>8)):
        m_days = 30
    return m_days

# c_wday[weekday,day_number,month_number]
def get_date_array():
    c_wday = []
    if ((date(cur_year, cur_mo, 1).weekday() != 0) and (cur_mo != 1)):
        n_d_p_m = get_num_days(cur_mo-1)
        while(date(cur_year,(cur_mo-1),n_d_p_m).weekday() != 6):
            wkdy = date(cur_year,(cur_mo-1),n_d_p_m).weekday()
            c_wday = [[wkdy, n_d_p_m, (cur_mo-1) ]] + c_wday
            n_d_p_m-=1
    elif ((date(cur_year, cur_mo, 1).weekday() != 0) and (cur_mo == 1)):
        n_d_p_m = 31
        while(date(cur_year-1,12,n_d_p_m).weekday() != 6):
            wkdy = date(cur_year-1,12,n_d_p_m).weekday()
            c_wday = [[wkdy, n_d_p_m, 12]] + c_wday
            n_d_p_m-=1

    n_d_c_m = get_num_days(cur_mo)
    n_d = 1
    while(n_d <=n_d_c_m):
        wkdy = date(cur_year, cur_mo, n_d).weekday() 
        c_wday = c_wday + [[wkdy, n_d, cur_mo]]
        n_d +=1
    
    if (cur_mo != 12):
        n_d_n_m = get_num_days(cur_mo+1)
        n_d = 1
        while(n_d <= n_d_n_m):
            wkdy = date(cur_year,(cur_mo+1),n_d).weekday()
            c_wday = c_wday + [[wkdy, n_d, (cur_mo+1)]] 
            n_d +=1
    else:
        n_d_n_m = 31 
        n_d = 1
        while(n_d <= n_d_n_m):
            wkdy = date(cur_year+1,1,n_d).weekday()
            c_wday = c_wday + [[wkdy, n_d, 1]] 
            n_d +=1
    
    if (cur_mo <11):
        l_d =  get_num_days(cur_mo+1)
        if (date(cur_year,cur_mo+1,l_d).weekday() != 6):
            o = 1
            wn = 6 - date(cur_year,cur_mo+1,l_d).weekday()
            while (wn > 0):
                wkdy = date(cur_year,cur_mo+2,o).weekday() 
                c_wday = c_wday + [[wkdy, o, (cur_mo+2)]]
                o +=1
                wn-=1
    elif (cur_mo == 11):
        if (date(cur_year, 12, 31).weekday() !=6):
            o = 1
            wn = 6 - date(cur_year, 12, 31).weekday()
            while (wn > 0):
                wkdy = date(cur_year+1,1,o).weekday() 
                c_wday = c_wday + [[wkdy, o, 1]]
                o +=1
                wn -=1
    elif (cur_mo == 12):
        if (date(cur_year+1, 1, 31).weekday() !=6):
            o = 1
            wn = 6 - date(cur_year+1, 1, 31).weekday()
            while (wn > 0):
                wkdy = date(cur_year+1,2,o).weekday() 
                c_wday = c_wday + [[wkdy, o, 2]]
                o +=1
                wn -=1
    return c_wday

@app.template_filter()
@evalcontextfilter
def nl2br(value):
    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
    for p in _paragraph_re.split(escape(value)))
    return result

#entries section
def get_entries():
    db = get_db()
    cur = db.execute('select id from entries')
    entries = cur.fetchall()
    if ( not entries):
        init_db()
    cur = db.execute('select id, nath, mplace, mmonth, mday, mtime, telephone from entries order by mday asc')
    entries = cur.fetchall()
    return entries

@app.route('/')
def show_entries():
    if (not get_entries()):
        init_db()
    entries = get_entries()
    dc = get_date_array()
    t_cords = [cur_day, cur_mo, cur_year]
    return render_template('show_entries.html', entries=entries, dc=dc, t_c = t_cords)

@app.route('/add', methods =['POST'])#, methods=['get']
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
#    db.execute('insert into entries (nath, mplace, mmonth, mday, mtime, telephone) values (?, ?, ?, ?, ?, ?)', [request.args.get('nath',0,type=str), request.args.get('mplace',0,type=str), request.args.get('mmonth',0,type=str), request.args.get('mday',0,type=str), request.args.get('mtime',0,type=str), request.args.get('telephone',0,type=str)])
    db.execute('insert into entries (nath, mplace, mmonth, mday, mtime, telephone) values (?, ?, ?, ?, ?, ?)', [request.form['nath'], request.form['mplace'], request.form['mmonth'], request.form['mday'], request.form['mtime'], request.form['telephone']])
    db.commit()
    return redirect(url_for('show_entries'))

@app.route('/remove')
def delete_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    id = request.args.get('id', 0, type=int)
    db.execute('delete from entries where id = (?)', [request.args.get('id', 0, type = int)])
    db.commit()
    flash('Another entry had been removed')
    return jsonify(result = id)

#art section
def get_art():
    db = get_db()
    cur = db.execute('select id, poetryname, poetry from art order by id asc')
    art = cur.fetchall()
    return art

@app.route('/art')
def show_art():
    art = get_art()
    return render_template('show_art.html', art =art)

@app.route('/add_art', methods = ['POST'])
def add_art():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into art (poetryname, poetry) values (?, ?)', [request.form['poetryname'], \
            nl2br(request.form['poetry'])  ])
    db.commit()
    return redirect(url_for('show_art'))

@app.route('/remove_art', methods=['POST'])
def remove_art():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from art where id = (?)', [request.args.get('id',0,type = int)])
    db.commit()
    return  redirect(url_for('show_art'))


#login section
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__=='__main__':
    app.run()
