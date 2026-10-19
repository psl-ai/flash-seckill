import hashlib, uuid
from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.db import Base, engine, get_db
from app.models import User, Activity, Registration, InventoryTransaction, now
from app.schemas import AuthIn, RefreshIn, TokenOut, ActivityIn, ActivityPatch, InventoryPatch, ActivityOut, ProfilePatch
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.services.activity import transition_status, ActivityStatus
from app.services.inventory import InventoryService
from app.tasks.registration_tasks import persist_registration
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

Base.metadata.create_all(engine)
app=FastAPI(title='秒抢 API', version='1.0.0'); bearer=HTTPBearer(auto_error=False); inv=InventoryService()
USER_REGISTRATION_LIMIT = 1
REQ=Counter('http_requests_total','HTTP requests',['method','path','status']); DUR=Histogram('http_request_duration_seconds','Request duration',['path']); REG_OK=Counter('registration_success_total','Successful registrations'); REG_FAIL=Counter('registration_failure_total','Failed registrations')
@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    import time
    start=time.perf_counter(); rid=str(uuid.uuid4()); response=await call_next(request); response.headers['X-Request-ID']=rid; REQ.labels(request.method,request.url.path,str(response.status_code)).inc(); DUR.labels(request.url.path).observe(time.perf_counter()-start); return response
def envelope(data=None, code='SUCCESS', message='success'): return {'code':code,'message':message,'request_id':str(uuid.uuid4()),'data':data}
def current_user(creds: HTTPAuthorizationCredentials=Depends(bearer), db: Session=Depends(get_db)):
    if not creds: raise HTTPException(401, detail=envelope(None,'UNAUTHORIZED','登录凭证无效'))
    try: payload=decode_token(creds.credentials); user=db.get(User,int(payload['sub']))
    except Exception: user=None
    if not user or not user.is_active: raise HTTPException(401, detail=envelope(None,'UNAUTHORIZED','登录凭证无效'))
    return user
def admin(user=Depends(current_user)):
    if user.role!='admin': raise HTTPException(403, detail=envelope(None,'FORBIDDEN','需要管理员权限'))
    return user
@app.exception_handler(HTTPException)
async def http_error(_, exc):
    from fastapi.responses import JSONResponse
    detail=exc.detail if isinstance(exc.detail,dict) else envelope(None,'ERROR',str(exc.detail)); return JSONResponse(content=detail, status_code=exc.status_code)
@app.post('/api/v1/auth/register', response_model=dict)
def register(body: AuthIn, db: Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==body.email)): raise HTTPException(409, detail=envelope(None,'EMAIL_EXISTS','邮箱已注册'))
    u=User(email=body.email,password_hash=hash_password(body.password),display_name=body.display_name or body.email.split('@')[0]); db.add(u); db.commit(); db.refresh(u); return envelope({'id':u.id,'email':u.email})
@app.post('/api/v1/auth/login', response_model=dict)
def login(body: AuthIn, db: Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==body.email))
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401, detail=envelope(None,'INVALID_CREDENTIALS','邮箱或密码错误'))
    return envelope(TokenOut(access_token=create_access_token({'sub':str(u.id),'role':u.role}),refresh_token=create_access_token({'sub':str(u.id),'type':'refresh'},10080)).model_dump())
@app.post('/api/v1/auth/refresh', response_model=dict)
def refresh(body: RefreshIn):
    try: p=decode_token(body.refresh_token)
    except Exception: raise HTTPException(401,detail=envelope(None,'UNAUTHORIZED','刷新令牌无效'))
    if p.get('type') != 'refresh': raise HTTPException(401,detail=envelope(None,'UNAUTHORIZED','刷新令牌无效'))
    return envelope(TokenOut(access_token=create_access_token({'sub':p['sub'],'role':p.get('role','user')}),refresh_token=body.refresh_token).model_dump())
@app.get('/api/v1/profile', response_model=dict)
def profile(user=Depends(current_user)): return envelope({'id':user.id,'email':user.email,'display_name':user.display_name,'role':user.role})

@app.patch('/api/v1/profile', response_model=dict)
def update_profile(body: ProfilePatch, user=Depends(current_user), db: Session = Depends(get_db)):
    user.display_name = body.display_name.strip()
    if not user.display_name: raise HTTPException(422, detail=envelope(None, 'INVALID_PROFILE', '昵称不能为空'))
    db.commit(); db.refresh(user)
    return envelope({'id': user.id, 'email': user.email, 'display_name': user.display_name, 'role': user.role})
@app.get('/health/live')
def live(): return {'status':'ok'}
@app.get('/health/ready')
def ready(): return {'status':'ok'}
@app.get('/metrics')
def metrics(): return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)

@app.get('/api/v1/activities', response_model=dict)
def list_activities(keyword: str | None = None, db: Session = Depends(get_db)):
    q = select(Activity).where(Activity.status.in_([ActivityStatus.PUBLISHED.value, ActivityStatus.REGISTRATION_OPEN.value]))
    if keyword: q = q.where(or_(Activity.name.ilike(f'%{keyword}%'), Activity.description.ilike(f'%{keyword}%')))
    items = db.scalars(q.order_by(Activity.created_at.desc())).all()
    return envelope([activity_dict(a) for a in items])

def activity_dict(a: Activity):
    return {'id': a.id, 'name': a.name, 'slug': a.slug, 'description': a.description, 'cover_url': a.cover_url,
            'status': a.status, 'start_at': a.start_at, 'end_at': a.end_at,
            'registration_start_at': a.registration_start_at, 'registration_end_at': a.registration_end_at,
            'total_stock': a.total_stock, 'available_stock': a.available_stock,
            'reserved_stock': a.reserved_stock, 'sold_stock': a.sold_stock,
            'max_registrations_per_user': a.max_registrations_per_user}

@app.get('/api/v1/activities/{activity_id}', response_model=dict)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    a = db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None, 'NOT_FOUND', '活动不存在'))
    return envelope(activity_dict(a))

@app.post('/api/v1/admin/activities', response_model=dict)
def create_activity(body: ActivityIn, user=Depends(admin), db: Session = Depends(get_db)):
    data = body.model_dump(); data['slug'] = data.get('slug') or hashlib.md5(data['name'].encode()).hexdigest()[:12]; data['created_by'] = user.id
    data['status'] = ActivityStatus.DRAFT.value; data['available_stock'] = data.get('total_stock', 0)
    a = Activity(**data); db.add(a); db.commit(); db.refresh(a); inv.seed(str(a.id), a.total_stock)
    return envelope(activity_dict(a))

@app.patch('/api/v1/admin/activities/{activity_id}', response_model=dict)
def patch_activity(activity_id: int, body: ActivityPatch, user=Depends(admin), db: Session = Depends(get_db)):
    a = db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None, 'NOT_FOUND', '活动不存在'))
    for k, v in body.model_dump(exclude_unset=True).items(): setattr(a, k, v)
    db.commit(); db.refresh(a); return envelope(activity_dict(a))

@app.post('/api/v1/admin/activities/{activity_id}/{action}', response_model=dict)
def activity_action(activity_id: int, action: str, user=Depends(admin), db: Session = Depends(get_db)):
    a = db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None, 'NOT_FOUND', '活动不存在'))
    try: a.status = transition_status(ActivityStatus(a.status), action).value
    except ValueError as e: raise HTTPException(409, detail=envelope(None, 'INVALID_STATE', str(e)))
    db.commit(); return envelope(activity_dict(a))

@app.post('/api/v1/activities/{activity_id}/registrations', response_model=dict)
def register_activity(activity_id: int, request: Request, user=Depends(current_user), db: Session=Depends(get_db), idempotency_key: str | None = Header(default=None, alias='Idempotency-Key')):
    a = db.get(Activity, activity_id)
    if not a or a.status not in (ActivityStatus.PUBLISHED.value, ActivityStatus.REGISTRATION_OPEN.value): raise HTTPException(409, detail=envelope(None,'ACTIVITY_NOT_OPEN','活动未开放报名'))
    existing_count = len(db.scalars(select(Registration).where(Registration.activity_id == activity_id, Registration.user_id == user.id)).all())
    if existing_count >= min(USER_REGISTRATION_LIMIT, a.max_registrations_per_user):
        raise HTTPException(409, detail=envelope(None, 'REGISTRATION_LIMIT_REACHED', '已达到该活动的报名上限'))
    key = idempotency_key or str(uuid.uuid4()); result = inv.reserve(str(activity_id), str(user.id), key)
    if result.code != 'SUCCESS':
        REG_FAIL.inc(); status = 409 if result.code != 'SOLD_OUT' else 409
        raise HTTPException(status, detail=envelope(None, result.code, {'SOLD_OUT':'活动名额已用完','ALREADY_REGISTERED':'不可重复报名'}.get(result.code, result.code)))
    reg = Registration(activity_id=activity_id, user_id=user.id, reservation_id=result.reservation_id, idempotency_key=key, status='queued')
    db.add(reg); a.available_stock = max(0, a.available_stock - 1); a.reserved_stock += 1
    db.add(InventoryTransaction(activity_id=activity_id, change_type='reserve', change_quantity=-1, before_available=a.available_stock+1, after_available=a.available_stock, reference_id=result.reservation_id, reason='registration'))
    db.commit(); db.refresh(reg); REG_OK.inc()
    try:
        persist_registration.delay(reg.id)
    except Exception:
        pass
    return envelope({'registration_id': reg.id, 'reservation_id': reg.reservation_id, 'status': reg.status})

@app.get('/api/v1/registrations', response_model=dict)
def my_registrations(user=Depends(current_user), db: Session=Depends(get_db)):
    return envelope([{'id': r.id, 'activity_id': r.activity_id, 'reservation_id': r.reservation_id, 'status': r.status} for r in db.scalars(select(Registration).where(Registration.user_id==user.id).order_by(Registration.created_at.desc())).all()])

@app.get('/api/v1/registrations/{registration_id}', response_model=dict)
def registration_detail(registration_id: int, user=Depends(current_user), db: Session=Depends(get_db)):
    r = db.get(Registration, registration_id)
    if not r or r.user_id != user.id: raise HTTPException(404, detail=envelope(None,'NOT_FOUND','报名记录不存在'))
    return envelope({'id':r.id,'activity_id':r.activity_id,'reservation_id':r.reservation_id,'status':r.status})

@app.post('/api/v1/registrations/{registration_id}/cancel', response_model=dict)
def cancel_registration(registration_id: int, user=Depends(current_user), db: Session=Depends(get_db)):
    r = db.get(Registration, registration_id)
    if not r or r.user_id != user.id: raise HTTPException(404, detail=envelope(None,'NOT_FOUND','报名记录不存在'))
    if r.status in ('canceled','expired'): return envelope({'id':r.id,'status':r.status})
    a = db.get(Activity, r.activity_id); result = inv.release(str(r.activity_id), r.reservation_id)
    if result.code == 'SUCCESS' and a: a.available_stock += 1; a.reserved_stock = max(0, a.reserved_stock-1)
    r.status='canceled'; r.canceled_at=now(); db.commit(); return envelope({'id':r.id,'status':r.status})

@app.get('/api/v1/admin/activities/{activity_id}/inventory', response_model=dict)
def inventory(activity_id: int, user=Depends(admin), db: Session=Depends(get_db)):
    a=db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None,'NOT_FOUND','活动不存在'))
    return envelope({'total_stock':a.total_stock,'available_stock':a.available_stock,'reserved_stock':a.reserved_stock,'sold_stock':a.sold_stock})

@app.patch('/api/v1/admin/activities/{activity_id}/inventory', response_model=dict)
def inventory_patch(activity_id: int, body: InventoryPatch, user=Depends(admin), db: Session=Depends(get_db)):
    a=db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None,'NOT_FOUND','活动不存在'))
    before=a.available_stock; a.total_stock += body.quantity; a.available_stock += body.quantity
    if a.available_stock < 0: raise HTTPException(409, detail=envelope(None,'INVENTORY_INSUFFICIENT','库存不足'))
    db.add(InventoryTransaction(activity_id=activity_id, change_type='admin_adjust', change_quantity=body.quantity, before_available=before, after_available=a.available_stock, reason=body.reason or 'admin'))
    db.commit(); inv.seed(str(activity_id), a.available_stock); return envelope(activity_dict(a))

@app.get('/api/v1/admin/activities/{activity_id}/statistics', response_model=dict)
def activity_statistics(activity_id: int, user=Depends(admin), db: Session = Depends(get_db)):
    a = db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None, 'NOT_FOUND', '活动不存在'))
    registrations = db.scalars(select(Registration).where(Registration.activity_id == activity_id)).all()
    return envelope({'activity_id': activity_id, 'registration_count': len(registrations), 'available_stock': a.available_stock, 'reserved_stock': a.reserved_stock, 'sold_stock': a.sold_stock})

@app.get('/api/v1/admin/activities/{activity_id}/inventory/transactions', response_model=dict)
def inventory_transactions(activity_id: int, user=Depends(admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(InventoryTransaction).where(InventoryTransaction.activity_id == activity_id).order_by(InventoryTransaction.created_at.desc())).all()
    return envelope([{'id': row.id, 'change_type': row.change_type, 'change_quantity': row.change_quantity, 'before_available': row.before_available, 'after_available': row.after_available, 'reason': row.reason} for row in rows])

@app.post('/api/v1/admin/activities/{activity_id}/inventory/reconcile', response_model=dict)
def reconcile_inventory(activity_id: int, user=Depends(admin), db: Session = Depends(get_db)):
    a = db.get(Activity, activity_id)
    if not a: raise HTTPException(404, detail=envelope(None, 'NOT_FOUND', '活动不存在'))
    inv.seed(str(activity_id), a.available_stock)
    return envelope({'activity_id': activity_id, 'redis_available_stock': inv.available(str(activity_id)), 'database_available_stock': a.available_stock, 'reconciled': True})
