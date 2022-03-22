import argparse
from datetime import datetime
from glob import glob
import logging
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, SmallInteger, Boolean, create_engine, ForeignKey, Date, Float, BigInteger, exc
from sqlalchemy.orm import relationship, sessionmaker, Session as SessionType
from sqlalchemy_utils import create_database, database_exists
import ast
import pandas as pd
import sys

MAX_INT = 2147483647
LOCATIONS = [{'name': 'Georgia, United States', 'id': 'ChIJV4FfHcU28YgR5xBP7BC8hGY'}, 
             {'name': 'North Carolina, United States', 'id': 'ChIJgRo4_MQfVIgRGa4i6fUwP60'}, 
             {'name': 'Florida, United States', 'id': 'ChIJvypWkWV2wYgR0E7HW9MTLvc'}]

if os.environ.get('python_env') == 'production':
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
else:
    db_user = os.environ.get('DEV_DB_USER')
    db_password = os.environ.get('DEV_DB_PASSWORD')
    db_host = os.environ.get('DEV_DB_HOST')
db_name = os.environ.get('DB_NAME')

# handling no password case
if db_password:
    engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}', echo=True)
else: 
    engine = create_engine(f'mysql+pymysql://{db_user}@{db_host}/{db_name}', echo=True)
    
Session = sessionmaker(bind=engine, expire_on_commit=False)

if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else: 
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', stream=sys.stdout)
logger = logging.getLogger()

if not database_exists(engine.url):
    create_database(engine.url, encoding='utf8mb4')
    
Base = declarative_base()

class Location(Base):
    __tablename__ = 'location'

    id = Column(String(100), primary_key=True, autoincrement=False)
    name = Column(String(75))
    link = Column(String(255))
    listing = relationship('Listing', back_populates='location', cascade='all, delete')
    
    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name={self.name}, link={self.link})>"
    
class Listing(Base):
    __tablename__ = 'listing'
    
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    location_id = Column(String(75), ForeignKey('location.id'))
    location = relationship("Location", back_populates="listing")
    occupancy = relationship('ListingOccupancy', back_populates='listing')
    city = Column(String(75))
    guests = Column(SmallInteger)
    bedrooms = Column(String(15))
    beds = Column(SmallInteger)
    baths = Column(Float)
    name = Column(String(100))
    rating = Column(Float)
    reviews_count = Column(SmallInteger)
    superhost = Column(Boolean)
    lat = Column(Float)
    lng = Column(Float)
    person_capacity = Column(SmallInteger)

    
    def __repr__(self) -> str:
        return f"<Location(id={self.id}, superHost={self.superhost}), city={self.city}, location={self.location_id}>"

class ListingOccupancy(Base):
    __tablename__ = 'listing_occupancy'
    
    listing_id = Column(BigInteger, ForeignKey('listing.id'), primary_key=True, autoincrement=False)
    listing = relationship('Listing', back_populates='occupancy')
    date = Column(Date, primary_key=True, autoincrement=False)
    bitmap = Column(String(255))
    
    
def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

def query_locations():
    with Session.begin() as session:
        return session.query(Location).all()

# TODO: update to accept json or something other than hardcoded
def insert_locations():
    try:
        with Session.begin() as session:
            ga = Location(id="ChIJV4FfHcU28YgR5xBP7BC8hGY", name="Georgia, United States", link="https://www.airbnb.com/s/Georgia--United-States/homes?property_type_id%5B%5D=67&place_id=ChIJV4FfHcU28YgR5xBP7BC8hGY&refinement_paths%5B%5D=%2Fhomes")
            fl = Location(id="ChIJvypWkWV2wYgR0E7HW9MTLvc", name="Florida, United States", link="https://www.airbnb.com/s/Florida--United-States/homes?property_type_id%5B%5D=67&place_id=ChIJvypWkWV2wYgR0E7HW9MTLvc&refinement_paths%5B%5D=%2Fhomes")
            nc = Location(id="ChIJgRo4_MQfVIgRGa4i6fUwP60", name="North Carolina, United States", link="https://www.airbnb.com/s/North-Carolina--United-States/homes?property_type_id%5B%5D=67&place_id=ChIJgRo4_MQfVIgRGa4i6fUwP60&refinement_paths%5B%5D=%2Fhomes")
            session.add_all([ga, fl, nc])
    except Exception as e:
        logger.error(e)
  
def get_baths(row):
    baths = ast.literal_eval(row['homeDetails'])[3]['title']
    if baths:
        try:
            return float(baths.split()[0])
        # baths are formatted weird
        except:
            if baths.lower() == 'half-bath':
                return 0.5
    return 0
def insert_listings(root_dir):
    try:
        with engine.begin() as conn: 
            all_listings = pd.read_excel(os.path.join(root_dir, 'tinyHouses.xlsx'), sheet_name=None)
            for location, listings in all_listings.items():
                listings.rename(columns={'avgRating': 'rating', 'isSuperhost': 'superhost', 'reviewsCount': 'reviews_count', 'personCapacity': 'person_capacity'}, inplace=True)
                listings['city'] = listings.apply(lambda row: ast.literal_eval(row['overview'])[1]['title'], axis=1)
                listings['guests'] = listings.apply(lambda row: int(ast.literal_eval(row['homeDetails'])[0]['title'].split()[0]), axis=1)
                listings['bedrooms'] = listings.apply(lambda row: ast.literal_eval(row['homeDetails'])[1]['title'], axis=1)
                listings['beds'] = listings.apply(lambda row: int(ast.literal_eval(row['homeDetails'])[2]['title'].split()[0]) if ast.literal_eval(row['homeDetails'])[2]['title'] else 0, axis=1)
                listings['baths'] = listings.apply(get_baths, axis=1)
                listings['location_id'] = next(filter(lambda loc: loc['name'] == location, LOCATIONS))['id']
                listings = listings[listings.columns.intersection(vars(Listing))]
                listings.to_sql('listing', conn, index=False, if_exists='append')
    except Exception as e:
        logger.error(e)
def insert_occupancy(io, date):
    try:
        with engine.begin() as conn:
            occupancies = pd.read_excel(io)
            occupancies.rename(columns={'id': 'listing_id'}, inplace=True)
            occupancies['date'] = date  
            occupancies = occupancies[occupancies['listing_id'] < MAX_INT]
            occupancies.to_sql('listing_occupancy', conn, index=False, if_exists='append')
    except Exception as e:
        logger.error(e)
  
def query_all_superhosts():
    with Session() as session:
        q = session.query(Listing).filter(Listing.superhost == 1)
        return q.all()


def insert_all_occupancies(root_dir): 
    for file in glob(root_dir + '/*-occ-data.xlsx'):
        date = datetime.strptime(file.split('/')[-1][:10], '%m-%d-%Y')
        with open(file, 'rb') as fh:  
            io = fh.read()
            insert_occupancy(io, date)
            
def init_db():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='command line tool to init database')
    parser.add_argument('dir', type=dir_path, help='Required root directory where all excel files are located')
    args = parser.parse_args()
    init_db()
    insert_locations()
    insert_listings(args.dir)
    insert_all_occupancies(args.dir)
