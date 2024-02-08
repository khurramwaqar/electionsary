from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, session, send_from_directory
import requests
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import config
from werkzeug.utils import secure_filename
import os
from os.path import join, dirname, realpath

main = Blueprint('main', __name__)


mysql = MySQL()

CANDIDATES_IMAGES = join(dirname(realpath(__file__)), 'static/images/candidates-images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg',}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

VIDEO_API_KEY = 'AIzaSyCGBvI2vs8xfLmgRvjXTGMBSnxeOOw7Ph0'
VIDEO_API_ENDPOINT = 'https://www.googleapis.com/youtube/v3/playlistItems?part=status,snippet,id,contentDetails&playlistId=PLS19FEYA85DiTQxRAxitaVdJk-8ffSHTH&maxResults=10'
VIDEO_API_ENDPOINT2 = 'https://www.googleapis.com/youtube/v3/playlistItems?part=status,snippet,id,contentDetails&playlistId=PLS19FEYA85DhRchJtJKmh_q6qncBvdL7c&maxResults=10'

# Initialize a variable to store the cached data
cached_api_data1 = None 
cached_api_data2 = None 

@main.route('/sitemap.xml')
def sitemap():
    return send_file('static/sitemap.xml', mimetype='text/xml')

# function for youtube api 
def fetch_data():
    global cached_api_data1
    global cached_api_data2
    try:
        # Make the API request
        response = requests.get(VIDEO_API_ENDPOINT, params={'key': VIDEO_API_KEY})
        response.raise_for_status()  # Raise an error for bad responses
        Halqa_Siyasat = response.json()
        response = requests.get(VIDEO_API_ENDPOINT2, params={'key': VIDEO_API_KEY})
        response.raise_for_status()  # Raise an error for bad responses
        General_Elections_2024 = response.json()        

        # Update the cached data        
        cached_api_data1 = General_Elections_2024
        cached_api_data2 = Halqa_Siyasat
        
        print("Videos refreshed successfully.")

    except Exception as e:
        print(f"Error fetching data: {e}")


election_faqs = [
    {"question": "What is the minimum age for becoming a candidate for the National Assembly of Pakistan?", "answer": "25 years."},
    {"question": "What is the minimum age for becoming a candidate for a Provincial Assembly?", "answer": "25 years."},
    {"question": "What is the minimum age for becoming a candidate for the office of the President?", "answer": "45 years."},
    {"question": "What is the minimum age for becoming a candidate for the office of the Prime Minister?", "answer": "Above 25 years."},
    {"question": "What are the basic requirements to assume the office of the Prime Minister?",
     "answer": "- A Pakistani Citizen.<br> - Be a Muslim.<br> - Be a member of the National Assembly.<br> - Be above 25 years of age.<br> - Able to provide a good conduct of character and is not commonly known as one who violates Islamic Injunctions.<br> - Adequate knowledge of Islamic teachings and practices obligatory duties prescribed by Islam as well as abstains from major sins.<br> - Has not, after the establishment of Pakistan, worked against the integrity of the country or opposed the ideology of Pakistan."},
    {"question": "Can I file an objection against the enrollment of any other person?", "answer": "Yes, if you are a registered voter of the same electoral area."},
    {"question": "Can a convicted and previously imprisoned offender contest elections?",
     "answer": "No, if a person is sentenced to imprisonment for at least two years, he cannot contest any election unless a period of five years has elapsed since his release."},
    {"question": "Can a person holding public office or in the service of Pakistan living away from their enrolled district vote through postal ballot if they cannot vote in person?",
     "answer": "Yes, a person in the service of Pakistan or holding a public office can vote through postal ballot paper if he/she wishes to cast their vote at the constituency of their hometown."},
    {"question": "Can family members of government servants who have been posted away from their enrolled constituency also cast their vote by postal ballot?",
     "answer": "Yes, they can if they are registered as voters."},
    {"question": "How can polling personnel/staff cast their votes?", "answer": "They can also cast their votes through postal ballots within the dates specified by the Election Commission."},
    {"question": "Are overseas Pakistanis eligible to vote?",
     "answer": "Overseas Pakistanis who are present in Pakistan at the time of the election can cast their vote at the polling station concerned if they are registered as voters. However, voting from aboard is not permissible under the law."},
    {"question": "What is the security deposit required for the election to the National Assembly?", "answer": "Rupees Four thousand only."},
    {"question": "What is the security deposit for the election to the Provincial Assembly?", "answer": "Rupees Two thousand only."},
    {"question": "Are the above-mentioned security deposits refundable?",
     "answer": "Yes, the security deposits are refundable within six months; otherwise, it shall be forfeited."},
    {"question": "In what case does a candidate lose his/her security deposit?",
     "answer": "A defeated candidate who receives less than one-eighth of the total number of votes cast at the election loses his/her security deposit."},
    {"question": "Can a person contest the election to the National Assembly from as many constituencies as he/she wants?", "answer": "Yes."},
    {"question": "Can a person retain more than one seat in the National Assembly if he/she is elected to all seats that he/she ran for?",
     "answer": "No, he/she has to resign from all seats except one."},
    {"question": "If a person is elected from the National Assembly as well as a Provincial Assembly seat, can he/she retain both the seats?",
     "answer": "No, he/she must resign one of the seats."},
    {"question": "What is the number of proposers and seconders required for subscribing to the nomination of a candidate?",
     "answer": "For each nomination, one proposer and one seconder are required."},
    {"question": "Who can be the proposer or a seconder?", "answer": "Any voter of that constituency can propose or second a nomination."},
    {"question": "How many voters are normally assigned to a particular polling station to vote?",
     "answer": "Normally 1000-1200 voters are assigned to each polling station. However, in exceptional cases, such a number may go up to 1500."},
    {"question": "How far can a polling station be from your house?",
     "answer": "Efforts are made to assign voters to the nearest polling station. However, in some cases, the distance may be about two kilometers."},
    {"question": "How many polling booths are required to be set up in each polling station?",
     "answer": "The polling booths are made keeping in view the number of total voters assigned to that polling station. However, normally two to four polling booths are set up at a polling station."},
    {"question": "Are there separate polling booths for male and female voters?", "answer": "Yes. The female voters are assigned separate polling booths in each polling station."},
    {"question": "How many nomination papers can be filed by a candidate?", "answer": "Not more than five in one constituency."},
    {"question": "Is it necessary to deposit a security fee for each nomination paper?",
     "answer": "No, security once deposited is enough for all the nominations for that constituency."},
    {"question": "Are female polling staff appointed for the female booths in polling stations?",
     "answer": "Yes, separate female polling staff is appointed at polling booths in urban areas. But in rural areas, sometimes female polling staff is not available. Therefore, elderly male staff is appointed at such booths catering to female voters."},
    {"question": "Are separate polling stations set up for female voters?",
     "answer": "Yes. Separate polling stations are set up for female voters in urban areas, but it is not possible to set up female polling stations in rural areas due to the non-availability of female staff. However, separate female booths within rural polling stations are provided for female voters."},
    {"question": "How can a candidate withdraw from the contest?",
     "answer": "A validly nominated candidate can withdraw his candidacy by submitting a notice in writing signed by him and delivered to the Returning Officer on or before the withdrawal date fixed by the Election Commission."},
    {"question": "Can a notice of withdrawal be canceled?", "answer": "No. A notice of withdrawal, in no circumstances, can be recalled or canceled."},
    {"question": "How can a contesting candidate retire from an election?",
     "answer": "A contesting candidate may retire from the contest by a notice in writing signed by him and delivered to the Returning Officer on any day not later than four days before the polling day."},
    {"question": "Can a notice of retirement be delivered by any person other than the candidate?",
     "answer": "Yes, an agent authorized in writing by such a candidate can submit the notice of retirement to the Returning Officer."},
    {"question": "Can a voter mark a ballot paper in the open in front of other people sitting in the polling station?",
     "answer": "No. Under the Constitution, elections are to be held by secret ballot. Therefore, the voter is required to mark/stamp the ballot paper in the screened-off compartment in the polling station not in view of any other individuals or polling staff."},
    {"question": "How can a blind or incapacitated person vote?",
     "answer": "If an elector is totally blind or otherwise so incapacitated as to require the help of a companion, the Presiding Officer may allow him to be accompanied by a companion provided that the companion is neither a candidate nor an agent of a candidate."},
    {"question": "If I go to a polling station and find that somebody else has impersonated and cast a vote in my place, what can I do?",
     "answer": "The matter should be brought to the notice of the Presiding Officer who, after satisfying himself, will issue a ballot paper called as “tendered ballot paper” in the same manner as ballot papers are issued to other electors. The tendered ballot paper shall be kept separately after it is marked by the voter. Tendered ballots are not counted."},
    {"question": "Can a person at the polling station cast their vote after the closing hour of the poll?",
     "answer": "Any person present within the building, room, tent, or enclosure in which the polling station is situated and is waiting to vote will be allowed to cast a vote even after the hour fixed for the close of the poll."},
    {"question": "If a contesting candidate is not satisfied with the result of an election, what recourse does he/she have to lodge their objections?",
     "answer": "A candidate can call an election in question by filing an election petition in the manner prescribed under the law. The election petitions will be heard and decided by the Election Tribunals appointed by the Chief Election Commissioner."},
    {"question": "If you are offered money to vote for a particular candidate, should you accept that money and vote?",
     "answer": "No. This is an illegal practice. The person offering the money and the recipient are carrying out an illegal act. The exchange of such money is a corrupt practice which is punishable with imprisonment for a term of three years or with a fine up to five thousand rupees for both."},
    {"question": "When can an election petition be filed?",
     "answer": "The election petition can be filed within 45 days of the publication of the names of returned candidates in the official gazette."},
    {"question": "Who can be appointed to an Election Tribunal?", "answer": "Normally, sitting Judges of the High Courts are appointed to the Election Tribunal."},
    {"question": "Is the decision of the Election Tribunal final?",
     "answer": "The decision of the Election Tribunal is appealable before the Supreme Court of Pakistan."}
]


# Home Route 
@main.route('/')
def home():
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    cursor.execute('SELECT * FROM `na_seats_24`;')
    seats = cursor.fetchall()
    news_video_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=status,snippet,id,contentDetails&playlistId=PLS19FEYA85DiTQxRAxitaVdJk-8ffSHTH&key=AIzaSyCGBvI2vs8xfLmgRvjXTGMBSnxeOOw7Ph0&maxResults=10"
    news_api_url = "https://arynews.tv/api/jsonify.php?count=9&post_type=post&cat=elections-2024&tax=post_tag"
    # Set the User-Agent header
    headers = {"User-Agent": "Mozilla/4.0"}	
    response = requests.get(news_api_url,headers=headers)
    response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
    news_json = response.json()
    videos_json1 = cached_api_data1
    videos_json2 = cached_api_data2
    
    

    return render_template('home.html',news_json=news_json['specific_post'],videos_json1=videos_json1,videos_json2=videos_json2,faqs=election_faqs,seats=seats)

@main.route('/constituencies/<string:type>/<string:year>')
def constituencies(type,year):
    if type == "national" and year == "2024":
        #Executing SQL Statements	
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `natconstituency` WHERE Year=%s;',(year,))
        constituencies_list = cursor.fetchall()
        for constituency in constituencies_list:
            cursor = mysql.connection.cursor(cursorclass=DictCursor)
            cursor.execute('SELECT constituency FROM `proconstituency` WHERE na_const_id= %s and Year = %s;',(constituency['constituencyID'],year))        
            proconstituencies = cursor.fetchall()
            constituency['proconstituency'] = proconstituencies
            cursor.execute('SELECT voters from `na_info` WHERE na_id=%s;',(constituency['constituencyID'],))
            voters = cursor.fetchone()            
            constituency['voters'] = voters
            # if voters:
            #     constituency['voters'] = voters['voters']
        return render_template('national-constituencies.html',data=constituencies_list,type=type,total_seats = len(constituencies_list))
    elif type == "punjab" and year == "2024":
        provinceid= 3 #Punjab
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `proconstituency` WHERE year=%s and ProvinceID=%s;',(year,provinceid))
        constituencies_list = cursor.fetchall()
        province_short = "PP"
        return render_template("provistional-constituencies.html",type=type,data = constituencies_list,total_seats=len(constituencies_list),province_short=province_short)
    elif type == "sindh" and year == "2024":
        provinceid= 2 #Sindh
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `proconstituency` WHERE year=%s and ProvinceID=%s;',(year,provinceid))
        constituencies_list = cursor.fetchall()
        province_short = "PS"
        return render_template("provistional-constituencies.html",type=type,data = constituencies_list,total_seats=len(constituencies_list),province_short=province_short)
    elif type == "kpk" and year == "2024":
        provinceid= 1 #kpk
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `proconstituency` WHERE year=%s and ProvinceID=%s;',(year,provinceid))
        constituencies_list = cursor.fetchall()
        province_short = "PK"
        return render_template("provistional-constituencies.html",type=type,data = constituencies_list,total_seats=len(constituencies_list),province_short=province_short)
    elif type == "balochistan" and year == "2024":
        provinceid= 4 #balochistan
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `proconstituency` WHERE year=%s and ProvinceID=%s;',(year,provinceid))
        constituencies_list = cursor.fetchall()
        province_short = "PB"
        return render_template("provistional-constituencies.html",type=type,data = constituencies_list,total_seats=len(constituencies_list),province_short=province_short)

    else:
        return redirect(url_for('main.not_found'))


@main.route('/political-parties')
def politicalparties():
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    cursor.execute('SELECT PartyID,Party_Name,party_shortname FROM `parties`;')
    parties = cursor.fetchall() 

    return render_template('political-parties.html',parties=parties)


@main.route('/infographics')
def infographics():
    return render_template('info-graphics.html')

@main.route('/manifestos')
def manifestos():
    return render_template('manifestos.html')

@main.route('/results')
def results():
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    cursor.execute('SELECT provinceID,pName FROM `province`;')
    provinces = cursor.fetchall() 
    default_province = None
    if request.args.get("p"):
        province_id = int(request.args.get("p"))
        default_province = {"provinceID":province_id,"pName":provinces[province_id-1]['pName']} 
    return render_template('result.html',provinces=provinces,default_province=default_province)

def get_total_votes(entry):
    total_votes_str = entry['total_votes']
    return int(total_votes_str) if total_votes_str is not None else 0

@main.route('/results/<int:year>')
def results_updated(year):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)   
    if year==2018:
        cursor.execute('SELECT * FROM `natconstituency` WHERE year=%s;', (year,))
        natconstituency = cursor.fetchall()
        for constituency in natconstituency:
            cursor.execute('SELECT * FROM `na_info` WHERE na_id = %s;', (constituency['constituencyID'],))
            na_info = cursor.fetchone()
            constituency['na_info'] = na_info

            cursor.execute('SELECT Winner FROM `naresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
            winner = cursor.fetchone()['Winner']
            constituency['winner'] = winner
    elif year == 2024:
        cursor.execute('SELECT * FROM `natconstituency` WHERE year=%s;', (year,))
        natconstituency = cursor.fetchall()
        for constituency in natconstituency:

            cursor.execute('SELECT candidate_name,party_abv,votes FROM `candidates_24` WHERE cons_name=%s ORDER BY votes DESC LIMIT 1',(constituency["constituency"],))
            leading = cursor.fetchone()

            
            
            cursor.execute('SELECT SUM(`votes`) AS `total_votes` FROM `candidates_24` WHERE `cons_name` = %s',(constituency["constituency"],))
            total_votes = cursor.fetchone()['total_votes']            

            if total_votes:
                turnout = int(total_votes) / int(constituency['reg_voters']) * 100
            else:
                turnout = 0
            if leading['votes'] != None:
                constituency['leading_candidate'] = leading['candidate_name']
                constituency['leading_party'] = leading['party_abv']
                constituency['leading_votes'] = leading['votes']
            else:
                constituency['leading_candidate'] = ""
                constituency['leading_party'] = ""
                constituency['leading_votes'] = ""
            constituency['total_votes'] = total_votes
            constituency['turnout'] = turnout
        natconstituency = sorted(natconstituency, key=get_total_votes, reverse=True)

            # cursor.execute('SELECT Winner FROM `naresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
            # winner = cursor.fetchone()['Winner']
            # constituency['winner'] = winner
    else:
        return redirect(url_for('main.not_found'))
    
    
    return render_template("results_updated.html", data=natconstituency, year=year)

@main.route('/provincial-results/<string:province>/<int:year>')
def provincial_results_updated(province,year):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    province = province.lower()
    province_mapping = {"sindh":"PS","kpk":"PK","punjab":"PP","balochistan":"PB"}

    # if year == 2018 and province in province_mapping:
    #     cursor.execute('SELECT provinceID FROM `province` WHERE pName=%s;',(province,))
    #     provinceID = cursor.fetchone()['provinceID']
    #     print(provinceID)
    #     cursor.execute('SELECT * FROM `proconstituency` WHERE provinceID = %s and year=%s;', (provinceID, year))
    #     proconstituency = cursor.fetchall()
    #     for constituency in proconstituency:
    #         cursor.execute('SELECT Winners FROM `proresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
    #         winner = cursor.fetchone()
    #         constituency['winner'] = winner
    if year == 2024 and province in province_mapping:
        cursor.execute('SELECT provinceID FROM `province` WHERE pName=%s;',(province,))
        provinceID = cursor.fetchone()['provinceID']
        print(provinceID)
        cursor.execute('SELECT * FROM `proconstituency` WHERE provinceID = %s and year=%s;', (provinceID, year))
        proconstituency = cursor.fetchall()
        for constituency in proconstituency:
            cursor.execute('SELECT Winners FROM `proresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
            winner = cursor.fetchone()
            constituency['winner'] = winner
    else:
        return redirect(url_for('main.not_found'))

    # return jsonify(proconstituency)
    return render_template("provincial-results.html",province=province, data=proconstituency, year=year,code = province_mapping[province])


# single constituency 
@main.route("/constituency/<string:type>-<int:constituency_number>/<int:year>")
def single_constituency(type,constituency_number, year):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    # province_mapping = {"PK": ("kpk", 1), "PP": ("punjab", 3), "PS": ("sindh", 2), "PB": ("balochistan", 4)}    
    province_mapping = {"PK":1,"PP":3,"PS":2,"PB":4}
    
    if type=="NA" and year == 2024:
        cursor.execute('SELECT * FROM `natconstituency` WHERE constituency=%s and year = %s;',(type+"-"+str(constituency_number),year))
        data = cursor.fetchone()

        query = 'SELECT * FROM `candidates_24` WHERE cons_name=%s ORDER BY `votes` DESC;'
        cursor.execute(query, (data['constituency'],))
        candidates = cursor.fetchall()       
        cursor.close()
        return render_template("single-constituency-national.html",data = data,candidates=candidates,year=year)
    elif type=="NA" and year == 2018:
        cursor.execute('SELECT * FROM `natconstituency` WHERE constituency=%s and year = %s;',(type+"-"+str(constituency_number),year))
        data = cursor.fetchone()

        query = 'SELECT * FROM `candidates_24` WHERE cons_name=%s;'
        cursor.execute(query, (data['constituency'],))
        candidates = cursor.fetchall()        
        cursor.close()
        return render_template("single-constituency-national.html",data = data,candidates=candidates,year=year)
    
    #kpk sindh punjab balochistan
    elif type in province_mapping and year == 2024:
        province_id = province_mapping[type]        
        cursor.execute('SELECT * FROM `proconstituency` WHERE constituency= %s and Year = %s and provinceID=%s;',(type+"-"+str(constituency_number),year,province_id))
        data = cursor.fetchone() 

        query = 'SELECT * FROM `candidates_24` WHERE cons_name=%s ORDER BY `votes` DESC;'
        cursor.execute(query, (data['constituency'],))
        candidates = cursor.fetchall()  
        cursor.close()     
        return render_template("single-constituency-provistional.html", data = data,candidates=candidates)
    else:
        return redirect(url_for('main.not_found'))


# party candidates 
@main.route('/party-candidates/<int:party_id>')
def party_canditates(party_id):
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    cursor.execute('SELECT * FROM `parties` WHERE partyID=%s;',(party_id,))
    party = cursor.fetchone()
    if party['party_shortname'] == "PTI":
        party_shortname = "PTI-IND"
    else:
        party_shortname = party['party_shortname']
    cursor.execute('SELECT * from `candidates_24` WHERE party_abv=%s;',(party_shortname,))    
    party_candidates = cursor.fetchall()
    for i in party_candidates:
        cursor.execute('SELECT Name from `natconstituency` WHERE constituency=%s and year=2024;',(i['cons_name'],))         
        cons_name = cursor.fetchone() 
        if not cons_name:
            cursor.execute('SELECT Name from `proconstituency` WHERE constituency=%s and year=2024;',(i['cons_name'],))         
            cons_name = cursor.fetchone()

        i['con']= cons_name['Name'] 
    return render_template("party-candidates.html",party=party, party_candidates=party_candidates,party_id=party_id)

# todo 
@main.route("/share-national")
def share_national():
    return render_template("share-template-national.html")

# 404 handler route 
@main.route("/not-found")
def not_found():
    return render_template("not-found.html")


##################################################### APIS #################################################



@main.route('/get-constituency-data-from-search/<string:constituency_name>')
def get_constituency_data_from_search(constituency_name):
    year = 2018
    constituency_name = constituency_name.upper().replace(" ","")
    constituency_name = constituency_name.replace("-","")
    constituency_name = constituency_name[:2] + '-' + constituency_name[2:]

    # Execute SQL query
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    cursor.execute('SELECT * FROM `natconstituency` WHERE constituency = %s and year=%s;', (constituency_name, year))
    constituency = cursor.fetchone()

    # cursor = mysql.connection.cursor(cursorclass=DictCursor)
    # cursor.execute('SELECT * FROM `natconstituency` WHERE constituency = %s and year=%s;', (constituency_name,year))
    # constituency = cursor.fetchone()

    
    cursor.execute('SELECT * FROM `na_info` WHERE na_id = %s;', (constituency['constituencyID'],))
    na_info = cursor.fetchone()
    constituency['na_info'] = na_info

    cursor.execute('SELECT Winner FROM `naresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
    winner = cursor.fetchone()['Winner']
    constituency['winner'] = winner
    return jsonify(constituency)


@main.route('/get-constituency-data/<string:province_id>')
def get_constituency_data(province_id):
    year = 2018
    cursor = mysql.connection.cursor(cursorclass=DictCursor)
    
    try:
        cursor.execute('SELECT * FROM `natconstituency` WHERE provinceID = %s;', (province_id,))
        natconstituency = cursor.fetchall()
        for constituency in natconstituency:
            cursor.execute('SELECT * FROM `na_info` WHERE na_id = %s;', (constituency['constituencyID'],))
            na_info = cursor.fetchone()
            constituency['na_info'] = na_info

            cursor.execute('SELECT Winner FROM `naresults` WHERE Constituency=%s AND Year=%s;',(constituency['constituency'],year))
            winner = cursor.fetchone()['Winner']
            constituency['winner'] = winner
    except Exception as e:
        return str(e)        

    finally:
        cursor.close()    
        return jsonify(natconstituency)
    
@main.route('/download-ost')
def download_ost():
    mp3_file_path = 'static/ost/ost.wav'  # Update with your actual file path

    # You can add more options to send_file if needed, such as specifying a different filename for download
    return send_file(mp3_file_path, as_attachment=True, download_name="Niklo Pakistan Ki Khatir - Sahir Ali Bagha - ARY Election Song.wav")


@main.route('/download-result/NA-<int:digit>')
def download_national_result(digit):
    # todo 
    pass







# call the function 
fetch_data()

# Background Scheduler 
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_data, trigger="interval", minutes=60)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())



# admin dash backend 
@main.route('/admin-dashboard', methods = ['POST','GET'])
def admin_dashboard():
    if 'loggedin' in session:
        return render_template("/admin/home.html")
    else:
        return redirect(url_for('main.admin_login'))
    
@main.route('/admin/update/<string:type>', methods = ['POST','GET'])
def admin_update(type):
    if 'loggedin' in session:
        limit = {'na':266,'pk':115,'pp':297,'ps':130,'pb':51}
        if "search" in request.args:
            search = int(request.args["search"])
            code = type.upper()+"-"
            constituency = code+str(search)

            cursor = mysql.connection.cursor(cursorclass=DictCursor)
            cursor.execute('SELECT ca_id,candidate_name,party,party_abv,votes,img FROM `candidates_24` WHERE cons_name=%s;',(constituency,))
            candidates_list = cursor.fetchall()
            return render_template("/admin/update.html",candidates_list=candidates_list,constituency=constituency,type=type,limit=limit)
        return render_template("/admin/update.html",type=type,limit=limit)
    else:
        return redirect(url_for('main.admin_login'))
    
@main.route("/admin/update-votes/<string:type>",methods=['POST'])
def admin_update_votes(type):
    if 'loggedin' in session:        
        code = type.upper()+"-"
        if request.method == "POST":
            constituency = request.form.get('constituency')
            candidate_id = request.form.get('candidate_id')
            votes = request.form.get('votes')
            
            cursor = mysql.connection.cursor(cursorclass=DictCursor)
            image = request.files["image"]                
            if image and allowed_file(image.filename):
                if image.content_length <= 1048576:
                    extension = os.path.splitext(image.filename)[1].lower()
                    filename = secure_filename(str(candidate_id)+extension)
                    image.save(os.path.join("static","candidates-images",filename))
                    cursor.execute('UPDATE candidates_24 SET votes = %s,img=%s WHERE ca_id=%s;',(votes,filename,candidate_id))
                else:
                    print("Image size exceeds 1MB limit.")                    
                    return redirect("/admin/update?search="+constituency.replace(code,""))
                    
            else:
                cursor.execute('UPDATE candidates_24 SET votes = %s WHERE ca_id=%s;',(votes,candidate_id))
            mysql.connection.commit()
            return redirect("/admin/update/"+type+"?search="+constituency.replace(code,""))

@main.route("/admin/na-seats",methods=['GET','POST'])
def admin_na_seats():
    if 'loggedin' in session: 
        if request.method == "POST":
            party_id = request.form.get("party_id")
            seats = request.form.get("seats")
            cursor = mysql.connection.cursor(cursorclass=DictCursor)
            cursor.execute('UPDATE na_seats_24 SET seats = %s WHERE id=%s;',(seats,party_id))
            mysql.connection.commit()
            return redirect(url_for("main.admin_na_seats"))
        cursor = mysql.connection.cursor(cursorclass=DictCursor)
        cursor.execute('SELECT * FROM `na_seats_24`;')
        parties = cursor.fetchall()
        return render_template("/admin/na-seats.html",parties=parties)
    else:
        return redirect(url_for('main.admin_login'))  


@main.route("/admin/login", methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get("username")
        password  = request.form.get("password")
        if username == config.USERNAME and password == config.PASSWORD:
            session['loggedin'] = True
            session['name'] = username
            return redirect(url_for("main.admin_dashboard"))
        else:
            return render_template("admin/login.html",error="Invalid Credentials!")
        
    return render_template("admin/login.html")

@main.route("/admin/logout")
def admin_logout():
    session.pop('loggedin', None)
    session.pop('name', None)
    # Redirect to index page
    return redirect(url_for('main.admin_dashboard'))