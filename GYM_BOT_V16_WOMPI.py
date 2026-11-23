import sqlite3,hashlib,json,socket,io,random,mimetypes,re,os,hmac,base64,secrets
import threading
from pathlib import Path
from datetime import datetime, date, timedelta
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from wompi_payments import create_checkout, verify_event, wompi_configured


def get_local_ip():
 try:
  sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.connect(('8.8.8.8',80)); ip=sock.getsockname()[0]; sock.close(); return ip
 except Exception:
  try:return socket.gethostbyname(socket.gethostname())
  except Exception:return '127.0.0.1'

BASE=Path(__file__).resolve().parent; DB_PATH=BASE/'gymbot_v5.db'; PORT=8000; LOCAL_IP=get_local_ip(); MOBILE_URL=f'http://{LOCAL_IP}:{PORT}'
def load_env_file():
 env_file=BASE/'.env'
 if not env_file.exists(): return
 for line in env_file.read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#') or '=' not in line: continue
  key,value=line.split('=',1);key=key.strip();value=value.strip().strip('"').strip("'")
  if key and key not in os.environ: os.environ[key]=value
load_env_file()

EXERCISES=[('Press banca', 'Pecho', 'Barra', 'Principiante', '3', '8-12', '90'), ('Press inclinado con mancuernas', 'Pecho', 'Mancuernas', 'Principiante', '3', '8-12', '90'), ('Press pecho máquina', 'Pecho', 'Máquina', 'Principiante', '3', '10-12', '75'), ('Aperturas máquina', 'Pecho', 'Máquina', 'Principiante', '2', '12-15', '60'), ('Cruce de poleas', 'Pecho', 'Polea', 'Intermedio', '3', '12-15', '60'), ('Jalón al pecho', 'Espalda', 'Polea', 'Principiante', '3', '8-12', '90'), ('Remo sentado', 'Espalda', 'Polea', 'Principiante', '3', '10-12', '90'), ('Remo con mancuerna', 'Espalda', 'Mancuernas', 'Principiante', '3', '10-12', '90'), ('Remo con barra', 'Espalda', 'Barra', 'Intermedio', '3', '6-10', '120'), ('Dominadas asistidas', 'Espalda', 'Máquina', 'Principiante', '3', '6-10', '120'), ('Pullover en polea', 'Espalda', 'Polea', 'Intermedio', '2', '12-15', '60'), ('Sentadilla goblet', 'Piernas', 'Mancuernas', 'Principiante', '3', '10-12', '90'), ('Prensa de piernas', 'Piernas', 'Máquina', 'Principiante', '3', '10-15', '90'), ('Extensión de cuádriceps', 'Piernas', 'Máquina', 'Principiante', '3', '12-15', '60'), ('Curl femoral', 'Piernas', 'Máquina', 'Principiante', '3', '10-15', '60'), ('Peso muerto rumano', 'Piernas', 'Barra', 'Intermedio', '3', '8-12', '120'), ('Hip thrust', 'Glúteos', 'Barra', 'Principiante', '3', '8-12', '90'), ('Zancadas', 'Piernas', 'Mancuernas', 'Intermedio', '3', '10-12', '90'), ('Elevación de gemelos', 'Pantorrilla', 'Máquina', 'Principiante', '3', '12-20', '60'), ('Press hombros máquina', 'Hombros', 'Máquina', 'Principiante', '3', '8-12', '90'), ('Press hombros mancuernas', 'Hombros', 'Mancuernas', 'Intermedio', '3', '8-12', '90'), ('Elevaciones laterales', 'Hombros', 'Mancuernas', 'Principiante', '3', '12-15', '60'), ('Face pull', 'Hombros', 'Polea', 'Principiante', '3', '12-15', '60'), ('Curl bíceps mancuernas', 'Bíceps', 'Mancuernas', 'Principiante', '3', '10-15', '60'), ('Curl barra', 'Bíceps', 'Barra', 'Intermedio', '3', '8-12', '75'), ('Curl martillo', 'Bíceps', 'Mancuernas', 'Principiante', '2', '10-15', '60'), ('Tríceps polea', 'Tríceps', 'Polea', 'Principiante', '3', '10-15', '60'), ('Extensión tríceps sobre cabeza', 'Tríceps', 'Polea', 'Intermedio', '3', '10-15', '60'), ('Fondos asistidos', 'Tríceps', 'Máquina', 'Intermedio', '3', '8-12', '90'), ('Plancha', 'Core', 'Peso corporal', 'Principiante', '3', '30-45 s', '45'), ('Crunch en polea', 'Core', 'Polea', 'Principiante', '3', '12-15', '45'), ('Elevación de rodillas', 'Core', 'Peso corporal', 'Principiante', '3', '10-15', '45'), ('Bicicleta estática', 'Cardio', 'Cardio', 'Principiante', '1', '15-30 min', '—'), ('Caminata inclinada', 'Cardio', 'Cardio', 'Principiante', '1', '15-30 min', '—'), ('Remo ergómetro', 'Cardio', 'Cardio', 'Principiante', '1', '10-20 min', '—'), ('Escaladora', 'Cardio', 'Cardio', 'Intermedio', '1', '10-20 min', '—'), ('Abducción de cadera', 'Glúteos', 'Máquina', 'Principiante', '3', '12-20', '60'), ('Extensión lumbar', 'Espalda', 'Máquina', 'Principiante', '3', '10-15', '60')]
PROGRAMS={'Full Body · 3 días': [('Día 1', ['Press pecho máquina', 'Jalón al pecho', 'Prensa de piernas', 'Press hombros máquina', 'Curl bíceps mancuernas', 'Tríceps polea']), ('Día 2', ['Press inclinado con mancuernas', 'Remo sentado', 'Sentadilla goblet', 'Curl femoral', 'Elevaciones laterales', 'Plancha']), ('Día 3', ['Press banca', 'Dominadas asistidas', 'Hip thrust', 'Extensión de cuádriceps', 'Curl martillo', 'Crunch en polea'])], 'Upper / Lower · 4 días': [('Día 1 · Upper', ['Press banca', 'Jalón al pecho', 'Press hombros mancuernas', 'Remo sentado', 'Curl barra', 'Tríceps polea']), ('Día 2 · Lower', ['Prensa de piernas', 'Peso muerto rumano', 'Extensión de cuádriceps', 'Curl femoral', 'Elevación de gemelos', 'Plancha']), ('Día 3 · Upper', ['Press inclinado con mancuernas', 'Remo con barra', 'Press pecho máquina', 'Face pull', 'Curl martillo', 'Extensión tríceps sobre cabeza']), ('Día 4 · Lower', ['Sentadilla goblet', 'Hip thrust', 'Zancadas', 'Curl femoral', 'Elevación de gemelos', 'Crunch en polea'])], 'PPL · 6 días': [('Día 1 · Push', ['Press banca', 'Press inclinado con mancuernas', 'Press hombros máquina', 'Elevaciones laterales', 'Tríceps polea']), ('Día 2 · Pull', ['Jalón al pecho', 'Remo con barra', 'Remo sentado', 'Face pull', 'Curl barra']), ('Día 3 · Legs', ['Prensa de piernas', 'Peso muerto rumano', 'Extensión de cuádriceps', 'Curl femoral', 'Elevación de gemelos']), ('Día 4 · Push', ['Press pecho máquina', 'Cruce de poleas', 'Press hombros mancuernas', 'Elevaciones laterales', 'Extensión tríceps sobre cabeza']), ('Día 5 · Pull', ['Dominadas asistidas', 'Remo con mancuerna', 'Pullover en polea', 'Curl martillo', 'Curl bíceps mancuernas']), ('Día 6 · Legs', ['Sentadilla goblet', 'Hip thrust', 'Zancadas', 'Curl femoral', 'Elevación de gemelos', 'Plancha'])]}
HTML = (BASE / 'templates' / 'app.html').read_text(encoding='utf-8')
def hp(x): return hashlib.sha256(x.encode()).hexdigest()
def issue_payment_token(user_id, role):
 secret=os.getenv('GYMBOT_SESSION_SECRET','')
 if len(secret)<32: return None
 payload=json.dumps({'uid':int(user_id),'role':str(role),'exp':int(datetime.utcnow().timestamp())+8*60*60},separators=(',',':')).encode()
 body=base64.urlsafe_b64encode(payload).decode().rstrip('=')
 sig=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()
 return body+'.'+sig
def verify_payment_token(token):
 try:
  body,sig=token.split('.',1);secret=os.getenv('GYMBOT_SESSION_SECRET','')
  expected=hmac.new(secret.encode(),body.encode(),hashlib.sha256).hexdigest()
  if len(secret)<32 or not hmac.compare_digest(expected,sig):return None
  payload=json.loads(base64.urlsafe_b64decode(body+'='*((4-len(body)%4)%4)))
  if int(payload.get('exp',0))<int(datetime.utcnow().timestamp()):return None
  return payload
 except Exception:return None

class DB:
 def __init__(self):
  self.c=sqlite3.connect(str(DB_PATH),check_same_thread=False);self.c.row_factory=sqlite3.Row
  self.c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,username TEXT UNIQUE,password TEXT,role TEXT,age INTEGER,height REAL,weight REAL,goal TEXT,level TEXT,days INTEGER,created TEXT,email TEXT,phone TEXT,avatar TEXT);
CREATE TABLE IF NOT EXISTS exercises(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,muscle TEXT,equipment TEXT,level TEXT,sets TEXT,reps TEXT,rest TEXT,description TEXT,video_url TEXT);
CREATE TABLE IF NOT EXISTS routines(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,name TEXT,goal TEXT,created TEXT,week_number INTEGER,week_start TEXT,week_end TEXT,status TEXT,completed_at TEXT);
CREATE TABLE IF NOT EXISTS routine_items(id INTEGER PRIMARY KEY AUTOINCREMENT,routine_id INTEGER,day TEXT,exercise_id INTEGER,position INTEGER);
CREATE TABLE IF NOT EXISTS routine_days(id INTEGER PRIMARY KEY AUTOINCREMENT,routine_id INTEGER,day_index INTEGER,day TEXT,status TEXT DEFAULT 'pending',completed_at TEXT,UNIQUE(routine_id,day));
CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,exercise_id INTEGER,date TEXT,weight REAL,reps INTEGER,sets INTEGER,rpe REAL,notes TEXT);\nCREATE TABLE IF NOT EXISTS memberships(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,plan TEXT NOT NULL,start_date TEXT,end_date TEXT,status TEXT NOT NULL DEFAULT 'pending_payment',payment_status TEXT NOT NULL DEFAULT 'pending',last_notice TEXT,created TEXT NOT NULL); CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,reference TEXT NOT NULL UNIQUE,amount_cop INTEGER NOT NULL,currency TEXT NOT NULL DEFAULT 'COP',status TEXT NOT NULL DEFAULT 'PENDING',wompi_transaction_id TEXT,created TEXT NOT NULL,updated TEXT,processed_at TEXT);''')
  usercols={row['name'] for row in self.c.execute('PRAGMA table_info(users)').fetchall()}
  for col,typ in [('email','TEXT'),('phone','TEXT'),('avatar','TEXT')]:
   if col not in usercols:self.c.execute(f'ALTER TABLE users ADD COLUMN {col} {typ}')
  self.migrate_routines()
  excols={row['name'] for row in self.c.execute('PRAGMA table_info(exercises)').fetchall()}
  if 'video_url' not in excols:self.c.execute('ALTER TABLE exercises ADD COLUMN video_url TEXT')
  self.c.execute("UPDATE exercises SET video_url=COALESCE(NULLIF(video_url,''),'https://www.youtube.com/results?search_query='||replace(name,' ','+'))")
  if self.c.execute('SELECT COUNT(*) FROM exercises').fetchone()[0]==0:
   for e in EXERCISES:self.c.execute('INSERT INTO exercises(name,muscle,equipment,level,sets,reps,rest,description) VALUES(?,?,?,?,?,?,?,?)',(*e,'Movimiento controlado; prioriza técnica y rango cómodo.'))
  self.c.execute("UPDATE exercises SET video_url=COALESCE(NULLIF(video_url,''),'https://www.youtube.com/results?search_query='||replace(name,' ','+'))")
  curated_videos={'Press banca':'https://www.youtube.com/watch?v=7aQY3u0Dk-Q','Peso muerto rumano':'https://www.youtube.com/watch?v=SOYfVYuZ_vQ','Sentadilla goblet':'https://www.youtube.com/watch?v=tCQcDTZhZ4k'}
  for _name,_url in curated_videos.items():self.c.execute('UPDATE exercises SET video_url=? WHERE name=?',(_url,_name))
  if self.c.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0:
   self.add_user('Administrador','admin','admin123','ADMIN',30,175,75,'Gestión','Avanzado',6);self.add_user('Usuario Demo','usuario','1234','USUARIO',25,175,75,'Hipertrofia','Principiante',3)
  self.c.commit()
 def migrate_routines(self):
  cols={row['name'] for row in self.c.execute('PRAGMA table_info(routines)').fetchall()}
  for col,typ in [('week_number','INTEGER'),('week_start','TEXT'),('week_end','TEXT'),('status','TEXT'),('completed_at','TEXT')]:
   if col not in cols:self.c.execute(f'ALTER TABLE routines ADD COLUMN {col} {typ}')
  rows=self.c.execute('SELECT id,created,week_number,week_start,week_end,status FROM routines ORDER BY id').fetchall()
  for r in rows:
   dt=datetime.fromisoformat(r['created']) if r['created'] else datetime.now()
   monday=dt.date()
   monday=monday.fromordinal(monday.toordinal()-monday.weekday())
   start=monday.isoformat();end=(monday.fromordinal(monday.toordinal()+6)).isoformat()
   week=int(r['week_number'] or r['id'] or 1)
   status=r['status'] or ('active' if r['id']==rows[-1]['id'] else 'history')
   self.c.execute('UPDATE routines SET week_number=?,week_start=?,week_end=?,status=? WHERE id=?',(week,r['week_start'] or start,r['week_end'] or end,status,r['id']))
   existing=self.c.execute('SELECT COUNT(*) FROM routine_days WHERE routine_id=?',(r['id'],)).fetchone()[0]
   if existing==0:
    ds=self.c.execute('SELECT day FROM routine_items WHERE routine_id=? GROUP BY day ORDER BY MIN(position)',(r['id'],)).fetchall()
    for idx,day in enumerate(ds):self.c.execute('INSERT OR IGNORE INTO routine_days(routine_id,day_index,day,status) VALUES(?,?,?,?)',(r['id'],idx,day['day'],'pending'))
  self.c.commit()
 def routine_days(self,rid):
  return self.c.execute('SELECT * FROM routine_days WHERE routine_id=? ORDER BY day_index',(rid,)).fetchall()
 def active_routine(self,u):
  return self.c.execute("SELECT * FROM routines WHERE user_id=? ORDER BY id DESC LIMIT 1",(u,)).fetchone()
 def complete_day(self,u,rid,day):
  r=self.c.execute('SELECT * FROM routines WHERE id=? AND user_id=?',(rid,u)).fetchone()
  if not r:raise ValueError('Rutina no encontrada')
  self.c.execute("UPDATE routine_days SET status='completed',completed_at=? WHERE routine_id=? AND day=?",(datetime.now().isoformat(),rid,day))
  pending=self.c.execute("SELECT COUNT(*) FROM routine_days WHERE routine_id=? AND status!='completed'",(rid,)).fetchone()[0]
  completed=pending==0
  if completed:self.c.execute("UPDATE routines SET status='completed',completed_at=? WHERE id=?",(datetime.now().isoformat(),rid))
  self.c.commit();return completed
 def add_user(self,n,u,p,r,a,h,w,g,l,d):
  x=self.c.execute('INSERT INTO users(name,username,password,role,age,height,weight,goal,level,days,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(n,u,hp(p),r,a,h,w,g,l,d,datetime.now().isoformat()));self.c.commit();return x.lastrowid
 def auth(self,u,p):return self.c.execute('SELECT * FROM users WHERE username=? AND password=?',(u,hp(p))).fetchone()
 def users(self):return self.c.execute('SELECT id,name,username,role,age,height,weight,goal,level,days,email,phone,avatar FROM users ORDER BY id DESC').fetchall()
 def user(self,i):return self.c.execute('SELECT * FROM users WHERE id=?',(i,)).fetchone()
 def exercises(self,q=''):
  q='%'+q+'%';return self.c.execute('SELECT * FROM exercises WHERE name LIKE ? OR muscle LIKE ? OR equipment LIKE ? ORDER BY muscle,name',(q,q,q)).fetchall()
 def ex(self,n):return self.c.execute('SELECT * FROM exercises WHERE name=?',(n,)).fetchone()
 def logs(self,u):return self.c.execute('SELECT l.*,e.name exercise FROM logs l JOIN exercises e ON e.id=l.exercise_id WHERE l.user_id=? ORDER BY l.id DESC LIMIT 50',(u,)).fetchall()
 def routines(self,u):return self.c.execute('SELECT * FROM routines WHERE user_id=? ORDER BY id DESC',(u,)).fetchall()
 def items(self,r):return self.c.execute('SELECT ri.day,e.* FROM routine_items ri JOIN exercises e ON e.id=ri.exercise_id WHERE ri.routine_id=? ORDER BY ri.day,ri.position',(r,)).fetchall()
 def save_routine(self,u,n,g,seq):
  now=datetime.now();monday=now.date();monday=monday.fromordinal(monday.toordinal()-monday.weekday());start=monday.isoformat();end=monday.fromordinal(monday.toordinal()+6).isoformat()
  prev=self.c.execute('SELECT COALESCE(MAX(week_number),0) FROM routines WHERE user_id=?',(u,)).fetchone()[0] or 0
  self.c.execute("UPDATE routines SET status='history' WHERE user_id=? AND status='active'",(u,))
  x=self.c.execute('INSERT INTO routines(user_id,name,goal,created,week_number,week_start,week_end,status) VALUES(?,?,?,?,?,?,?,?)',(u,n,g,now.isoformat(),prev+1,start,end,'active'));rid=x.lastrowid
  for idx,(day,names) in enumerate(seq):
   self.c.execute('INSERT INTO routine_days(routine_id,day_index,day,status) VALUES(?,?,?,?)',(rid,idx,day,'pending'))
   for pos,name in enumerate(names):
    e=self.ex(name)
    if e:self.c.execute('INSERT INTO routine_items(routine_id,day,exercise_id,position) VALUES(?,?,?,?)',(rid,day,e['id'],pos))
  self.c.commit()
  return rid
 def history(self,u):return self.c.execute('SELECT * FROM routines WHERE user_id=? ORDER BY week_number DESC,id DESC',(u,)).fetchall()
 def admin_detail(self,u):
  user=self.user(u);active=self.active_routine(u)
  return {'user':dict(user) if user else None,'active':dict(active) if active else None,'routines':[dict(x) for x in self.history(u)],'days':[dict(x) for x in self.routine_days(active['id'])] if active else [],'items':[dict(x) for x in self.items(active['id'])] if active else [],'logs':[dict(x) for x in self.logs(u)]}
 def log(self,u,e,w,r,s,rpe,n):self.c.execute('INSERT INTO logs(user_id,exercise_id,date,weight,reps,sets,rpe,notes) VALUES(?,?,?,?,?,?,?,?)',(u,e,datetime.now().strftime('%Y-%m-%d %H:%M'),w,r,s,rpe,n));self.c.commit()
 def membership(self,u):
  row=self.c.execute('SELECT * FROM memberships WHERE user_id=? ORDER BY id DESC LIMIT 1',(u,)).fetchone()
  if not row:return None
  d=dict(row)
  if d.get('end_date') and d.get('status')=='active':
   try:
    remaining=(date.fromisoformat(d['end_date'])-date.today()).days
    d['days_remaining']=remaining
    if remaining<0:d['status']='expired'
    elif remaining<=5:d['status']='expiring'
   except ValueError:d['days_remaining']=None
  return d
 def memberships(self):
  rows=self.c.execute('SELECT m.*,u.name,u.username FROM memberships m JOIN users u ON u.id=m.user_id WHERE m.id=(SELECT MAX(m2.id) FROM memberships m2 WHERE m2.user_id=m.user_id) ORDER BY m.end_date').fetchall()
  out=[]
  for row in rows:
   d=dict(row)
   try:
    rem=(date.fromisoformat(d['end_date'])-date.today()).days if d.get('end_date') else None
   except ValueError:rem=None
   d['days_remaining']=rem
   if d['status']=='active' and rem is not None:
    if rem<0:d['status']='expired'
    elif rem<=5:d['status']='expiring'
   out.append(d)
  return out
 def activate_membership(self,u,plan='Mensual',days=30):
  if not self.user(u):raise ValueError('Cliente no encontrado')
  start=date.today()
  current=self.c.execute("SELECT end_date FROM memberships WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",(u,)).fetchone()
  if current and current['end_date']:
   try:
    previous_end=date.fromisoformat(current['end_date'])
    if previous_end>=start:start=previous_end+timedelta(days=1)
   except ValueError:pass
  end=start+timedelta(days=max(1,min(int(days),365)))
  self.c.execute("UPDATE memberships SET status='expired' WHERE user_id=? AND status='active'",(u,))
  self.c.execute('INSERT INTO memberships(user_id,plan,start_date,end_date,status,payment_status,created) VALUES(?,?,?,?,?,?,?)',(u,plan,start.isoformat(),end.isoformat(),'active','manual_pending_gateway',datetime.now().isoformat()))
  self.c.commit()
  return self.membership(u)
 def delete_user(self,u):
  self.c.execute('DELETE FROM memberships WHERE user_id=?',(u,))
  self.c.execute('DELETE FROM logs WHERE user_id=?',(u,))
  rids=[x['id'] for x in self.c.execute('SELECT id FROM routines WHERE user_id=?',(u,)).fetchall()]
  for rid in rids:self.c.execute('DELETE FROM routine_items WHERE routine_id=?',(rid,))
  self.c.execute('DELETE FROM routines WHERE user_id=?',(u,))
  self.c.execute('DELETE FROM users WHERE id=?',(u,))
  self.c.commit()
db=DB()
PAYMENT_LOCK=threading.Lock()
def send(h,c,d):
 raw=json.dumps(d,ensure_ascii=False).encode();h.send_response(c);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Content-Length',str(len(raw)));h.end_headers();h.wfile.write(raw)
def css_for_connect():
 return '''<style>html,body{margin:0;min-height:100%;font-family:Inter,Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 50% 0,#294422 0,transparent 40%),#070a08;color:#f5f7f2}.connect{min-height:100vh;display:grid;place-items:center;padding:24px}.connect-card{width:min(430px,100%);box-sizing:border-box;text-align:center;background:linear-gradient(145deg,#141d17,#0a0f0c);border:1px solid #334435;border-radius:28px;padding:34px;box-shadow:0 35px 100px #0009}.eyebrow{color:#c9ff4d;font-size:10px;font-weight:900;letter-spacing:1.8px}.connect-card h1{font-size:34px;letter-spacing:-1.5px;margin:10px 0}.connect-card p{color:#9aa79c;line-height:1.55}.connect-card img{width:230px;height:230px;background:#fff;padding:10px;border-radius:18px;margin:14px auto}.url{font-family:monospace;color:#c9ff4d;background:#0a100c;border:1px solid #26342a;border-radius:11px;padding:11px;word-break:break-all}.small{font-size:11px}.connect-card button{border:0;border-radius:12px;padding:12px 18px;background:#c9ff4d;color:#121b06;font-weight:900}</style>'''

LANDING = (BASE / 'templates' / 'index.html').read_text(encoding='utf-8')

class H(BaseHTTPRequestHandler):
 def body(self):return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
 def do_GET(self):
  p=urlparse(self.path);q=parse_qs(p.query)
  try:
   if p.path.startswith('/static/'):
    relative=p.path[len('/static/'):].lstrip('/')
    asset=(BASE/'static'/relative).resolve()
    static_root=(BASE/'static').resolve()
    if static_root not in asset.parents or not asset.is_file():
     self.send_error(404);return
    raw=asset.read_bytes()
    content_type=mimetypes.guess_type(str(asset))[0] or 'application/octet-stream'
    self.send_response(200);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
   if p.path=='/':raw=LANDING.encode('utf-8');self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
   if p.path=='/app':raw=HTML.encode('utf-8');self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
   if p.path=='/connect':
    page=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="theme-color" content="#070a08"><meta name="application-name" content="GYM BOT V10"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Conectar · GYM BOT V13</title>{css_for_connect()}</head><body><main class="connect"><div class="connect-card"><div class="eyebrow">GYM BOT V13 · ACCESO MÓVIL</div><h1>Conecta tu celular</h1><p>Escanea el código QR con el celular conectado a la misma red Wi-Fi.</p><img src="/qr.png" alt="QR GYM BOT"><div class="url">{MOBILE_URL}</div><p class="small">Si el QR no funciona, abre manualmente la dirección anterior.</p><button onclick="window.close()">Cerrar</button></div></main></body></html>'''.encode('utf-8')
    self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(page)));self.end_headers();self.wfile.write(page);return
   if p.path=='/qr.png':
    import qrcode
    img=qrcode.make(MOBILE_URL)
    buf=io.BytesIO();img.save(buf,format='PNG');raw=buf.getvalue()
    self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
   if p.path=='/api/network':return send(self,200,{'ip':LOCAL_IP,'url':MOBILE_URL,'port':PORT})
   if p.path=='/api/dashboard':
    u=db.user(int(q['uid'][0]))
    if u['role']!='USUARIO':
     clients=[dict(x) for x in db.users() if x['role']=='USUARIO']
     active=0; completed_days=0; total_days=0; recent=[]
     for cu in clients:
      rs=db.routines(cu['id'])
      if rs:
       r=rs[0]; active+=1
       days=db.routine_days(r['id']); done=sum(1 for x in days if x['status']=='completed')
       completed_days+=done; total_days+=len(days)
       recent.append({'name':cu['name'],'goal':cu['goal'],'level':cu['level'],'progress':round(done/len(days)*100) if days else 0,'routine':r['name']})
     avg=round(completed_days/total_days*100) if total_days else 0
     recent=sorted(recent,key=lambda x:x['progress'],reverse=True)[:5]
     return send(self,200,{'user':dict(u),'stats':[[len(clients),'Clientes'],[active,'Rutinas activas'],[avg,'% cumplimiento'],[len(db.exercises()),'Ejercicios']],'admin':{'recent':recent}})
    rcount=len(db.routines(u['id']))
    return send(self,200,{'user':dict(u),'stats':[[len(db.logs(u['id'])),'Entrenamientos'],[len(db.exercises()),'Ejercicios'],[rcount,'Rutinas asignadas'],[u['level'] or '—','Nivel']]})
   if p.path=='/api/routines':
    uid=int(q['uid'][0]);rows=[dict(x) for x in db.routines(uid)];return send(self,200,rows)
   if p.path=='/api/routine':
    r=db.c.execute('SELECT * FROM routines WHERE id=?',(int(q['id'][0]),)).fetchone()
    if not r:raise ValueError('Rutina no encontrada')
    return send(self,200,{'routine':dict(r),'items':[dict(x) for x in db.items(r['id'])],'days':[dict(x) for x in db.routine_days(r['id'])]})
   if p.path=='/api/routine_state':
    uid=int(q['uid'][0]);r=db.active_routine(uid)
    if not r:return send(self,200,{'has_routine':False,'can_generate':True})
    days=db.routine_days(r['id']);done=sum(1 for x in days if x['status']=='completed');total=len(days)
    return send(self,200,{'has_routine':True,'can_generate':done>=total and total>0,'completed':done>=total and total>0,'completed_days':done,'total_days':total,'routine':dict(r)})
   if p.path=='/api/exercises':return send(self,200,[dict(x) for x in db.exercises(q.get('q',[''])[0])])
   if p.path=='/api/progress':return send(self,200,{'exercises':[dict(x) for x in db.exercises()],'logs':[dict(x) for x in db.logs(int(q['uid'][0]))]})
   if p.path=='/api/memberships':
    return send(self,200,db.memberships())
   if p.path=='/api/membership':
    uid=int(q['uid'][0]);m=db.membership(uid)
    return send(self,200,{'membership':m})
   if p.path=='/api/users':return send(self,200,[dict(x) for x in db.users()])
   if p.path=='/api/admin/user_detail':return send(self,200,db.admin_detail(int(q['uid'][0])))
   if p.path=='/api/ai_status':
    import os
    return send(self,200,{'enabled':bool(os.getenv('OPENAI_API_KEY','').strip()),'model':os.getenv('GYMBOT_AI_MODEL','gpt-5-mini')})
   return send(self,404,{'error':'Ruta no encontrada'})
  except Exception as e:return send(self,500,{'error':str(e)})
 def generate_routine(self,d):
  uid=int(d['uid']);current=db.active_routine(uid)
  if current:
   cdays=db.routine_days(current['id']);done=sum(1 for x in cdays if x['status']=='completed')
   if cdays and done<len(cdays):raise ValueError('Tu semana actual todavía está activa. Completa todas las sesiones antes de generar una nueva.')
  goal=d.get('goal','Hipertrofia'); level=d.get('level','Principiante'); days=max(2,min(6,int(d.get('days',3)))); time=max(30,min(90,int(d.get('time',60)))); equipment=d.get('equipment','Gimnasio completo'); avoid=(d.get('avoid') or '').lower()
  allowed={'Peso corporal','Mancuernas'} if equipment=='Casa' else ({'Mancuernas','Peso corporal'} if equipment=='Mancuernas' else ({'Máquina','Polea','Cardio','Peso corporal'} if equipment=='Máquinas' else None))
  exs=[dict(x) for x in db.exercises()]; words=[w.strip() for w in avoid.replace(',',';').split(';') if w.strip()]
  def ok(e):
   if allowed is not None and e['equipment'] not in allowed:return False
   if level in ('Principiante','Intermedio') and e['level']=='Avanzado':return False
   return not any(w in (e['name']+' '+e['muscle']+' '+e['equipment']).lower() for w in words)
  exs=[e for e in exs if ok(e) and e['muscle']!='Cardio']; by={}
  recent_names=set()
  recent=db.c.execute('SELECT ri.exercise_id FROM routine_items ri JOIN routines r ON r.id=ri.routine_id WHERE r.user_id=? ORDER BY r.id DESC LIMIT 40',(uid,)).fetchall()
  recent_names={db.c.execute('SELECT name FROM exercises WHERE id=?',(x['exercise_id'],)).fetchone()['name'] for x in recent}
  rng=random.Random(uid*1009 + (db.c.execute('SELECT COUNT(*) FROM routines WHERE user_id=?',(uid,)).fetchone()[0] or 0)*917)
  for e in exs:by.setdefault(e['muscle'],[]).append(e)
  for muscle in by:rng.shuffle(by[muscle])
  priorities={'Hipertrofia':['Pecho','Espalda','Piernas','Glúteos','Hombros','Bíceps','Tríceps','Core'],'Fuerza':['Pecho','Espalda','Piernas','Hombros','Bíceps','Tríceps','Core'],'Pérdida de grasa':['Piernas','Espalda','Pecho','Hombros','Glúteos','Core','Bíceps','Tríceps'],'Acondicionamiento':['Piernas','Espalda','Pecho','Hombros','Core','Glúteos','Bíceps','Tríceps']}.get(goal,['Pecho','Espalda','Piernas','Hombros','Bíceps','Tríceps','Core'])
  patterns={2:[('Día 1 · Full Body',priorities[:5]),('Día 2 · Full Body',priorities[2:7])],3:[('Día 1 · Full Body',priorities[:5]),('Día 2 · Full Body',priorities[1:6]),('Día 3 · Full Body',priorities[2:7])],4:[('Día 1 · Upper',priorities[:4]+['Bíceps']),('Día 2 · Lower',['Piernas','Glúteos','Core','Pantorrilla']),('Día 3 · Upper',priorities[1:5]+['Tríceps']),('Día 4 · Lower',['Piernas','Glúteos','Core','Pantorrilla'])],5:[('Día 1 · Push',['Pecho','Hombros','Tríceps']),('Día 2 · Pull',['Espalda','Bíceps','Hombros']),('Día 3 · Legs',['Piernas','Glúteos','Pantorrilla','Core']),('Día 4 · Upper',['Pecho','Espalda','Hombros','Bíceps','Tríceps']),('Día 5 · Lower',['Piernas','Glúteos','Pantorrilla','Core'])],6:[('Día 1 · Push',['Pecho','Hombros','Tríceps']),('Día 2 · Pull',['Espalda','Bíceps','Hombros']),('Día 3 · Legs',['Piernas','Glúteos','Pantorrilla','Core']),('Día 4 · Push',['Pecho','Hombros','Tríceps']),('Día 5 · Pull',['Espalda','Bíceps','Hombros']),('Día 6 · Legs',['Piernas','Glúteos','Pantorrilla','Core'])]}
  max_ex=4 if time<=40 else (5 if time<=60 else 6)
  if level=='Principiante' or d.get('experience')=='Baja':max_ex=max(3,min(max_ex,5))
  seq=[];out=[];used=set()
  for day,muscles in patterns[days]:
   names=[];detail=[]
   for muscle in muscles:
    candidates=[e for e in by.get(muscle,[]) if e['name'] not in used]
    fresh=[e for e in candidates if e['name'] not in recent_names]
    candidates=(fresh or candidates)
    candidates=sorted(candidates,key=lambda e:(e['level']!=level))
    if not candidates:continue
    e=candidates[0];used.add(e['name']);names.append(e['name']);detail.append(e)
    if len(names)>=max_ex:break
   if len(names)<max_ex:
    for e in exs:
     if e['name'] not in used:names.append(e['name']);detail.append(e);used.add(e['name'])
     if len(names)>=max_ex:break
   seq.append((day,names));out.append({'day':day,'exercises':detail})
  next_week=(db.c.execute('SELECT COALESCE(MAX(week_number),0) FROM routines WHERE user_id=?',(uid,)).fetchone()[0] or 0)+1
  name=f"Semana {next_week} · Plan personalizado · {days} días";rid=db.save_routine(uid,name,goal,seq)
  return {'routine':{'id':rid,'name':name,'goal':goal,'days':days,'time':time,'week_number':next_week},'days':out}
 def ai_chat_answer(self,d):
  import os
  try:
   from openai import OpenAI
  except Exception:
   return None
  key=os.getenv('OPENAI_API_KEY','').strip()
  if not key:return None
  model=os.getenv('GYMBOT_AI_MODEL','gpt-5.6-luna').strip() or 'gpt-5.6-luna'
  uid=int(d.get('uid') or 0)
  user=db.user(uid) if uid else None
  routine=db.active_routine(uid) if uid else None
  profile='Sin perfil cargado.'
  if user:
   profile=f"Nombre: {user['name']} | Rol: {user['role']} | Objetivo: {user['goal']} | Nivel: {user['level']} | Días/semana: {user['days']} | Edad: {user['age']} | Peso: {user['weight']} kg | Estatura: {user['height']} cm"
  routine_context='Sin rutina activa.'
  if routine:
   rd=db.routine_days(routine['id']);ri=db.items(routine['id'])
   done=sum(1 for x in rd if x['status']=='completed')
   exlines='; '.join(f"{x['day']}: {x['name']} ({x['sets']}x{x['reps']}, descanso {x['rest']}s)" for x in ri[:30])
   routine_context=f"Rutina activa: {routine['name']} | Semana {routine['week_number']} | Objetivo: {routine['goal']} | Progreso: {done}/{len(rd)} días | Ejercicios: {exlines}"
  system="""Eres GYM BOT AI, el entrenador digital de una aplicación de entrenamiento. Responde SIEMPRE en español claro, profesional, práctico y motivador. Usa el perfil y la rutina del usuario cuando sean relevantes. Puedes explicar técnica, músculos, selección de ejercicios, series, repeticiones, descanso, RPE/RIR, progresión, calentamiento y cómo usar la rutina. No inventes que un ejercicio está en la rutina si no aparece en el contexto. No diagnostiques enfermedades ni lesiones y no sustituyas a un médico/fisioterapeuta; ante dolor fuerte, lesión, mareo u otros síntomas preocupantes recomienda parar y buscar atención profesional. Para preguntas administrativas, si el rol es ADMIN, ayuda a interpretar seguimiento, cumplimiento, rutinas e historial, pero no expongas contraseñas ni secretos. Sé conciso pero útil, usando listas cuando mejoren la lectura. Si el usuario pide una rutina nueva, explica que debe usar el generador para crearla y guardarla en el historial."""
  prompt=f"PERFIL: {profile}\nRUTINA: {routine_context}\nPREGUNTA ACTUAL: {d.get('message','')}"
  history=d.get('history') or []
  # Keep only safe text turns and cap size.
  turns=[]
  for h in history[-10:]:
   if isinstance(h,dict) and h.get('role') in ('user','assistant') and isinstance(h.get('content'),str):
    turns.append({'role':h['role'],'content':h['content'][:1200]})
  try:
   client=OpenAI(api_key=key)
   response=client.responses.create(model=model,instructions=system,input=turns+[{'role':'user','content':prompt}])
   text=(getattr(response,'output_text',None) or '').strip()
   if text:return text
  except Exception as e:
   name=type(e).__name__
   code=getattr(e,'status_code',None)
   text=str(e).lower()
   if code==429 or 'insufficient_quota' in text or 'credit_balance_exhausted' in text:
    raise RuntimeError('La IA está configurada, pero la cuenta de API no tiene créditos disponibles. GYM BOT seguirá usando su base local hasta que se habilite saldo.')
   if code in (401,403) or 'authentication' in text or 'invalid_api_key' in text:
    raise RuntimeError('La clave de OpenAI no fue aceptada. Revisa OPENAI_API_KEY en esta ventana de PowerShell.')
   if code in (500,502,503,504):
    raise RuntimeError('El servicio de IA está temporalmente no disponible. Inténtalo nuevamente en unos segundos.')
   raise RuntimeError(f'La IA no pudo responder ({name}). Revisa la configuración de OpenAI.')
  return None
 def chat_answer(self,d):
  import unicodedata
  msg=(d.get("message") or "").strip()
  norm="".join(c for c in unicodedata.normalize("NFD",msg.lower()) if unicodedata.category(c)!="Mn")
  if not norm:
   return "Claro. ¿Qué ejercicio o tema de entrenamiento quieres consultar?"
  exs=[dict(x) for x in db.exercises()]
  matches=[]
  for e in exs:
   en="".join(c for c in unicodedata.normalize("NFD",e["name"].lower()) if unicodedata.category(c)!="Mn")
   if en in norm or any(len(part)>=4 and part in norm for part in en.split()):
    matches.append(e)
  muscles={
   "pecho":["pecho"],"espalda":["espalda"],"piernas":["piernas","pierna","cuadriceps","femoral"],
   "gluteos":["gluteos","gluteo"],"hombros":["hombros","hombro","deltoides"],
   "biceps":["biceps"],"triceps":["triceps"],"core":["core","abdomen","abdominales"],
   "pantorrilla":["pantorrilla","gemelos"]
  }
  muscle=None
  for k,aliases in muscles.items():
   if any(a in norm for a in aliases):
    muscle=k
    break
  if muscle and not matches:
   pool=[e for e in exs if muscle in "".join(c for c in unicodedata.normalize("NFD",e["muscle"].lower()) if unicodedata.category(c)!="Mn")]
   if pool:
    return f"🏋️ Ejercicios recomendados para {muscle.capitalize()}:\n\n" + "\n".join(f"• {e['name']} — {e['sets']} series × {e['reps']} reps · descanso {e['rest']} s" for e in pool[:6]) + "\n\nPuedes preguntarme por cualquiera para explicarte su ejecución."
  if matches:
   e=matches[0]
   return (f"🏋️ {e['name']}\n\n"
           f"Músculo principal: {e['muscle']}\n"
           f"Equipo: {e['equipment']}\n"
           f"Nivel: {e['level']}\n"
           f"Trabajo orientativo: {e['sets']} series × {e['reps']} repeticiones\n"
           f"Descanso: {e['rest']} segundos\n\n"
           f"Técnica: {e['description']}\n\n"
           "Si quieres, puedo darte una alternativa para el mismo músculo.")
  if any(x in norm for x in ["rpe","esfuerzo","intensidad"]):
   return "📊 RPE es una escala de esfuerzo de 1 a 10. Como guía, RPE 7 suele dejar unas 3 repeticiones en reserva y RPE 8 unas 2. Prioriza siempre una técnica segura."
  if "rir" in norm or "repeticiones en reserva" in norm:
   return "🎯 RIR indica cuántas repeticiones adicionales podrías hacer con buena técnica. RIR 2 significa que terminarías la serie sintiendo que podrías hacer unas 2 repeticiones más."
  if any(x in norm for x in ["descanso","descansar","pausa entre series"]):
   return "⏱️ Como orientación inicial, usa 60–90 segundos en muchos ejercicios accesorios y 90–120 segundos en movimientos más exigentes. Ajusta según rendimiento y recuperación."
  if any(x in norm for x in ["rutina","entrenamiento","programa"]) and muscle:
   pool=[e for e in exs if muscle in "".join(c for c in unicodedata.normalize("NFD",e["muscle"].lower()) if unicodedata.category(c)!="Mn")][:5]
   if pool:
    return f"🔥 Para una sesión de {muscle.capitalize()}, puedes combinar:\n\n" + "\n".join(f"• {e['name']} · {e['sets']} × {e['reps']}" for e in pool) + "\n\nPara una rutina completa y personalizada usa ✨ Generar mi rutina."
  if any(norm.startswith(x) for x in ["hola","buenas","buenos dias","buenas tardes","buenas noches","hey","saludos"]):
   return "👋 ¡Hola! Soy GYM BOT. Puedo ayudarte con entrenamiento, ejercicios, técnica, series, repeticiones, descanso, RPE, RIR y tu rutina. Cuando la IA externa esté disponible también puedo conversar sobre temas generales."
  if "presidente de colombia" in norm:
   return "🇨🇴 Puedo darte información sobre actualidad política cuando la IA externa esté disponible. En este momento la conexión de IA está sin créditos, así que no quiero inventarte una respuesta."
  if "inteligencia artificial" in norm or "que es ia" in norm:
   return "🤖 La inteligencia artificial es tecnología que permite a los sistemas aprender patrones, procesar información y generar respuestas o predicciones. En GYM BOT la usamos para conversar, explicar ejercicios y personalizar planes cuando la API está disponible."
  return ("🤖 Estoy listo para ayudarte. La IA externa está temporalmente sin saldo, pero la base local de GYM BOT sigue disponible para entrenamiento. Prueba preguntas como:\n\n"
          "• ¿Cómo hago press banca?\n"
          "• Dame ejercicios para bíceps\n"
          "• ¿Qué ejercicios trabajan espalda?\n"
          "• ¿Cuántas series hago de tríceps?\n"
          "• ¿Qué es RPE?\n"
          "• ¿Cuánto descanso entre series?\n\n"
          "También puedes usar ✨ Generar mi rutina para crear un programa personalizado.")

 def do_POST(self):
  try:
   p=urlparse(self.path).path;d=self.body()
   if p=='/webhooks/wompi':
    raw_event=d
    checksum=self.headers.get('X-Event-Checksum','')
    if not verify_event(raw_event,checksum):return send(self,401,{'error':'Firma de evento Wompi inválida'})
    if raw_event.get('event')!='transaction.updated':return send(self,200,{'ok':True,'ignored':True})
    tx=(raw_event.get('data') or {}).get('transaction') or {}
    reference=str(tx.get('reference') or '')
    payment=db.c.execute('SELECT * FROM payments WHERE reference=?',(reference,)).fetchone()
    if not payment:return send(self,200,{'ok':True,'ignored':True})
    # Comprobación cruzada: referencia, moneda y monto deben coincidir con la orden local.
    if str(tx.get('currency',''))!='COP' or int(tx.get('amount_in_cents') or tx.get('amountInCents') or 0)!=int(payment['amount_cop'])*100:
     return send(self,400,{'error':'Los datos del pago no coinciden con la orden'})
    status=str(tx.get('status') or '').upper()
    with PAYMENT_LOCK:
     payment=db.c.execute('SELECT * FROM payments WHERE reference=?',(reference,)).fetchone()
     if not payment:return send(self,200,{'ok':True,'ignored':True})
     db.c.execute('UPDATE payments SET status=?,wompi_transaction_id=?,updated=? WHERE reference=?',(status,str(tx.get('id') or ''),datetime.now().isoformat(),reference))
     if status=='APPROVED' and not payment['processed_at']:
      db.activate_membership(int(payment['user_id']),'Mensual',int(os.getenv('GYMBOT_MEMBERSHIP_DAYS','30')))
      db.c.execute("UPDATE memberships SET payment_status='paid_wompi' WHERE user_id=? AND id=(SELECT MAX(id) FROM memberships WHERE user_id=?)",(int(payment['user_id']),int(payment['user_id'])))
      db.c.execute('UPDATE payments SET processed_at=? WHERE reference=?',(datetime.now().isoformat(),reference))
     db.c.commit()
    return send(self,200,{'ok':True})
   if p=='/api/payments/checkout':
    token=self.headers.get('Authorization','')
    token=token[7:] if token.startswith('Bearer ') else ''
    session=verify_payment_token(token)
    if not session:return send(self,401,{'error':'Sesión de pago inválida o vencida. Inicia sesión nuevamente.'})
    uid=int(session['uid'])
    user=db.user(uid)
    if not user or user['role']!='USUARIO':return send(self,403,{'error':'Solo los clientes pueden pagar su membresía.'})
    if not wompi_configured():return send(self,503,{'error':'Wompi no está configurado todavía. Completa las variables del archivo .env.'})
    amount=int(os.getenv('GYMBOT_MEMBERSHIP_PRICE_COP','0'))
    if amount<1000: return send(self,503,{'error':'Configura un precio de membresía válido (mínimo $1.000 COP).'})
    reference='GYMBOT-'+secrets.token_hex(12).upper()
    checkout=create_checkout(reference,amount,user['email'] or '',user['name'] or '')
    db.c.execute('INSERT INTO payments(user_id,reference,amount_cop,currency,status,created) VALUES(?,?,?,?,?,?)',(uid,reference,amount,'COP','PENDING',datetime.now().isoformat()))
    db.c.commit()
    return send(self,201,{'ok':True,'reference':reference,'amount_cop':amount,'checkout_url':checkout['checkout_url']})
   if p=='/api/register':
    name=(d.get('name') or '').strip();username=(d.get('username') or '').strip().lower();password=d.get('password') or ''
    email=(d.get('email') or '').strip().lower();phone=(d.get('phone') or '').strip()
    if len(name)<3:raise ValueError('Escribe tu nombre completo.')
    if len(username)<4 or not re.fullmatch(r'[a-z0-9_.-]+',username):raise ValueError('El usuario debe tener 4 caracteres o más y usar letras, números, punto, guion o guion bajo.')
    if len(password)<8:raise ValueError('La contraseña debe tener al menos 8 caracteres.')
    age=int(d.get('age') or 0);height=float(d.get('height') or 0);weight=float(d.get('weight') or 0);days=int(d.get('days') or 3)
    if not 14<=age<=100:raise ValueError('La edad debe estar entre 14 y 100 años.')
    if not 100<=height<=230:raise ValueError('La estatura debe estar entre 100 y 230 cm.')
    if not 30<=weight<=300:raise ValueError('El peso debe estar entre 30 y 300 kg.')
    if not 2<=days<=6:raise ValueError('Selecciona entre 2 y 6 días de entrenamiento.')
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):raise ValueError('El correo no tiene un formato válido.')
    if not d.get('accept_terms'):raise ValueError('Debes aceptar los términos para continuar.')
    uid=db.add_user(name,username,password,'USUARIO',age,height,weight,d.get('goal','Hipertrofia'),d.get('level','Principiante'),days)
    db.c.execute('UPDATE users SET email=?,phone=? WHERE id=?',(email,phone,uid));db.c.execute('INSERT INTO memberships(user_id,plan,status,payment_status,created) VALUES(?,?,?,?,?)',(uid,'Por definir','pending_payment','pending',datetime.now().isoformat()));db.c.commit()
    return send(self,201,{'ok':True,'message':'Cuenta creada. Tu membresía queda pendiente de activación por el gimnasio.','user_id':uid,'membership_status':'pending_payment'})
   if p=='/api/login':
    u=db.auth(d.get('username',''),d.get('password',''))
    if not u:return send(self,401,{'error':'Usuario o contraseña incorrectos'})
    return send(self,200,{'user':dict(u),'payment_token':issue_payment_token(u['id'],u['role'])})
   if p=='/api/chat':
    try:
     ai=self.ai_chat_answer(d)
    except Exception as e:
     return send(self,502,{'error':str(e)})
    return send(self,200,{'answer':ai or self.chat_answer(d),'ai':bool(ai)})
   if p=='/api/generate_routine':return send(self,200,self.generate_routine(d))
   if p=='/api/complete_day':
    completed=db.complete_day(int(d['uid']),int(d['routine_id']),d['day']);return send(self,200,{'ok':True,'completed':completed})
   if p=='/api/log':
    if not 1<=float(d['rpe'])<=10:raise ValueError('RPE debe estar entre 1 y 10')
    db.log(int(d['uid']),int(d['eid']),float(d['w']),int(d['reps']),int(d['sets']),float(d['rpe']),d.get('notes',''));return send(self,200,{'ok':True})
   if p=='/api/users':
    i=db.add_user(d['name'],d['username'],d['password'],'USUARIO',int(d['age']),float(d['height']),float(d['weight']),d['goal'],d['level'],int(d['days']));db.c.execute('INSERT INTO memberships(user_id,plan,status,payment_status,created) VALUES(?,?,?,?,?)',(i,'Por definir','pending_payment','pending',datetime.now().isoformat()));db.c.commit();return send(self,200,{'id':i})
   if p=='/api/membership/activate':
    m=db.activate_membership(int(d['uid']),d.get('plan','Mensual'),int(d.get('days',30)))
    return send(self,200,{'ok':True,'membership':m})
   if p=='/api/profile':
    uid=int(d.get('uid') or 0);u=db.user(uid)
    if not u:raise ValueError('Usuario no encontrado')
    fields=[];values=[]
    for key,col,cast in [('age','age',int),('height','height',float),('weight','weight',float),('goal','goal',str),('level','level',str),('days','days',int),('avatar','avatar',str)]:
     if key in d:
      value=d[key]
      if key=='avatar' and len(value)>900000:raise ValueError('La imagen supera el tamaño permitido.')
      fields.append(f'{col}=?');values.append(cast(value) if value not in (None,'') else None)
    if fields:
     values.append(uid);db.c.execute('UPDATE users SET '+','.join(fields)+' WHERE id=?',values);db.c.commit()
    return send(self,200,{'ok':True,'user':dict(db.user(uid))})
   if p=='/api/assign':
    pr=d['program'];db.save_routine(int(d['uid']),pr,pr.split('·')[0].strip(),PROGRAMS[pr]);return send(self,200,{'ok':True})
   return send(self,404,{'error':'Ruta no encontrada'})
  except sqlite3.IntegrityError:return send(self,400,{'error':'El usuario ya existe'})
  except Exception as e:return send(self,400,{'error':str(e)})
 def do_DELETE(self):
  try:
   q=parse_qs(urlparse(self.path).query)
   if urlparse(self.path).path=='/api/users':db.delete_user(int(q['id'][0]));return send(self,200,{'ok':True})
   return send(self,404,{'error':'Ruta no encontrada'})
  except Exception as e:return send(self,400,{'error':str(e)})
 def log_message(self,*a):pass
if __name__=='__main__':
 print('\n'+'='*62)
 print('  GYM BOT V16 · WOMPI READY')
 print('='*62)
 print(f'  PC      : http://127.0.0.1:{PORT}')
 print(f'  CELULAR : {MOBILE_URL}')
 print(f'  CONEXIÓN: {MOBILE_URL}/connect')
 print('  QR      : disponible desde la aplicación')
 print('='*62+'\n')
 ThreadingHTTPServer.allow_reuse_address=True
 server=ThreadingHTTPServer(('0.0.0.0',PORT),H);server.daemon_threads=True;server.serve_forever()