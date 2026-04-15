"""
AIEMCS - Seed Data Generator
Generates 200 sources, 300 incharges, 1000 equipment records, and utilization data.
Run: python generate_seed.py
"""

import random
import bcrypt
import datetime

# ── helpers ────────────────────────────────────────────────────────────────────

BLOCKS = {
    'A': 300, 'B': 300, 'C': 300, 'D': 300, 'E': 300, 'H': 500
}
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
SLOTS = [
    '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
    '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00',
    '16:00-17:00', '17:00-18:00'
]

def rand_location(block=None):
    if block is None:
        block = random.choice(list(BLOCKS.keys()))
    max_room = BLOCKS[block]
    room = random.randint(1, max_room)
    return f"{block}_{room:03d}"

def rand_date(start_year=2010, end_year=2023):
    start = datetime.date(start_year, 1, 1)
    end   = datetime.date(end_year, 12, 31)
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, delta))

def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

# ── domain data ────────────────────────────────────────────────────────────────

DOMAIN_EQUIPMENT = {
    'hospital': [
        ('MRI Machine',        'imaging',   ['1.5T MRI', '3T MRI', '3T wide-bore MRI']),
        ('CT Scanner',         'imaging',   ['64-slice CT', '128-slice CT', '256-slice CT']),
        ('Ventilator',         'critical',  ['ICU Ventilator', 'Transport Ventilator', 'Neonatal Ventilator']),
        ('ECG Machine',        'cardio',    ['12-lead ECG', 'Portable ECG', 'Holter Monitor']),
        ('Ultrasound',         'imaging',   ['Portable Ultrasound', 'Color Doppler', '4D Ultrasound']),
        ('Defibrillator',      'emergency', ['AED Defibrillator', 'Manual Defibrillator']),
        ('Infusion Pump',      'drug_admin',['Syringe Pump', 'Volumetric Pump']),
        ('Patient Monitor',    'monitoring',['Bedside Monitor', 'Central Monitor']),
        ('Dialysis Machine',   'renal',     ['Hemodialysis Unit', 'CRRT Machine']),
        ('Surgical Robot',     'surgery',   ['da Vinci Surgical System']),
    ],
    'engineering': [
        ('CNC Milling Machine','machining', ['3-axis CNC', '5-axis CNC']),
        ('3D Printer',         '3d_print',  ['FDM Printer', 'SLA Printer', 'SLS Printer']),
        ('Robotic Arm',        'robotics',  ['6-DOF Robot Arm', 'Collaborative Robot']),
        ('Oscilloscope',       'electronics',['100MHz Oscilloscope', '500MHz Oscilloscope']),
        ('Lathe Machine',      'machining', ['Conventional Lathe', 'CNC Lathe']),
        ('Welding Machine',    'fabrication',['MIG Welder', 'TIG Welder', 'Arc Welder']),
        ('PLC Trainer',        'automation',['Siemens S7-1200 PLC', 'Allen-Bradley PLC']),
        ('Signal Generator',   'electronics',['Function Generator', 'RF Signal Generator']),
        ('Wind Tunnel',        'aero',      ['Subsonic Wind Tunnel', 'Open Circuit Wind Tunnel']),
        ('Hydraulic Press',    'mechanical',['10-ton Press', '50-ton Hydraulic Press']),
    ],
    'media': [
        ('Desktop Computer',   'desktop',   [
            'Intel i3, 8GB RAM, 256GB SSD',
            'Intel i5, 16GB RAM, 512GB SSD',
            'Intel i7, 16GB RAM, 512GB SSD, GTX 1660',
            'Intel i9, 32GB RAM, 1TB SSD, RTX 3080'
        ]),
        ('Laptop',             'laptop',    [
            'Intel i5, 8GB RAM, 256GB SSD',
            'Intel i7, 16GB RAM, 512GB SSD',
            'Intel i9, 32GB RAM, 1TB NVMe'
        ]),
        ('DSLR Camera',        'camera',    ['Canon EOS 5D', 'Nikon D850', 'Sony A7 III']),
        ('Video Camera',       'camera',    ['Sony PXW-Z90', 'Blackmagic URSA Mini Pro']),
        ('Audio Mixer',        'audio',     ['Yamaha MG16', 'Behringer X32']),
        ('Lighting Kit',       'lighting',  ['LED Panel Kit', 'Softbox Studio Kit']),
        ('Green Screen',       'studio',    ['Chroma Key Backdrop 3x4m']),
        ('Drone',              'aerial',    ['DJI Mavic 3', 'DJI Phantom 4 Pro']),
    ],
    'science': [
        ('Spectrophotometer',  'optical',   ['UV-Vis Spectrophotometer', 'FTIR Spectrometer']),
        ('Centrifuge',         'separation',['Microcentrifuge', 'High-Speed Centrifuge']),
        ('Autoclave',          'sterilization',['Vertical Autoclave', 'Horizontal Autoclave']),
        ('Microscope',         'optical',   ['Compound Microscope', 'Electron Microscope', 'Fluorescence Microscope']),
        ('PCR Machine',        'molecular', ['Standard PCR', 'Real-Time qPCR']),
        ('pH Meter',           'chemistry', ['Bench pH Meter', 'Portable pH Meter']),
        ('Gas Chromatograph',  'analytical',['GC with FID', 'GC-MS System']),
        ('Electrophoresis',    'molecular', ['Gel Electrophoresis Unit', 'Capillary Electrophoresis']),
    ],
    'agriculture': [
        ('Soil Sensor',        'sensor',    ['NPK Soil Sensor', 'Moisture Sensor Array']),
        ('Weather Station',    'sensor',    ['Automatic Weather Station', 'Davis Instruments Vantage Pro']),
        ('Drone Sprayer',      'aerial',    ['DJI Agras T40', 'XAG P100']),
        ('Irrigation Controller','automation',['Smart Drip Irrigator', 'Pivot Irrigation Control']),
        ('Seed Germinator',    'lab',       ['Controlled Environment Germinator']),
        ('Tractor',            'machinery', ['35HP Tractor', '55HP Tractor']),
        ('Harvester',          'machinery', ['Mini Combine Harvester']),
        ('Greenhouse Monitor', 'sensor',    ['IoT Greenhouse Controller']),
    ],
    'fashion': [
        ('Sewing Machine',     'textile',   ['Industrial Sewing Machine', 'Computerized Sewing Machine']),
        ('Embroidery Machine', 'textile',   ['Single-Head Embroidery Machine', 'Multi-Head Embroidery Machine']),
        ('Cutting Plotter',    'design',    ['Vinyl Cutter Plotter', 'Laser Cutting Machine']),
        ('Knitting Machine',   'textile',   ['Flat Knitting Machine', 'Circular Knitting Machine']),
        ('Heat Press',         'printing',  ['Swing Away Heat Press', 'Conveyor Heat Press']),
        ('Pattern Maker',      'design',    ['Digital Pattern Maker', 'Grading Machine']),
        ('Fabric Tester',      'quality',   ['Tensile Strength Tester', 'Color Fastness Tester']),
    ],
    'hotel': [
        ('Commercial Oven',    'kitchen',   ['Convection Oven', 'Deck Oven', 'Rotary Oven']),
        ('Dishwasher',         'kitchen',   ['Undercounter Dishwasher', 'Conveyor Dishwasher']),
        ('Refrigerator',       'storage',   ['Walk-in Cooler', 'Display Refrigerator']),
        ('Food Mixer',         'kitchen',   ['20L Planetary Mixer', '60L Spiral Mixer']),
        ('Deep Fryer',         'kitchen',   ['Commercial Deep Fryer', 'Pressure Fryer']),
        ('Grill',              'kitchen',   ['Contact Grill', 'Char-Grill', 'Salamander Grill']),
        ('Espresso Machine',   'beverage',  ['La Marzocco Linea', 'Nuova Simonelli Aurelia']),
        ('POS Terminal',       'management',['Touchscreen POS', 'Handheld POS']),
    ],
}

FACULTY_BLOCK_MAP = {
    'hospital':    ('HEALTH',  'MBBS',   ['H']),
    'engineering': ('FEAT',    'CSE',    ['A', 'B', 'C']),
    'media':       ('ARTS',    'MEDIA',  ['D', 'E']),
    'science':     ('SCIENCE', 'BTECH',  ['A', 'B']),
    'agriculture': ('AGRI',    'AGRI',   ['C', 'D']),
    'fashion':     ('DESIGN',  'FASHION',['E']),
    'hotel':       ('HOTEL',   'HM',     ['D']),
}

FIRST_NAMES = ['Amit','Priya','Rahul','Sneha','Vikram','Anita','Suresh','Kavita',
               'Mohan','Deepa','Rajesh','Pooja','Arjun','Meera','Sanjay','Nisha',
               'Arun','Sunita','Vijay','Lakshmi','Ravi','Uma','Manoj','Gita',
               'Krishna','Radha','Ashok','Seema','Naveen','Reena','Dinesh','Puja',
               'Rohit','Swati','Gaurav','Shweta','Nitin','Tanya','Ajay','Ritu']
LAST_NAMES  = ['Sharma','Patel','Singh','Kumar','Verma','Gupta','Rao','Nair',
               'Iyer','Reddy','Joshi','Chauhan','Mehta','Shah','Pandey','Tiwari',
               'Mishra','Dubey','Srivastava','Chaudhary','Das','Bose','Roy','Sen']

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_email(name, uid):
    clean = name.lower().replace(' ', '.')
    domains = ['edu.in','university.ac.in','institute.org','college.edu']
    return f"{clean}{uid}@{random.choice(domains)}"

# ── generators ─────────────────────────────────────────────────────────────────

def gen_sources(n=200):
    rows = []
    source_ids = random.sample(range(100000, 999999), n)
    for i, sid in enumerate(source_ids):
        name = rand_name()
        faculty, dept, blocks = random.choice(list(FACULTY_BLOCK_MAP.values()))
        block = random.choice(blocks)
        loc = rand_location(block)
        rows.append({
            'source_id': sid,
            'name': name,
            'email': rand_email(name, sid % 1000),
            'phone': f"9{random.randint(100000000,999999999)}",
            'room_duty': loc,
            'faculty': faculty,
            'department': dept,
        })
    return rows

def gen_incharges(n=300):
    rows = []
    incharge_ids = random.sample(range(600000, 799999), n)
    pw_hash = hash_pw('incharge@123')  # default password for all
    for i, iid in enumerate(incharge_ids):
        name = rand_name()
        faculty, dept, blocks = random.choice(list(FACULTY_BLOCK_MAP.values()))
        block = random.choice(blocks)
        loc = rand_location(block)
        rows.append({
            'incharge_id': iid,
            'name': name,
            'email': rand_email(name, iid % 1000),
            'phone': f"8{random.randint(100000000,999999999)}",
            'room_duty': loc,
            'password_hash': pw_hash,
            'role': 'incharge',
        })
    return rows

def gen_equipment(n=1000, sources=None, incharges=None):
    rows = []
    tag_counter = 10000
    source_ids   = [s['source_id']   for s in sources]
    incharge_ids = [i['incharge_id'] for i in incharges]

    for _ in range(n):
        domain = random.choice(list(DOMAIN_EQUIPMENT.keys()))
        eq_name, eq_cat, models = random.choice(DOMAIN_EQUIPMENT[domain])
        model = random.choice(models)
        faculty, dept, blocks = FACULTY_BLOCK_MAP[domain]
        block = random.choice(blocks)
        loc   = rand_location(block)
        qty   = random.randint(1, 20)
        price = random.randint(5000, 2000000)
        tag   = f"UPT/{random.choice(['IT','ENG','MED','SCI','AGRI','DES','HM'])}/{block}/G/{tag_counter} to UPT/../{tag_counter+qty-1}"
        tag_counter += qty + random.randint(1, 50)

        rows.append({
            'tag': tag,
            'equipment_name': eq_name,
            'equipment_category': eq_cat,
            'equipment_model_details': model,
            'unit_price': price,
            'date_of_purchase': str(rand_date()),
            'quantity': qty,
            'working_status': random.choices(
                ['good', 'faulty', 'maintenance', 'good'],
                weights=[70, 15, 10, 5]
            )[0],
            'faculty': faculty,
            'deparment': dept,
            'block_location': loc,
            'source_id': random.choice(source_ids),
            'incharge_id': random.choice(incharge_ids),
        })
    return rows

def gen_utilization(n=500, incharges=None):
    rows = []
    incharge_ids = [i['incharge_id'] for i in incharges]
    activities   = ['free','lab session','lecture','exam','workshop','demo','maintenance']
    types        = ['lab','classroom','hall','studio','workshop']
    blocks       = ['A','B','C','D','E','H']

    for _ in range(n):
        block = random.choice(blocks)
        loc   = rand_location(block)
        slots_chosen = random.sample(SLOTS, random.randint(1, 3))
        rows.append({
            'block_location': loc,
            'type': random.choice(types),
            'day': random.choice(DAYS),
            'slot': ', '.join(slots_chosen),
            'activity': random.choice(activities),
            'incharge_id': random.choice(incharge_ids),
        })
    return rows

# ── SQL emitter ────────────────────────────────────────────────────────────────

def to_sql_str(val):
    if val is None:
        return 'NULL'
    s = str(val).replace("'", "''")
    return f"'{s}'"

def emit_inserts(table: str, rows: list[dict]) -> str:
    if not rows:
        return ''
    cols = list(rows[0].keys())
    col_str = ', '.join(cols)
    lines = [f"INSERT INTO {table} ({col_str}) VALUES"]
    vals_list = []
    for row in rows:
        vals = ', '.join(to_sql_str(row[c]) for c in cols)
        vals_list.append(f"  ({vals})")
    lines.append(',\n'.join(vals_list) + ';')
    return '\n'.join(lines)

# ── main ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import os, sys

    random.seed(42)

    print("Generating sources...")
    sources   = gen_sources(200)
    print("Generating incharges...")
    incharges = gen_incharges(300)
    print("Generating equipment...")
    equipment = gen_equipment(1000, sources, incharges)
    print("Generating utilization...")
    utilization = gen_utilization(500, incharges)

    sql = f"""-- ============================================================
-- AIEMCS Seed Data (auto-generated)
-- ============================================================
USE aiemcs;

{emit_inserts('source_data', sources)}

{emit_inserts('incharge_data', incharges)}

{emit_inserts('equipment_data', equipment)}

{emit_inserts('equipment_utilization', utilization)}
"""

    out = os.path.join(os.path.dirname(__file__), 'seed_data.sql')
    with open(out, 'w') as f:
        f.write(sql)

    print(f"\n✅ Seed data written to {out}")
    print(f"   {len(sources)} sources | {len(incharges)} incharges | {len(equipment)} equipment | {len(utilization)} utilization rows")
    print("\nDefault incharge login password: incharge@123")
