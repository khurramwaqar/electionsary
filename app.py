from flask import Flask, request, render_template, send_from_directory
from main.routes import main
# from admin.routes import admin
import config
from flask_mysqldb import MySQL

app = Flask(__name__)

# BASE CONFIG 
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'electionsarynews_zamanat'
# app.config['MYSQL_PASSWORD'] = 'PHtn?pDSyIg$'
# app.config['MYSQL_DB'] = 'electionsarynews_elections2024'

# app.config.from_object(config.BaseConfig)
# DOMAIN = "https://elections.arynews.tv"

# DEV CONFIG 
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'elections.arynews.tv'

# app.config.from_object(config.DevelopmentConfig)
# DOMAIN = "http://localhost:5000/"


# mysql = MySQL(app)

app.config['MYSQL_HOST'] = 'ns3153983.ip-51-91-244.eu'
app.config['MYSQL_USER'] = 'strapi'
app.config['MYSQL_PASSWORD'] = '0j#4J2h4u'
app.config['MYSQL_DB'] = 'strapi'

app.config.from_object(config.DevelopmentConfig)
DOMAIN = "http://localhost:5000/"


mysql = MySQL(app)
 

app.register_blueprint(main, url_prefix='/')
# app.register_blueprint(admin, url_prefix='/admin')

@app.context_processor
def inject_active_page():
    # Get the last part of the endpoint (route) after the dot
    active_page = request.endpoint.split('.')[-1] if request.endpoint else None
    return {'active_page': active_page}

@app.context_processor
def inject_domain():    
    return dict(domain=DOMAIN)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('not-found.html'), 404

# @app.errorhandler(Exception)
# def general_error(error):
#     return render_template('error.html', error=error), 500






