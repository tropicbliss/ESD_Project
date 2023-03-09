from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from os import environ

# cool
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/groomer'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
CORS(app)

class Groomer(db.Model):
    __tablename__ = 'groomer'
    groomerId = db.Column(db.String(13), primary_key=True)
    groomerName = db.Column(db.String(100), nullable=False)
    groomerPicURL = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer)
    address = db.Column(db.String(150), nullable=False)
    contactNo = db.Column(db.Integer)
    email = db.Column(db.String(100), nullable=False)
    acceptablePetType = db.Column(db.String(100), nullable=False)
    membershipTier  = db.Column(db.String(100), nullable=False)


    def __init__(self, groomerId, groomerName, groomerPicURL, capacity, address, contactNo, email, acceptablePetType, membershipTier):
        self.groomerId = groomerId
        self.groomerName = groomerName
        self.groomerPicURL = groomerPicURL
        self.capacity = capacity
        self.address = address
        self.contactNo = contactNo
        self.email = email
        self.acceptablePetType = acceptablePetType
        self.membershipTier = membershipTier



    def json(self):
        return {"groomerId": self.groomerId, "groomerName": self.groomerName, "groomerPicURL": self.groomerPicURL, "capacity": self.capacity, "address": self.address,"address": self.address, "contactNo": self.contactNo, "acceptablePetType": self.acceptablePetType, "membershipTier": self.membershipTier}

        
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
engine = create_engine('mysql+mysqlconnector://root@localhost:3306/groomer', echo = True)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind = engine)
session = Session()


#populating table with data
# g1= Groomer (groomerId= 58723, groomerName='Purrfect Grooming', groomerPicURL='https://uploads-ssl.webflow.com/6139cf517cd6d2b4af548b94/613a19d4ea090fe88fee09ca_pet-hotel-780x440.jpeg', capacity= 15, address='123 Bukit Timah Road, Singapore', contactNo= 67891234, email= 'info@purrfectgrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# session.add(g1)
# session.commit()

# g2= Groomer (groomerId= 23654, groomerName='The Poodle Parlour', groomerPicURL='https://hips.hearstapps.com/edc.h-cdn.co/assets/17/02/2560x1899/best-dog-boarding-d-hotel.jpg?resize=980:*', capacity= 10, address='10 Jalan Besar, Singapore', contactNo= 98765432, email= 'info@poodleparlour.com.sg', acceptablePetType='dogs', membershipTier='General')

# g3= Groomer (groomerId= 87521, groomerName='Furry Friends Spa', groomerPicURL='https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d67b1adc75e74bf2ec_P9izERWKJMy3WtCFXcTeHVGpTtFBSHNvzNYqVX25S-HpTiyiehbxShWAEjDx_wQM5oMIwXlRjyLeqTIoNsPArfbNA85DMDIHBZaMMmtW_5CdXhdpojsgqtsuQZdqP_KuqPwem7fdctcoN61r-wYrzqw.png', capacity= 20, address='45 East Coast Road, Singapore', contactNo= 87654321, email= 'info@furryfriendsspa.com.sg', acceptablePetType='cats', membershipTier='General')

# g4= Groomer (groomerId= 41236, groomerName='Happy Tails Grooming', groomerPicURL= 'https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d6c0f79321c09de4d9_ElKiF-ZwAmb8Vc3FMu1LqGMknFgwOIcrnM8b-yQI3TzRZ-NWYp_tMPYEfbuKckagF4u7d7NUn3eo0sjt072HFvfzbA2iXPv47S6yMGGusSNllyXicoPxQ4QCB8jNMKskd0rjQ4a13_CnyjE7WCSGQ9g.png', capacity= 12, address='1 Jurong West Avenue, Singapore', contactNo= 65432109, email= 'info@happytailsgrooming.com.sg', acceptablePetType='dogs', membershipTier='General')

# g5= Groomer (groomerId= 93217, groomerName='Pawfection Grooming', groomerPicURL='https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fb52ea65865b5c2b38e013_Mxhlj6pWRRDYS2twyi_jW6kTCFF9EhUZFaaCVUB7C55_XO2m8eFTTyiVsP_7Ia7u6qYGtaF2ykyUJROsw0Zhu5ly8KZHmtInBHBtMCD_f3WfVq2UZGgxPN-aAFazPpscaFVHa4B0qPi4jNADNj6qX2A.png', capacity= 18, address='77 Serangoon Road, Singapore', contactNo= 89012345, email= 'info@pawfectiongrooming.com.sg', acceptablePetType='dogs', membershipTier='General')

# g6= Groomer (groomerId= 48763, groomerName='Pet Paradise', groomerPicURL='https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fb52eb1e697bc47aeffa2d_wKk60FNfX2cVCXLc-7E5h3G37FxbWglFJrTvgTXUdZnACVhuYrpIn_-Tc06kGgRHIAfw78zrLFyeR6hlh3gMFbmFn7e1_NHUC9yWp5NYZEdwd4WrryxTxZ0U6A1l6vPr8OJ4DubZPljyg3RxyxcPxNM.png', capacity= 25, address='36 Ang Mo Kio Avenue, Singapore', contactNo= 76543210, email= 'info@petparadise.com.sg', acceptablePetType='cats', membershipTier='General')

# g7= Groomer (groomerId= 23890, groomerName='Pawsitive Grooming', groomerPicURL='https://uploads-ssl.webflow.com/606e96048e07f8de3d446a0b/62fca4d781de9f6164b09227_h_AiqYKT-vjlFm0pRly2zuO2fLwcpdh_pyHr9dzj-_3w0izXQfHi0MAvXR0EedFoC37vJ_URqkW3jdk_yngBug5A0W1JF9K9nyAxwcSxDC5Pg2284Nt0Y6VTvDzfBH5gRgQhrSDNyGE5Bl5wu_jdHaQ.png', capacity= 14, address='55 Yishun Industrial Park, Singapore', contactNo= 67890123, email= 'info@pawsitivegrooming.com.sg', acceptablePetType='dogs', membershipTier='General')

# g8= Groomer (groomerId= 76549, groomerName='Whiskers & Wags Grooming', groomerPicURL='https://jetpetresort.com/wp-content/uploads/2014/05/jet-palace.jpg', capacity= 10, address='29 Lorong Mambong, Singapore', contactNo= 90123456, email= 'info@whiskersandwagsgrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# g9= Groomer (groomerId= 23756, groomerName='Doggy Doo', groomerPicURL='https://cdn.vox-cdn.com/thumbor/fnaPJnReyO6zNSOJMFHmKlwwovc=/0x0:3500x2336/1400x1400/filters:focal(1228x1285:1788x1845):format(jpeg)/cdn.vox-cdn.com/uploads/chorus_image/image/55994079/DCPhotographerElliottO_Donovan-LifeofRileyFinal_1of21_.0.0.jpg', capacity= 16, address='10 Changi Village Road, Singapore', contactNo= 78901234, email= 'info@doggydoo.com.sg', acceptablePetType='dogs', membershipTier='General')

# g10= Groomer (groomerId= 34567, groomerName='Furball Frenzy', groomerPicURL='https://www.naruwan-hotel.com.tw/en_new/NewImages/PitArea/img/PitArea%20(2).jpg', capacity= 20, address='51 Hougang Avenue, Singapore', contactNo= 65437890, email= 'info@furballfrenzy.com.sg', acceptablePetType='cats', membershipTier='General')

# g11= Groomer (groomerId= 90876, groomerName='The Barker Shop', groomerPicURL='https://scontent.fsin4-1.fna.fbcdn.net/v/t39.30808-6/306083044_174731381771471_1413778060914768815_n.jpg?stp=cp6_dst-jpg_p600x600&_nc_cat=101&ccb=1-7&_nc_sid=730e14&_nc_ohc=6sZQqzIouw4AX9xe9Pm&_nc_ht=scontent.fsin4-1.fna&oh=00_AfC-meJjXrxSBCk6Gosx_PXcxJ5Wix71hk8469D8AgQ_-w&oe=640F16C4', capacity= 12, address='63 Choa Chu Kang Road, Singapore', contactNo= 78906543, email= 'info@barkershop.com.sg', acceptablePetType='dogs', membershipTier='General')

# g12= Groomer (groomerId= 23456, groomerName='Pampered Paws', groomerPicURL='https://shopee.sg/blog/wp-content/uploads/2022/06/How-to-choose-the-best-dog-boarding-service-in-Singapore.jpg', capacity= 15, address='8 Jalan Kayu, Singapore', contactNo= 12345678, email= 'info@pamperedpaws.com.sg', acceptablePetType='dogs', membershipTier='General')

# g13= Groomer (groomerId= 78901, groomerName='Purrfect Pet Grooming', groomerPicURL='https://www.thebestsingapore.com/wp-content/uploads/2021/04/The-Waggington-2.jpg', capacity= 10, address='18 Boon Lay Way, Singapore', contactNo= 34567890, email= 'info@purrfectpetgrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# g14= Groomer (groomerId= 43567, groomerName='Tails Up Grooming', groomerPicURL='https://siestacloudlivestorage.azureedge.net/default/medium_26654_95370a23-07aa-46ef-8dc8-6d7a2e448007.jpg', capacity= 18, address='77 Upper East Coast Road, Singapore', contactNo= 87654321, email= 'info@tailsupgrooming.com.sg', acceptablePetType='dogs', membershipTier='General')

# g15= Groomer (groomerId= 76543, groomerName='The Paw Spa', groomerPicURL='https://i.pinimg.com/originals/43/ad/40/43ad40572c70d44bf32aa501520c608e.jpg', capacity= 22, address='6 Eu Tong Sen Street, Singapore', contactNo= 23456789, email= 'info@pawspa.com.sg', acceptablePetType='cats', membershipTier='General')

# g16= Groomer (groomerId= 35467, groomerName='Doggy Delight', groomerPicURL='https://www.telegraph.co.uk/content/dam/family/2021/06/22/dog-hotel-love_4_trans_NvBQzQNjv4BqplGOf-dgG3z4gg9owgQTXH-5rYAcEMfZ-k6qzXXxMMM.jpg', capacity= 14, address='2 Woodlands Avenue, Singapore', contactNo= 78901234, email= 'info@doggydelight.com.sg', acceptablePetType='dogs', membershipTier='General')

# g17= Groomer (groomerId= 98567, groomerName="The Cat's Meow", groomerPicURL='https://cocomomo.my/images/rooms.jpg', capacity= 12, address='9 Temasek Boulevard, Singapore', contactNo= 34567890, email= 'info@thecatsmeow.com.sg', acceptablePetType='cats', membershipTier='General')

# g18= Groomer (groomerId= 56789, groomerName='Paws and Claws', groomerPicURL='https://img1.wsimg.com/isteam/ip/5484e2de-15b1-489e-95d5-2e80f0a7b41c/fb_5011265872258629_1822x2048-0001.jpg/:/rs=w:388,cg:true,m', capacity= 20, address='27 Jalan Membina, Singapore', contactNo= 98765432, email= 'info@pawsandclaws.com.sg', acceptablePetType='dogs', membershipTier='General')

# g19= Groomer (groomerId= 45678, groomerName='Furry Friends Grooming', groomerPicURL='https://s3-ap-southeast-1.amazonaws.com/atap-main/gallery-full/0bf2abbb-3cc6-4ee5-9cef-83b60037b333/pet-hotel.jpg', capacity= 15, address='6 Raffles Boulevard, Singapore', contactNo= 87654321, email= 'info@furryfriendsgrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# g20= Groomer (groomerId= 67890, groomerName='Pawfect Grooming', groomerPicURL='https://npr.brightspotcdn.com/dims4/default/9213782/2147483647/strip/true/crop/1572x968+0+71/resize/880x542!/quality/90/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com%2F54%2Fc0%2F0c6c64cf4814a6c57bca8e81d2aa%2Ftv-dog.jpg', capacity= 12, address='101 Upper Cross Street, Singapore', contactNo= 23456789, email= 'info@pawfectgrooming.com.sg', acceptablePetType='dogs', membershipTier='General')

# g21= Groomer (groomerId= 12345, groomerName='Whiskers N Paws', groomerPicURL='https://static.thehoneycombers.com/wp-content/uploads/sites/2/2018/09/the-wagington.png', capacity= 18, address='3 Simei Street 6, Singapore', contactNo= 76543210, email= 'info@whiskersnpaws.com.sg', acceptablePetType='cats', membershipTier='General')

# g22= Groomer (groomerId= 89012, groomerName='Dapper Dogs', groomerPicURL='https://www.petplace.com/static/311e67c27b4d67333c454721869e8beb/c23ac/shutterstock_1065580706.jpg', capacity= 14, address='2 Serangoon Road, Singapore', contactNo= 34567890, email= 'info@dapperdogs.com.sg', acceptablePetType='dogs', membershipTier='General')

# g23= Groomer (groomerId= 34567, groomerName='Pawsitively Grooming', groomerPicURL='https://www.chinadaily.com.cn/business/img/attachement/jpg/site1/20160225/b083fe955aa11838d1e206.jpg', capacity= 20, address='10 Tampines Central, Singapore', contactNo= 65432109, email= 'info@pawsitivelygrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# g24= Groomer (groomerId= 90123, groomerName='Furry Tails', groomerPicURL='https://cdn.shopify.com/s/files/1/0605/3888/0242/files/Pet_Hotel_480x480.jpg?v=1635352352', capacity= 10, address='8 Marina Boulevard, Singapore', contactNo= 12345678, email= 'info@furrytails.com.sg', acceptablePetType='dogs', membershipTier='General')

# g25= Groomer (groomerId= 78901, groomerName='Meow Grooming', groomerPicURL='https://media.bizj.us/view/img/12352627/k9-resorts-of-overland-park-luxury-suites-1*1200xx4032-2265-0-138.jpg', capacity= 16, address='50 Jurong Gateway Road, Singapore', contactNo= 56789012, email= 'info@meowgrooming.com.sg', acceptablePetType='cats', membershipTier='General')

# session.add_all([g1,g2,g3,g4,g5,g6,g7,g8,g9,g10,g11,g12,g13,g14,g15,g16,g17,g18,g19,g20,g21,g22,g23,g24,g25])
# session.commit()

#get all groomers
@app.route("/groomer")
def get_all():
    groomerlist = Groomer.query.all()
    if len(groomerlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "groomer": [groomer.json() for groomer in groomerlist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no groomers."
        }
    ), 404


#get specific groomer by groomerId
@app.route("/groomer/<string:groomerId>")
def find_by_groomerId(groomerId):
    groomer = Groomer.query.filter_by(groomerId=groomerId).first()
    if groomer:
        return jsonify(
            {
                "code": 200,
                "data": groomer.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Groomer not found."
        }
    ), 404


#add new groomer
@app.route("/groomer/<string:groomerId>", methods=['POST'])
def create_groomer(groomerId):
    if (Groomer.query.filter_by(groomerId = groomerId).first()):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "groomerId": groomerId
                },
                "message": "Groomer already exists."
            }
        ), 400
    data = request.get_json()
    groomer = Groomer(groomerId, **data)
    try:
        db.session.add(groomer)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "groomerId": groomerId
                },
                "message": "An error occurred adding the new groomer."
            }
        ), 500
    return jsonify(
        {
            "code": 201,
            "data": groomer.json()
        }
    ), 201

#edit groomer details
@app.route("/groomer/<string:find>", methods=['PUT'])
def update_groomer(find):
  
    if (Groomer.query.filter_by(groomerId=find).first()):
        groomer_data = request.get_json()
        groomer = Groomer(find, **groomer_data)

        groomerName = groomer_data["groomerName"]
        groomerPicURL = groomer_data['groomerPicURL']
        capacity = groomer_data["capacity"]
        address = groomer_data['address']
        contactNo = groomer_data['contactNo']
        email = groomer_data['email']
        acceptablePetType = groomer_data['acceptablePetType']
        membershipTier = groomer_data['membershipTier']
        
        groomer.groomerName = groomerName
        groomer.groomerPicURL = groomerPicURL
        groomer.capacity = capacity
        groomer.address = address
        groomer.contactNo = contactNo
        groomer.email = email
        groomer.acceptablePetType = acceptablePetType
        groomer.membershipTier = membershipTier

        db.session.commit()            
        return jsonify(
    {
        "code": 201,
        "data": groomer.json()
    }
), 201
    else:
      return jsonify(
            {
                "code": 404,
                "data": {
                    "groomerId": find
                },
                "message": "Groomer not found."
            }
        ), 404


#upgrade groomer tier
@app.route("/groomer/<string:find>/upgrade", methods=['PUT'])
def upgrade_groomer_tier(find):
    print("Dickhead",flush=True)
    if (Groomer.query.filter_by(groomerId=find).first()):
        groomer = Groomer.query.filter_by(groomerId=find).first()
        groomer.membershipTier = 'Premium'

        db.session.commit()            
        return jsonify(
    {
        "code": 201,
        "data": groomer.json()
    }
), 201
    else:
      return jsonify(
            {
                "code": 404,
                "data": {
                    "groomerId": find
                },
                "message": "Groomer not found."
            }
        ), 404

#delete groomer details
@app.route("/groomer/<string:find>", methods=['DELETE'])
def delete_groomer(find):
    if (Groomer.query.filter_by(groomerId=find).first()):
        groomer = Groomer.query.get(find)
        db.session.delete(groomer)
        db.session.commit()
        return jsonify(
        {
            "code": 201,
            "data": groomer.json(),
            'message': 'Groomer deleted'
        }
        ), 201
    else:
      return jsonify(
            {
                "code": 404,
                "data": {
                    "groomer": find
                },
                "message": "Groomer not found."
            }
        ), 404
if __name__ == '__main__':
    app.run(port=5000, debug=True)