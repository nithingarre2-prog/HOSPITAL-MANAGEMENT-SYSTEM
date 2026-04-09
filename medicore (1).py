# ─────────────────────────────────────────────────────────────
#  MediCore — Hospital Management System
#  Topic: Maintain patient records, schedule appointments with
#         doctors, generate bills, manage doctors and
#         hospital operations efficiently.
#
#  Run:  python medicore.py   (or Start Debugging in VS Code)
#  Requires: Python 3.6+  (no extra libraries needed)
# ─────────────────────────────────────────────────────────────

import sqlite3
import os
from datetime import date, datetime

DB_FILE = "medicore.db"

# ── Pre-registered doctors ──────────────────────────────────
DEFAULT_DOCTORS = [
    (1,  "Dr. Priya Sharma",   "Cardiology",       "MBBS, MD",     "Ext. 201", "09:00", "17:00", "Mon,Tue,Wed,Thu,Fri"),
    (2,  "Dr. Arjun Mehta",    "Neurology",         "MBBS, DM",     "Ext. 202", "08:00", "16:00", "Mon,Tue,Wed,Thu,Fri"),
    (3,  "Dr. Sunita Rao",     "Orthopedics",       "MBBS, MS",     "Ext. 203", "10:00", "18:00", "Mon,Wed,Fri,Sat"),
    (4,  "Dr. Vikram Nair",    "General Medicine",  "MBBS",         "Ext. 204", "08:00", "14:00", "Mon,Tue,Wed,Thu,Fri,Sat"),
    (5,  "Dr. Kavya Iyer",     "Pediatrics",        "MBBS, MD",     "Ext. 205", "09:00", "15:00", "Mon,Tue,Wed,Thu,Fri"),
    (6,  "Dr. Ramesh Pillai",  "Gynecology",        "MBBS, MS",     "Ext. 206", "12:00", "20:00", "Mon,Tue,Thu,Fri"),
    (7,  "Dr. Suresh Gupta",   "Oncology",          "MBBS, MD, DM", "Ext. 207", "09:00", "17:00", "Tue,Wed,Thu,Fri"),
    (8,  "Dr. Anjali Verma",   "ENT",               "MBBS, MS",     "Ext. 208", "11:00", "19:00", "Mon,Tue,Wed,Thu,Fri"),
    (9,  "Dr. Mohan Das",      "Ophthalmology",     "MBBS, MS",     "Ext. 209", "09:00", "13:00", "Mon,Tue,Thu,Sat"),
    (10, "Dr. Nisha Reddy",    "Psychiatry",        "MBBS, MD",     "Ext. 210", "14:00", "20:00", "Mon,Wed,Fri"),
]

# ══════════════════════════════════════════════════════════════
#  DATABASE SETUP
# ══════════════════════════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER,
            gender      TEXT,
            blood       TEXT,
            contact     TEXT    NOT NULL,
            emergency   TEXT,
            address     TEXT,
            dept        TEXT,
            doctor      TEXT,
            ward        TEXT,
            status      TEXT    DEFAULT 'Admitted',
            diagnosis   TEXT,
            notes       TEXT,
            admit_date  TEXT    DEFAULT (date('now')),
            created     TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  INTEGER NOT NULL,
            doctor_id   INTEGER NOT NULL,
            doctor_name TEXT    NOT NULL,
            dept        TEXT,
            appt_date   TEXT    NOT NULL,
            appt_time   TEXT,
            appt_type   TEXT    DEFAULT 'Consultation',
            reason      TEXT,
            status      TEXT    DEFAULT 'Scheduled',
            created     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            dept        TEXT,
            qual        TEXT,
            contact     TEXT,
            avail_from  TEXT,
            avail_to    TEXT,
            avail_days  TEXT,
            notes       TEXT
        );

        CREATE TABLE IF NOT EXISTS bills (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  INTEGER NOT NULL,
            consult     REAL    DEFAULT 0,
            medicine    REAL    DEFAULT 0,
            lab         REAL    DEFAULT 0,
            room        REAL    DEFAULT 0,
            other       REAL    DEFAULT 0,
            discount    REAL    DEFAULT 0,
            total       REAL    DEFAULT 0,
            status      TEXT    DEFAULT 'Pending',
            notes       TEXT,
            issued      TEXT    DEFAULT (date('now')),
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        );
    """)
    conn.commit()

    # Seed doctors only if table is empty
    count = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO doctors VALUES (?,?,?,?,?,?,?,?,?)",
            [(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], "") for d in DEFAULT_DOCTORS]
        )
        conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ══════════════════════════════════════════════════════════════

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def hr(char="─", width=62):
    print(char * width)

def header(title):
    clear()
    hr("═")
    print("  🏥   MediCore — Hospital Management System")
    hr("═")
    print(f"  ▶  {title}")
    hr()

def pause():
    input("\n  Press Enter to continue...")

def inp(prompt, required=True):
    while True:
        val = input(f"  {prompt}: ").strip()
        if val or not required:
            return val
        print("  ⚠   This field is required.")

def inp_int(prompt, lo=0, hi=99999, required=True):
    while True:
        raw = inp(prompt, required)
        if not raw and not required:
            return None
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
            print(f"  ⚠   Enter a number between {lo} and {hi}.")
        except ValueError:
            print("  ⚠   Please enter a valid number.")

def inp_float(prompt, required=False):
    while True:
        raw = inp(prompt, required)
        if not raw:
            return 0.0
        try:
            v = float(raw)
            if v < 0:
                print("  ⚠   Amount cannot be negative.")
                continue
            return v
        except ValueError:
            print("  ⚠   Please enter a valid amount (e.g. 500 or 1500.50).")

def choose(prompt, options):
    """Show a numbered list; return 0-based index of chosen item."""
    for i, o in enumerate(options, 1):
        print(f"    {i}. {o}")
    while True:
        raw = inp(prompt)
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
            print(f"  ⚠   Enter a number between 1 and {len(options)}.")
        except ValueError:
            print("  ⚠   Invalid input.")

def select_patient(conn, label="Select Patient"):
    """List all patients and return the chosen row, or None."""
    rows = conn.execute(
        "SELECT id, name, contact, status FROM patients ORDER BY id"
    ).fetchall()
    if not rows:
        print("\n  ⚠   No patients registered yet.")
        return None
    print(f"\n  {label}:")
    hr("-")
    print(f"  {'ID':<8} {'Name':<25} {'Contact':<16} {'Status'}")
    hr("-")
    for r in rows:
        print(f"  P-{r['id']:05d}  {r['name']:<25} {r['contact']:<16} {r['status']}")
    hr("-")
    pid = inp_int("  Enter Patient ID", lo=1)
    p = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    if not p:
        print("  ⚠   Patient ID not found.")
        return None
    return p

def select_doctor(conn, label="Select Doctor"):
    """List all doctors and return chosen row, or None."""
    rows = conn.execute(
        "SELECT * FROM doctors ORDER BY id"
    ).fetchall()
    if not rows:
        print("\n  ⚠   No doctors found.")
        return None
    print(f"\n  {label}:")
    hr("-")
    print(f"  {'ID':<5} {'Name':<28} {'Department':<20} {'Available'}")
    hr("-")
    for r in rows:
        print(f"  {r['id']:<5} {r['name']:<28} {r['dept']:<20} {r['avail_from']}–{r['avail_to']}  [{r['avail_days']}]")
    hr("-")
    did = inp_int("  Enter Doctor ID", lo=1)
    d = conn.execute("SELECT * FROM doctors WHERE id=?", (did,)).fetchone()
    if not d:
        print("  ⚠   Doctor ID not found.")
        return None
    return d

# ══════════════════════════════════════════════════════════════
#  1. PATIENT MANAGEMENT
# ══════════════════════════════════════════════════════════════

def add_patient():
    header("Add New Patient")

    name      = inp("Full Name")
    age       = inp_int("Age", lo=0, hi=130)

    print("\n  Gender:")
    gender    = ["Male", "Female", "Other"][choose("Select", ["Male", "Female", "Other"])]

    print("\n  Blood Group:")
    blood     = ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"][
                 choose("Select", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])]

    contact   = inp("Contact Number")
    emergency = inp("Emergency Contact", required=False)
    address   = inp("Address", required=False)

    conn = get_conn()
    print("\n  Department:")
    depts = ["General Medicine","Cardiology","Orthopedics","Neurology",
             "Pediatrics","Gynecology","Oncology","ENT","Ophthalmology",
             "Dermatology","Psychiatry","Emergency"]
    dept  = depts[choose("Select", depts)]

    print("\n  Assigned Doctor (from registered doctors):")
    d = select_doctor(conn, "Assign Doctor")
    doctor = d["name"] if d else inp("Doctor Name (manual entry)")

    ward      = inp("Ward / Room No.", required=False)
    diagnosis = inp("Diagnosis / Chief Complaint")
    notes     = inp("Notes / Prescriptions", required=False)
    admit_date = inp("Admission Date (YYYY-MM-DD)", required=False) or str(date.today())

    print("\n  Patient Status:")
    status = ["Admitted","Observation","Critical","Discharged"][
              choose("Select", ["Admitted","Observation","Critical","Discharged"])]

    conn.execute("""
        INSERT INTO patients
          (name,age,gender,blood,contact,emergency,address,dept,
           doctor,ward,status,diagnosis,notes,admit_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (name, age, gender, blood, contact, emergency, address, dept,
          doctor, ward, status, diagnosis, notes, admit_date))
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    hr()
    print(f"  ✅   Patient registered!   ID: P-{pid:05d}")
    pause()

def view_patients():
    header("All Patient Records")
    conn = get_conn()
    rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    conn.close()
    if not rows:
        print("\n  No patients registered yet.")
        pause()
        return
    print(f"\n  {'ID':<9} {'Name':<22} {'Age':>3}  {'Gender':<8} {'Blood':<5} {'Status':<12} {'Dept':<20} {'Contact'}")
    hr()
    for r in rows:
        print(f"  P-{r['id']:05d}  {r['name']:<22} {r['age']:>3}  {r['gender']:<8} "
              f"{(r['blood'] or '—'):<5} {r['status']:<12} {(r['dept'] or '—'):<20} {r['contact']}")
    pause()

def search_patient():
    header("Search Patient")
    q    = inp("Enter name, contact or diagnosis")
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM patients WHERE name LIKE ? OR contact LIKE ? OR diagnosis LIKE ?",
        (f"%{q}%", f"%{q}%", f"%{q}%")
    ).fetchall()
    conn.close()
    if not rows:
        print("\n  No matching patients found.")
    else:
        print(f"\n  Found {len(rows)} record(s):\n")
        print(f"  {'ID':<9} {'Name':<22} {'Status':<12} {'Dept':<20} {'Doctor'}")
        hr()
        for r in rows:
            print(f"  P-{r['id']:05d}  {r['name']:<22} {r['status']:<12} "
                  f"{(r['dept'] or '—'):<20} {r['doctor'] or '—'}")
    pause()

def view_patient_detail():
    header("Patient Detail")
    conn = get_conn()
    p    = select_patient(conn, "Select Patient to View")
    conn.close()
    if not p:
        pause(); return
    hr()
    print(f"  ID          : P-{p['id']:05d}")
    print(f"  Name        : {p['name']}")
    print(f"  Age / Gender: {p['age']} / {p['gender']}")
    print(f"  Blood Group : {p['blood'] or '—'}")
    print(f"  Contact     : {p['contact']}")
    print(f"  Emergency   : {p['emergency'] or '—'}")
    print(f"  Address     : {p['address'] or '—'}")
    print(f"  Department  : {p['dept'] or '—'}")
    print(f"  Doctor      : {p['doctor'] or '—'}")
    print(f"  Ward / Room : {p['ward'] or '—'}")
    print(f"  Status      : {p['status']}")
    print(f"  Diagnosis   : {p['diagnosis'] or '—'}")
    print(f"  Notes       : {p['notes'] or '—'}")
    print(f"  Admit Date  : {p['admit_date']}")
    hr()
    pause()

def update_patient():
    header("Update Patient Status")
    conn = get_conn()
    p    = select_patient(conn, "Select Patient to Update")
    if not p:
        conn.close(); pause(); return

    print(f"\n  Patient: {p['name']}  (Current Status: {p['status']})\n")
    print("  What would you like to update?")
    field = ["Status only", "Status + Diagnosis/Notes", "Full record"][
             choose("Select", ["Status only", "Status + Diagnosis/Notes", "Full record"])]

    print("\n  New Status:")
    status = ["Admitted","Observation","Critical","Discharged"][
              choose("Select", ["Admitted","Observation","Critical","Discharged"])]

    diagnosis = p["diagnosis"]
    notes     = p["notes"]
    ward      = p["ward"]
    doctor    = p["doctor"]

    if field in ("Status + Diagnosis/Notes", "Full record"):
        diagnosis = inp("Diagnosis / Chief Complaint") or diagnosis
        notes     = inp("Notes / Prescriptions", required=False) or notes
    if field == "Full record":
        ward   = inp("Ward / Room No.", required=False) or ward
        doctor = inp("Assigned Doctor", required=False) or doctor

    conn.execute(
        "UPDATE patients SET status=?, diagnosis=?, notes=?, ward=?, doctor=? WHERE id=?",
        (status, diagnosis, notes, ward, doctor, p["id"])
    )
    conn.commit()
    conn.close()
    print(f"\n  ✅   Patient P-{p['id']:05d} updated successfully.")
    pause()

def discharge_patient():
    header("Discharge Patient")
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, status FROM patients WHERE status != 'Discharged' ORDER BY id"
    ).fetchall()
    if not rows:
        print("\n  No active (non-discharged) patients.")
        conn.close(); pause(); return
    print("\n  Active Patients:")
    hr("-")
    for r in rows:
        print(f"  P-{r['id']:05d}  {r['name']:<25}  [{r['status']}]")
    hr("-")
    pid = inp_int("  Enter Patient ID to Discharge", lo=1)
    p   = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    if not p:
        print("  ⚠   Patient ID not found.")
        conn.close(); pause(); return
    confirm = inp(f"  Confirm discharge of '{p['name']}'? (yes/no)", required=False)
    if confirm.lower() != "yes":
        print("  Discharge cancelled.")
        conn.close(); pause(); return
    conn.execute("UPDATE patients SET status='Discharged' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    print(f"\n  ✅   {p['name']} has been discharged.")
    pause()

def patient_menu():
    while True:
        header("Patient Management")
        print("  1. ➕  Add New Patient")
        print("  2. 📋  View All Patients")
        print("  3. 🔍  Search Patient")
        print("  4. 🗂   View Patient Detail")
        print("  5. ✏️   Update Patient Status / Record")
        print("  6. 🚪  Discharge Patient")
        print("  0. ←   Back to Main Menu")
        hr()
        ch = inp("Choice")
        if   ch == "1": add_patient()
        elif ch == "2": view_patients()
        elif ch == "3": search_patient()
        elif ch == "4": view_patient_detail()
        elif ch == "5": update_patient()
        elif ch == "6": discharge_patient()
        elif ch == "0": break
        else: print("  ⚠   Invalid choice.")

# ══════════════════════════════════════════════════════════════
#  2. APPOINTMENT MANAGEMENT
# ══════════════════════════════════════════════════════════════

def book_appointment():
    header("Book New Appointment")
    conn = get_conn()

    p = select_patient(conn, "Select Patient")
    if not p:
        conn.close(); pause(); return

    print(f"\n  Patient: {p['name']}  (P-{p['id']:05d})")

    d = select_doctor(conn, "Select Doctor")
    if not d:
        conn.close(); pause(); return

    appt_date = inp("Appointment Date (YYYY-MM-DD)")
    appt_time = inp("Appointment Time (HH:MM, 24hr)", required=False)

    print("\n  Appointment Type:")
    appt_type = ["Consultation","Follow-up","Lab Test","Surgery","Emergency","Routine Check-up"][
                  choose("Select", ["Consultation","Follow-up","Lab Test","Surgery","Emergency","Routine Check-up"])]

    reason = inp("Reason / Notes", required=False)

    # ── Strict availability check — blocks booking outside schedule ──
    day_map = {"Monday":"Mon","Tuesday":"Tue","Wednesday":"Wed","Thursday":"Thu",
               "Friday":"Fri","Saturday":"Sat","Sunday":"Sun"}
    try:
        dt       = datetime.strptime(appt_date, "%Y-%m-%d")
        day_abbr = day_map[dt.strftime("%A")]
        avail_days = [x.strip() for x in d["avail_days"].split(",")]

        # 1. Day check
        if day_abbr not in avail_days:
            print(f"\n  ❌  Booking REJECTED: {d['name']} is not available on {dt.strftime('%A')}.")
            print(f"       Available days : {d['avail_days']}")
            conn.close(); pause(); return

        # 2. Time check (enforced when time is provided)
        if appt_time:
            try:
                t_req  = datetime.strptime(appt_time,    "%H:%M").time()
                t_from = datetime.strptime(d["avail_from"], "%H:%M").time()
                t_to   = datetime.strptime(d["avail_to"],   "%H:%M").time()
                if not (t_from <= t_req <= t_to):
                    print(f"\n  ❌  Booking REJECTED: Requested time {appt_time} is outside")
                    print(f"       {d['name']}'s schedule ({d['avail_from']}–{d['avail_to']}).")
                    print(f"       Please choose a time within the available window.")
                    conn.close(); pause(); return
            except ValueError:
                print("\n  ⚠   Invalid time format. Use HH:MM (e.g. 09:30).")
                conn.close(); pause(); return

    except ValueError:
        print("\n  ⚠   Invalid date format. Use YYYY-MM-DD (e.g. 2025-06-15).")
        conn.close(); pause(); return

    conn.execute("""
        INSERT INTO appointments
          (patient_id, doctor_id, doctor_name, dept, appt_date, appt_time, appt_type, reason)
        VALUES (?,?,?,?,?,?,?,?)
    """, (p["id"], d["id"], d["name"], d["dept"], appt_date, appt_time, appt_type, reason))
    conn.commit()
    aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    hr()
    print(f"  ✅   Appointment booked!   ID: A-{aid:04d}")
    print(f"       Patient : {p['name']}")
    print(f"       Doctor  : {d['name']}  ({d['dept']})")
    print(f"       Date    : {appt_date}  {appt_time or ''}")
    print(f"       Type    : {appt_type}")
    pause()

def view_appointments():
    header("All Appointments")
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*, p.name AS patient_name
        FROM appointments a
        JOIN patients p ON p.id = a.patient_id
        ORDER BY a.appt_date DESC, a.appt_time DESC
    """).fetchall()
    conn.close()
    if not rows:
        print("\n  No appointments found.")
        pause(); return
    print(f"\n  {'ID':<7} {'Patient':<22} {'Doctor':<26} {'Date':<12} {'Time':<7} {'Type':<16} {'Status'}")
    hr()
    for r in rows:
        print(f"  A-{r['id']:04d}  {r['patient_name']:<22} {r['doctor_name']:<26} "
              f"{r['appt_date']:<12} {(r['appt_time'] or '—'):<7} {r['appt_type']:<16} {r['status']}")
    pause()

def view_appointments_by_patient():
    header("Appointments — By Patient")
    conn = get_conn()
    p    = select_patient(conn, "Select Patient")
    if not p:
        conn.close(); pause(); return
    rows = conn.execute(
        "SELECT * FROM appointments WHERE patient_id=? ORDER BY appt_date DESC",
        (p["id"],)
    ).fetchall()
    conn.close()
    print(f"\n  Appointments for: {p['name']}\n")
    if not rows:
        print("  No appointments found for this patient.")
        pause(); return
    print(f"  {'ID':<7} {'Doctor':<26} {'Date':<12} {'Time':<7} {'Type':<16} {'Status'}")
    hr()
    for r in rows:
        print(f"  A-{r['id']:04d}  {r['doctor_name']:<26} {r['appt_date']:<12} "
              f"{(r['appt_time'] or '—'):<7} {r['appt_type']:<16} {r['status']}")
    pause()

def update_appt_status():
    header("Update Appointment Status")
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.id, p.name AS pname, a.doctor_name, a.appt_date, a.status
        FROM appointments a JOIN patients p ON p.id=a.patient_id
        ORDER BY a.id DESC
    """).fetchall()
    if not rows:
        print("\n  No appointments found.")
        conn.close(); pause(); return
    print(f"\n  {'ID':<7} {'Patient':<22} {'Doctor':<26} {'Date':<12} {'Status'}")
    hr()
    for r in rows:
        print(f"  A-{r['id']:04d}  {r['pname']:<22} {r['doctor_name']:<26} {r['appt_date']:<12} {r['status']}")
    hr()
    aid    = inp_int("  Enter Appointment ID", lo=1)
    print("\n  New Status:")
    status = ["Scheduled","Completed","Cancelled"][
              choose("Select", ["Scheduled","Completed","Cancelled"])]
    conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, aid))
    conn.commit()
    conn.close()
    print(f"\n  ✅   Appointment A-{aid:04d} status set to '{status}'.")
    pause()

def appointment_menu():
    while True:
        header("Appointment Management")
        print("  1. 📅  Book New Appointment")
        print("  2. 📋  View All Appointments")
        print("  3. 👤  View Appointments by Patient")
        print("  4. ✏️   Update Appointment Status")
        print("  0. ←   Back to Main Menu")
        hr()
        ch = inp("Choice")
        if   ch == "1": book_appointment()
        elif ch == "2": view_appointments()
        elif ch == "3": view_appointments_by_patient()
        elif ch == "4": update_appt_status()
        elif ch == "0": break
        else: print("  ⚠   Invalid choice.")

# ══════════════════════════════════════════════════════════════
#  3. DOCTOR MANAGEMENT
# ══════════════════════════════════════════════════════════════

def list_doctors():
    header("Registered Doctors")
    conn = get_conn()
    rows = conn.execute("SELECT * FROM doctors ORDER BY id").fetchall()
    conn.close()
    if not rows:
        print("\n  No doctors found.")
        pause(); return
    print(f"\n  {'ID':<5} {'Name':<28} {'Department':<20} {'Qual':<16} {'Hours':<14} {'Days'}")
    hr()
    for r in rows:
        hours = f"{r['avail_from']}–{r['avail_to']}"
        print(f"  {r['id']:<5} {r['name']:<28} {r['dept']:<20} {(r['qual'] or '—'):<16} {hours:<14} {r['avail_days']}")
    pause()

def add_doctor():
    header("Add New Doctor")
    conn = get_conn()

    # Get next available ID
    max_id = conn.execute("SELECT MAX(id) FROM doctors").fetchone()[0] or 0
    new_id = max_id + 1

    name    = inp("Full Name (e.g. Dr. John Smith)")
    print("\n  Department:")
    depts   = ["General Medicine","Cardiology","Orthopedics","Neurology",
               "Pediatrics","Gynecology","Oncology","ENT","Ophthalmology",
               "Dermatology","Psychiatry","Emergency"]
    dept    = depts[choose("Select", depts)]
    qual    = inp("Qualification (e.g. MBBS, MD)", required=False)
    contact = inp("Contact / Extension", required=False)
    avail_from = inp("Available From (HH:MM, e.g. 09:00)", required=False) or "09:00"
    avail_to   = inp("Available To   (HH:MM, e.g. 17:00)", required=False) or "17:00"

    print("\n  Select Available Days (enter numbers separated by commas, e.g. 1,2,3):")
    all_days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for i, d in enumerate(all_days, 1):
        print(f"    {i}. {d}")
    raw_days = inp("Days (e.g. 1,2,3,4,5)")
    selected_days = []
    for part in raw_days.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(all_days):
                selected_days.append(all_days[idx])
    if not selected_days:
        selected_days = ["Mon","Tue","Wed","Thu","Fri"]

    notes = inp("Notes", required=False)

    conn.execute(
        "INSERT INTO doctors VALUES (?,?,?,?,?,?,?,?,?)",
        (new_id, name, dept, qual, contact, avail_from, avail_to, ",".join(selected_days), notes)
    )
    conn.commit()
    conn.close()
    print(f"\n  ✅   Doctor added!   ID: {new_id}  —  {name}")
    pause()

def delete_doctor():
    header("Delete Doctor")
    conn = get_conn()
    rows = conn.execute("SELECT id, name, dept FROM doctors ORDER BY id").fetchall()
    if not rows:
        print("\n  No doctors found.")
        conn.close(); pause(); return
    print("\n  Registered Doctors:")
    hr("-")
    for r in rows:
        print(f"  [{r['id']:>3}]  {r['name']:<28}  {r['dept']}")
    hr("-")
    did = inp_int("  Enter Doctor ID to delete", lo=1)
    d   = conn.execute("SELECT * FROM doctors WHERE id=?", (did,)).fetchone()
    if not d:
        print("  ⚠   Doctor ID not found.")
        conn.close(); pause(); return
    confirm = inp(f"  Delete '{d['name']}'? (yes/no)", required=False)
    if confirm.lower() != "yes":
        print("  Deletion cancelled.")
        conn.close(); pause(); return
    conn.execute("DELETE FROM doctors WHERE id=?", (did,))
    conn.commit()
    conn.close()
    print(f"\n  ✅   Doctor '{d['name']}' deleted.")
    pause()

def doctor_menu():
    while True:
        header("Doctor Management")
        print("  1. 🩺  View All Doctors")
        print("  2. ➕  Add New Doctor")
        print("  3. 🗑   Delete Doctor")
        print("  0. ←   Back to Main Menu")
        hr()
        ch = inp("Choice")
        if   ch == "1": list_doctors()
        elif ch == "2": add_doctor()
        elif ch == "3": delete_doctor()
        elif ch == "0": break
        else: print("  ⚠   Invalid choice.")

# ══════════════════════════════════════════════════════════════
#  4. BILLING
# ══════════════════════════════════════════════════════════════

def generate_bill():
    header("Generate Patient Bill")
    conn = get_conn()
    p    = select_patient(conn, "Select Patient to Bill")
    if not p:
        conn.close(); pause(); return

    print(f"\n  Patient  : {p['name']}  (P-{p['id']:05d})")
    print(f"  Doctor   : {p['doctor'] or '—'}")
    print(f"  Dept     : {p['dept'] or '—'}")
    print("\n  Enter charges (press Enter to skip / leave 0):\n")

    consult  = inp_float("  Consultation Fee    (₹)")
    medicine = inp_float("  Medicine Charges    (₹)")
    lab      = inp_float("  Lab / Test Charges  (₹)")
    room     = inp_float("  Room / Ward Charges (₹)")
    other    = inp_float("  Other Charges       (₹)")
    discount = inp_float("  Discount            (₹)")
    total    = max(0, consult + medicine + lab + room + other - discount)
    notes    = inp("  Description / Notes", required=False)

    print("\n  Payment Status:")
    status = ["Pending","Paid","Partial","Waived"][
              choose("Select", ["Pending","Paid","Partial","Waived"])]

    conn.execute("""
        INSERT INTO bills
          (patient_id,consult,medicine,lab,room,other,discount,total,status,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (p["id"], consult, medicine, lab, room, other, discount, total, status, notes))
    conn.commit()
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    hr("═")
    print(f"  🧾   BILL RECEIPT  —  B-{bid:04d}")
    hr("═")
    print(f"  Patient         : {p['name']}")
    print(f"  Date            : {date.today()}")
    hr("-")
    print(f"  Consultation    : ₹ {consult:>10,.2f}")
    print(f"  Medicine        : ₹ {medicine:>10,.2f}")
    print(f"  Lab / Tests     : ₹ {lab:>10,.2f}")
    print(f"  Room / Ward     : ₹ {room:>10,.2f}")
    print(f"  Other           : ₹ {other:>10,.2f}")
    if discount > 0:
        print(f"  Discount        : ₹ {discount:>10,.2f}  (—)")
    hr("-")
    print(f"  TOTAL           : ₹ {total:>10,.2f}")
    print(f"  Status          : {status}")
    hr("═")
    pause()

def view_bills():
    header("All Bills")
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.*, p.name AS patient_name
        FROM bills b JOIN patients p ON p.id = b.patient_id
        ORDER BY b.id DESC
    """).fetchall()
    conn.close()
    if not rows:
        print("\n  No bills generated yet.")
        pause(); return
    print(f"\n  {'ID':<7} {'Patient':<22} {'Consult':>10} {'Medicine':>10} {'Lab':>8} {'Room':>8} {'Discount':>9} {'Total (₹)':>12}  {'Status':<10}  {'Date'}")
    hr()
    for r in rows:
        print(f"  B-{r['id']:04d}  {r['patient_name']:<22} {r['consult']:>10,.2f} {r['medicine']:>10,.2f} "
              f"{r['lab']:>8,.2f} {r['room']:>8,.2f} {r['discount']:>9,.2f} {r['total']:>12,.2f}  "
              f"{r['status']:<10}  {r['issued']}")
    pause()

def view_bill_detail():
    header("Bill Detail")
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.id, p.name FROM bills b
        JOIN patients p ON p.id=b.patient_id ORDER BY b.id DESC
    """).fetchall()
    if not rows:
        print("\n  No bills found.")
        conn.close(); pause(); return
    for r in rows:
        print(f"  B-{r['id']:04d}  {r['name']}")
    bid = inp_int("\n  Enter Bill ID", lo=1)
    row = conn.execute("""
        SELECT b.*, p.name AS pname, p.contact, p.dept, p.doctor
        FROM bills b JOIN patients p ON p.id=b.patient_id WHERE b.id=?
    """, (bid,)).fetchone()
    conn.close()
    if not row:
        print("  ⚠   Bill not found.")
        pause(); return
    hr("═")
    print(f"  🧾   BILL DETAIL  —  B-{row['id']:04d}")
    hr("═")
    print(f"  Patient     : {row['pname']}  (📞 {row['contact']})")
    print(f"  Department  : {row['dept'] or '—'}      Doctor: {row['doctor'] or '—'}")
    print(f"  Bill Date   : {row['issued']}")
    hr("-")
    print(f"  Consultation: ₹ {row['consult']:>10,.2f}")
    print(f"  Medicine    : ₹ {row['medicine']:>10,.2f}")
    print(f"  Lab / Tests : ₹ {row['lab']:>10,.2f}")
    print(f"  Room / Ward : ₹ {row['room']:>10,.2f}")
    print(f"  Other       : ₹ {row['other']:>10,.2f}")
    print(f"  Discount    : ₹ {row['discount']:>10,.2f}  (—)")
    hr("-")
    print(f"  TOTAL       : ₹ {row['total']:>10,.2f}")
    print(f"  Status      : {row['status']}")
    if row['notes']:
        print(f"  Notes       : {row['notes']}")
    hr("═")
    pause()

def update_bill_status():
    header("Update Bill Payment Status")
    conn = get_conn()
    rows = conn.execute("""
        SELECT b.id, p.name, b.total, b.status
        FROM bills b JOIN patients p ON p.id=b.patient_id
        ORDER BY b.id DESC
    """).fetchall()
    if not rows:
        print("\n  No bills found.")
        conn.close(); pause(); return
    print(f"\n  {'ID':<7} {'Patient':<25} {'Total (₹)':>12}  {'Status'}")
    hr()
    for r in rows:
        print(f"  B-{r['id']:04d}  {r['name']:<25} {r['total']:>12,.2f}  {r['status']}")
    hr()
    bid    = inp_int("  Enter Bill ID", lo=1)
    print("\n  New Payment Status:")
    status = ["Pending","Paid","Partial","Waived"][
              choose("Select", ["Pending","Paid","Partial","Waived"])]
    conn.execute("UPDATE bills SET status=? WHERE id=?", (status, bid))
    conn.commit()
    conn.close()
    print(f"\n  ✅   Bill B-{bid:04d} status set to '{status}'.")
    pause()

def billing_menu():
    while True:
        header("Billing Management")
        print("  1. 💳  Generate New Bill")
        print("  2. 📋  View All Bills")
        print("  3. 🗂   View Bill Detail")
        print("  4. ✏️   Update Payment Status")
        print("  0. ←   Back to Main Menu")
        hr()
        ch = inp("Choice")
        if   ch == "1": generate_bill()
        elif ch == "2": view_bills()
        elif ch == "3": view_bill_detail()
        elif ch == "4": update_bill_status()
        elif ch == "0": break
        else: print("  ⚠   Invalid choice.")

# ══════════════════════════════════════════════════════════════
#  5. HOSPITAL OPERATIONS & SUMMARY REPORT
# ══════════════════════════════════════════════════════════════

def hospital_summary():
    header("Hospital Operations Summary")
    conn = get_conn()

    total_p   = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    admitted  = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Admitted'").fetchone()[0]
    critical  = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Critical'").fetchone()[0]
    obs       = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Observation'").fetchone()[0]
    disc      = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Discharged'").fetchone()[0]

    total_a   = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    sched     = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Scheduled'").fetchone()[0]
    done      = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Completed'").fetchone()[0]
    cancelled = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='Cancelled'").fetchone()[0]

    total_doc = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]

    total_b     = conn.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
    pending_c   = conn.execute("SELECT COUNT(*) FROM bills WHERE status='Pending'").fetchone()[0]
    paid_c      = conn.execute("SELECT COUNT(*) FROM bills WHERE status='Paid'").fetchone()[0]
    revenue     = conn.execute("SELECT COALESCE(SUM(total),0) FROM bills WHERE status='Paid'").fetchone()[0]
    pending_amt = conn.execute("SELECT COALESCE(SUM(total),0) FROM bills WHERE status='Pending'").fetchone()[0]
    total_billed= conn.execute("SELECT COALESCE(SUM(total),0) FROM bills").fetchone()[0]

    # Department breakdown
    dept_rows = conn.execute(
        "SELECT dept, COUNT(*) AS c FROM patients WHERE dept IS NOT NULL AND dept!='' GROUP BY dept ORDER BY c DESC"
    ).fetchall()

    conn.close()

    print(f"\n  📅  Report Date : {date.today()}")
    print()
    print("  ── PATIENTS ──────────────────────────────────────")
    print(f"  Total Registered   : {total_p}")
    print(f"  Currently Admitted : {admitted}")
    print(f"  Under Observation  : {obs}")
    print(f"  Critical Cases     : {critical}")
    print(f"  Discharged         : {disc}")
    print()
    print("  ── APPOINTMENTS ──────────────────────────────────")
    print(f"  Total              : {total_a}")
    print(f"  Scheduled (Upcoming): {sched}")
    print(f"  Completed          : {done}")
    print(f"  Cancelled          : {cancelled}")
    print()
    print("  ── DOCTORS ───────────────────────────────────────")
    print(f"  Total Registered   : {total_doc}")
    print()
    print("  ── BILLING ───────────────────────────────────────")
    print(f"  Total Bills        : {total_b}")
    print(f"  Paid               : {paid_c:<5}  Revenue : ₹ {revenue:>12,.2f}")
    print(f"  Pending            : {pending_c:<5}  Pending : ₹ {pending_amt:>12,.2f}")
    print(f"  Total Billed                        ₹ {total_billed:>12,.2f}")

    if dept_rows:
        print()
        print("  ── DEPT BREAKDOWN ────────────────────────────────")
        for r in dept_rows:
            bar = "█" * r["c"]
            print(f"  {r['dept']:<22}: {r['c']:>3}  {bar}")

    hr()
    pause()

def operations_menu():
    while True:
        header("Hospital Operations")
        print("  1. 📊  Hospital Summary Report")
        print("  2. 🩺  View All Registered Doctors")
        print("  0. ←   Back to Main Menu")
        hr()
        ch = inp("Choice")
        if   ch == "1": hospital_summary()
        elif ch == "2": list_doctors()
        elif ch == "0": break
        else: print("  ⚠   Invalid choice.")

# ══════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════

def main():
    init_db()
    while True:
        header("Main Menu")
        print("  1. 🧑‍🤝‍🧑  Patient Management")
        print("  2. 📅  Appointment Scheduling")
        print("  3. 🩺  Doctor Management")
        print("  4. 💳  Billing")
        print("  5. 🏥  Hospital Operations & Reports")
        print("  0. 🚪  Exit")
        hr()
        ch = inp("Select option")
        if   ch == "1": patient_menu()
        elif ch == "2": appointment_menu()
        elif ch == "3": doctor_menu()
        elif ch == "4": billing_menu()
        elif ch == "5": operations_menu()
        elif ch == "0":
            clear()
            print("\n  Goodbye! Stay healthy. 🏥\n")
            break
        else:
            print("  ⚠   Invalid option. Please try again.")

if __name__ == "__main__":
    main()
