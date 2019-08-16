from flask import Flask, request, url_for, jsonify
from mtgsdk import Card
from threading import Thread
import requests
import json

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('CARDFETCH_SETTINGS', silent=True)

@app.route('/', methods=['POST'])
def card_fetch():
    token = request.form.get('token', None)
    command = request.form.get('command', None)
    text = request.form.get('text', "")
    responseURL = request.form.get('response_url', None)
    user = request.form.get('user_name', "")

    flavor = "finding "+text.replace('-g', 'golden')+" for "+user+"..."

    ret = jsonify(response_type="in_channel", text=flavor)

    if command == "/mtg":
        t = Thread(target=do_mtg_search, args=(app, responseURL, text))
        t.start()
        return ret

    if command == "/hs":
        gold = False
        if text.find("-g ") != -1:
            gold = True
            text = text.split(maxsplit=1)[1]

        t = Thread(target=do_hs_search, args=(app, responseURL, text, gold))
        t.start()
        return ret

    return "command not recognized."


def do_hs_search(app, responseURL, searchTerm, gold):
    with app.app_context():
        with app.test_request_context():
            ret = "card not found."

            name = None
            imgurl = None

            response = requests.get("https://omgvamp-hearthstone-v1.p.mashape.com/cards/"+searchTerm, headers={"X-Mashape-Key": "WaPqRvu4Mdmsh8aFptRJeKeNOw42p1dpygSjsnvIBQKFYaMHsc", "Accept": "application/json"})
            if response.status_code is 200:
                r = []
                for result in response.json():
                    if 'img' in result.keys():
                        r = result
                        break
                
                key = 'img'
                name = r['name']
                if gold is True:
                    key = 'imgGold'
                    name = "Gold "+name

                imgurl = r[key]
                if imgurl == "":
                    ret = "No image url found."
                else:
                    ret = ""

            requests.post(responseURL, headers={"Content-Type":"application/json"}, data=json.dumps({ "response_type" : "in_channel", "text" : ret, "attachments" : [{"image_url" : imgurl, "title" : name}] }))


def do_mtg_search(app, responseURL, searchTerm):
    with app.app_context():
        with app.test_request_context():
            retTotal = ""
            for term in searchTerm.split(","):
                term = term.strip()
                ret = term + " not found."
                found = False
                query = Card.where(pageSize=1).where(page=1)
                query.params['contains']='multiverseid,imageUrl'
                query.params['orderBy']='multiverseid desc'
                
                img = ""

                for c in Card.where(pageSize=10).where(page=1).where(name="\""+term+"\"").all():
                    if c.image_url != None:
                        img = c.image_url
                        if '//' in c.name:
                            img = img + "&options=rotate90"
                        ret = "<"+img+"|"+c.name+">"
                        found = True
                        break

                if found is False:
                    for c in Card.where(pageSize=10).where(page=1).where(name=term).all():
                            if c.image_url != None:
                                img = c.image_url
                                if '//' in c.name:
                                    img = img + "&options=rotate90"
                                ret = "<"+img+"|"+c.name+">"
                                break

                retTotal = retTotal + ret + " "

            requests.post(responseURL, headers={"Content-Type":"application/json"}, data=json.dumps({ "response_type" : "in_channel", "text" : retTotal }))
