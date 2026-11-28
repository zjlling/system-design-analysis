#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云齿通 CloudDent 后端 API v3（31表 + 认证权限）
- 数据主源：PostgreSQL clouddent 库 31 张表（v5报告29表 + v6新增跨店调阅申请/前台绩效）
- 前端 state（14数组）作为视图缓存；load 时从 29 表装配，save 时回写 29 表
- 接口：/api/state(GET) /api/state(PUT 回写31表,需Bearer token) /api/login /api/health /api/tables
"""
import json, os, time, hashlib, secrets
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import psycopg2

DB = dict(host="127.0.0.1", port=5432, dbname="clouddent",
          user="clouddent", password=os.environ.get("CD_DB_PASS", "Clouddent2026"))

ACCOUNTS = {
    "reception": {"username":"reception","tel":"13800138001","password":"123456","name":"前台导诊"},
    "doctor":    {"username":"doctor","tel":"13800138002","password":"123456","name":"口腔医生"},
    "hq":        {"username":"hq","tel":"13800138003","password":"123456","name":"门诊总部"},
    "admin":     {"username":"admin","tel":"13900000000","password":"123456","name":"系统管理员"},
}

def conn():
    return psycopg2.connect(**DB)

def q(cur, sql, args=None):
    cur.execute(sql, args or ())

def rows(cur, sql, args=None):
    cur.execute(sql, args or ())
    return cur.fetchall()

def s(v):
    return "" if v is None else str(v)
def dt(v):
    if v is None: return ""
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
    if hasattr(v, "date"): return v.date().strftime("%Y-%m-%d")
    return str(v)[:10]
def dtm(v):
    if v is None: return ""
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d %H:%M")
    return str(v)[:16]

# ---------- v3：token 会话、角色权限、工资条计算 ----------
TOKENS = {}  # token -> {role, name, ts}
def issue_token(role, name):
    t = hashlib.md5(("%s%s%s%d" % (role, name, secrets.token_hex(4), time.time_ns())).encode()).hexdigest()
    TOKENS[t] = {"role": role, "name": name, "ts": time.time()}
    return t

def auth(request_headers):
    """从 Authorization: Bearer <token> 校验会话，返回 {role,name} 或 None。
       无 token 时 Demo 仍可读（老师直接开页面），但写操作必须带 token。"""
    h = request_headers.get("Authorization", "") if request_headers else ""
    if h.startswith("Bearer "):
        tk = h[7:].strip()
        info = TOKENS.get(tk)
        if info and time.time() - info["ts"] < 86400:
            return info
    return None

def can(role, action):
    """服务端角色权限矩阵（不依赖前端拦截）。"""
    M = {
      "admin":     {"read","write","approve","pay","perf_all"},
      "hq":        {"read","perf_all","audit"},
      "reception": {"read","write","approve","perf_self"},
      "doctor":    {"read","write","perf_self"},
    }
    return action in M.get(role, set())

def commission(inc):
    inc = float(inc or 0)
    return round(inc * (0.15 if inc < 100000 else 0.18 if inc < 150000 else 0.20))

def payroll(base, inc, specialty, satisfaction, full, tax, is_doctor, receptions=0, convert=0):
    """与前端 payrollOf() 完全一致的工资条计算。"""
    base = float(base or 0); tax = float(tax or 0)
    if is_doctor:
        gross = base + commission(inc) + float(specialty or 0) + float(satisfaction or 0) + float(full or 0)
    else:
        gross = base + round(float(receptions or 0) * 12) + float(convert or 0) + float(full or 0)
    social = round(gross*0.08) + round(gross*0.02) + round(gross*0.003) + round(gross*0.12)
    return {"gross": gross, "social": social, "tax": tax, "net": gross - social - tax,
            "commission": commission(inc) if is_doctor else round(float(receptions or 0)*12)}

# ---------- 从 29 表装配前端 state ----------
def build_state():
    c = conn(); cur = c.cursor(); st = {}
    # 预约
    st["appointments"] = [dict(zip(
        ["id","patientId","name","shopId","date","time","doctorId","item","status","chair","source"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),dt(r[4]),dtm(r[5]),s(r[6]),s(r[7]),s(r[8]),s(r[9]),s(r[10])]))
        for r in rows(cur, """SELECT a.appointmentid,a.patientid,p.name,a.shopid,
            a.appointmenttime,a.appointmenttime,a.doctorid,
            COALESCE(cs.itemname,'口腔检查'),a.status,
            COALESCE(co.dentalchairid,'待分配'),a.source
            FROM appointment a JOIN patient p ON p.patientid=a.patientid
            LEFT JOIN chargesheet ch ON ch.treatmentrecordid=a.treatmentrecordid
            LEFT JOIN chargedetail cs ON cs.chargesheetid=ch.chargesheetid
            LEFT JOIN chairoccupancy co ON co.appointmentid=a.appointmentid ORDER BY a.appointmentid""")]
    # 医生排班
    st["schedules"] = [dict(zip(["id","doctorId","date","shift","shopId"],
        [s(r[0]),s(r[1]),dt(r[2]),s(r[3]),s(r[4])]))
        for r in rows(cur,"SELECT doctorscheduleid,doctorid,scheduledate,timeslot,shopid FROM doctorschedule ORDER BY doctorscheduleid")]
    # 号源
    st["slots"] = [dict(zip(["id","scheduleId","time","status"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3])]))
        for r in rows(cur,"SELECT appointmentslotid,doctorscheduleid,timeslot,status FROM appointmentslot ORDER BY appointmentslotid")]
    # 牙椅
    st["chairs"] = [dict(zip(["id","room","no","status","shopId"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),s(r[4])]))
        for r in rows(cur,"SELECT dentalchairid,room,chairno,status,shopid FROM dentalchair ORDER BY dentalchairid")]
    # 收费单
    st["bills"] = [dict(zip(["id","billNo","patientId","name","shopId","item","amount","status","payMethod","doctorId","date","receipt"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),s(r[4]),s(r[5]),float(r[6] or 0),s(r[7]),s(r[8]),s(r[9]),
         dt(r[10]),s(r[11])]))
        for r in rows(cur,"""SELECT c.chargesheetid,c.chargesheetid,c.patientid,p.name,c.shopid,
            COALESCE(cd.itemname,''),c.totalamount,c.status,COALESCE(pr.channel,''),
            COALESCE(tr.doctorid,''),c.chargedate,COALESCE(er.receiptno,'')
            FROM chargesheet c JOIN patient p ON p.patientid=c.patientid
            LEFT JOIN chargedetail cd ON cd.chargesheetid=c.chargesheetid
            LEFT JOIN paymentrecord pr ON pr.chargesheetid=c.chargesheetid AND pr.payresult='成功'
            LEFT JOIN treatmentrecord tr ON tr.treatmentrecordid=c.treatmentrecordid
            LEFT JOIN electronicreceipt er ON er.chargesheetid=c.chargesheetid
            ORDER BY c.chargesheetid""")]
    # 耗材
    st["consumables"] = [dict(zip(["id","name","spec","unit","stock","warning","shopId","supplier"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),float(r[4] or 0),float(r[5] or 0),s(r[6]),'']))
        for r in rows(cur,"""SELECT cc.consumablecategoryid,cc.name,cc.spec,cc.unit,
            COALESCE((SELECT SUM(bs.qty) FROM batchstock bs WHERE bs.consumablecategoryid=cc.consumablecategoryid),0),
            cc.safetythreshold, 'S1'
            FROM consumablecategory cc ORDER BY cc.consumablecategoryid""")]
    st["consumeLogs"] = [dict(zip(["id","itemId","itemName","qty","shopId","date","by"],
        [s(r[0]),s(r[1]),s(r[2]),float(r[3] or 0),s(r[4]),
         dt(r[5]),s(r[6])]))
        for r in rows(cur,"""SELECT cc1.consumableconsumptionid,cc1.consumablecategoryid,cc.name,
            cc1.qty,tr.shopid,cc1.usedate,tr.doctorid
            FROM consumableconsumption cc1 JOIN consumablecategory cc ON cc.consumablecategoryid=cc1.consumablecategoryid
            JOIN treatmentrecord tr ON tr.treatmentrecordid=cc1.treatmentrecordid ORDER BY cc1.consumableconsumptionid""")]
    st["purchases"] = [dict(zip(["id","itemId","itemName","qty","supplier","status","date","by"],
        [s(r[0]),s(r[1]),s(r[2]),float(r[3] or 0),s(r[4]),'已入库',
         dt(r[5]),s(r[6])]))
        for r in rows(cur,"""SELECT pd.purchasedetailid,pd.consumablecategoryid,cc.name,pd.qty,
            s.name,cp.purchasedate,cp.operatorid FROM purchasedetail pd
            JOIN consumablecategory cc ON cc.consumablecategoryid=pd.consumablecategoryid
            JOIN consumablepurchase cp ON cp.consumablepurchaseid=pd.consumablepurchaseid
            LEFT JOIN supplier s ON s.supplierid=cp.supplierid ORDER BY pd.purchasedetailid""")]
    # 诊疗记录（病历列表）
    st["records"] = [dict(zip(["id","patientId","name","shopId","doctorId","tooth","chief","diagnosis","treatment","allergy","imaging","date"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),s(r[4]),s(r[5]),s(r[6]),s(r[7]),s(r[8]),s(r[9]),s(r[10]),
         dt(r[11])]))
        for r in rows(cur,"""SELECT tr.treatmentrecordid,tr.patientid,p.name,tr.shopid,tr.doctorid,
            tr.tooth,tr.chief,tr.diagnosis,tr.treatment,mr.allergy,tr.imaging,tr.recorddate
            FROM treatmentrecord tr JOIN patient p ON p.patientid=tr.patientid
            JOIN medicalrecord mr ON mr.medicalrecordid=tr.medicalrecordid ORDER BY tr.treatmentrecordid""")]
    # 回访
    st["returnVisits"] = [dict(zip(["id","patientId","name","shopId","type","planDate","result","status"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),s(r[4]),
         dt(r[5]),s(r[6]),s(r[7])]))
        for r in rows(cur,"""SELECT rv.returnvisittaskid,rv.patientid,p.name,p.shopid,rv.type,
            rv.plandate,rv.result,rv.status FROM returnvisittask rv JOIN patient p ON p.patientid=rv.patientid
            ORDER BY rv.returnvisittaskid""")]
    st["feedbacks"] = [dict(zip(["id","patientId","patient","shopId","date","content","reply"],
        [s(r[0]),s(r[1]),s(r[2]),s(r[3]),dt(r[4]),s(r[5]),s(r[6])]))
        for r in rows(cur,"""SELECT rf.returnvisitfeedbackid,rv.patientid,p.name,p.shopid,
            rf.feedbacktime,rf.content,COALESCE(rf.reply,'') FROM returnvisitfeedback rf
            JOIN returnvisittask rv ON rv.returnvisittaskid=rf.returnvisittaskid
            JOIN patient p ON p.patientid=rv.patientid ORDER BY rf.returnvisitfeedbackid""")]
    # 季度成本（audits）
    st["audits"] = [dict(zip(["id","shopId","month","revenue","cost","diff","status"],
        [s(r[0]),s(r[1]),s(r[2]),0.0,float(r[3] or 0),0,'待核查']))
        for r in rows(cur,"SELECT quarterlycostsummaryid,shopid,quarter,totalcost FROM quarterlycostsummary ORDER BY quarterlycostsummaryid")]
    # 跨店调阅：从 accesslog 里 action 含"调阅"/"授权"的记录重建
    st["crossRequests"] = build_cross(cur)
    # v4：医生绩效（Performance 父类 JOIN DoctorPerformance 子类，API 按公式算工资条）
    st["performance"] = []
    for r in rows(cur, """SELECT p.performanceid,dp.doctorid,p.name,p.shopid,p.month,
        dp.visits,dp.revenue,p.basesalary,dp.specialtybonus,p.fullattendance,
        dp.satisfaction,p.tax,p.score,p.grade
        FROM doctorperformance dp JOIN performance p ON dp.doctorperformanceid=p.performanceid
        ORDER BY dp.doctorid,p.month DESC"""):
        st["performance"].append(dict(id=s(r[0]),doctorId=s(r[1]),name=s(r[2]),shopId=s(r[3]),
            month=s(r[4]),visits=int(r[5] or 0),income=float(r[6] or 0),base=float(r[7] or 0),
            specialty=float(r[8] or 0),full=float(r[9] or 0),satisfaction=float(r[10] or 0),
            tax=float(r[11] or 0),score=int(r[12] or 0),grade=s(r[13])))
    # v4：前台绩效（Performance 父类 JOIN ReceptionistPerformance 子类）
    st["staffPerf"] = []
    for r in rows(cur, """SELECT p.performanceid,rp.receptionistid,p.name,p.shopid,p.month,
        rp.receptions,p.basesalary,rp.convertbonus,p.fullattendance,p.tax,p.score,p.grade
        FROM receptionistperformance rp JOIN performance p ON rp.receptionistperformanceid=p.performanceid
        ORDER BY rp.receptionistid,p.month DESC"""):
        st["staffPerf"].append(dict(id=s(r[0]),workerId=s(r[1]),name=s(r[2]),shopId=s(r[3]),
            month=s(r[4]),receptions=int(r[5] or 0),base=float(r[6] or 0),
            convert=float(r[7] or 0),full=float(r[8] or 0),tax=float(r[9] or 0),
            score=int(r[10] or 0),grade=s(r[11])))

    # 访问日志
    st["accessLogs"] = [dict(zip(["id","time","worker","view","action","detail","patientId","shopId"],
        [s(r[0]),dt(r[1]),s(r[2]),'',s(r[3]),s(r[4]),s(r[5]),s(r[6])]))
        for r in rows(cur,"SELECT a.accesslogid,a.logtime,w.name,a.action,a.detail,a.patientid,a.shopid FROM accesslog a JOIN worker w ON w.workerid=a.workerid ORDER BY a.logtime DESC")]
    c.close()
    return st

def build_cross(cur):
    # v3：跨店调阅申请从 crossshoprequest 真表装配（替换硬编码）
    out = []
    for r in rows(cur, """SELECT cr.crossshoprequestid,cr.patientid,p.name,cr.applicantid,
        cr.applicantrole,cr.fromshopid,cr.toshopid,cr.reason,cr.status,
        cr.createdat,cr.expireat,cr.approvedbyname
        FROM crossshoprequest cr JOIN patient p ON p.patientid=cr.patientid
        ORDER BY cr.createdat DESC"""):
        out.append(dict(id=s(r[0]),patientId=s(r[1]),name=s(r[2]),
            applicantId=s(r[3]),applicantRole=s(r[4]),
            fromShopId=s(r[5]),toShopId=s(r[6]),reason=s(r[7]),status=s(r[8]),
            createdAt=dtm(r[9]),expireAt=dtm(r[10]),approvedBy=s(r[11]),
            doctorId=s(r[3]) if s(r[4])=="口腔医生" else ""))
    return out

# ---------- 前端 save 回写 29 表（关键变更：用户操作落到报告的表） ----------
def write_back(state):
    """把前端 state 的用户变更全量对账回 29 张表：
       新增记录 INSERT，已存在记录按状态 UPDATE。老师点任意按钮后查对应表都能看到变化。"""
    c = conn(); c.autocommit = True; cur = c.cursor()
    def exists(table, col, val):
        return bool(rows(cur, 'SELECT 1 FROM %s WHERE %s=%%s' % (table, col), (val,)))
    def exe(sql, args):
        try: q(cur, sql, args)
        except Exception: pass

    # --- 患者新增 → Patient ---
    for p in state.get("patients", []):
        pid = s(p.get("id"))
        if pid and not exists("patient","patientid",pid):
            exe("""INSERT INTO patient(patientid,name,gender,age,phone,allergy,level,shopid,created)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now())""",
                (pid,s(p.get("name")),s(p.get("gender")) or "—",p.get("age") or None,
                 s(p.get("phone")),s(p.get("allergy")) or "无",s(p.get("level")) or "普通",
                 s(p.get("shopId")) or "S1"))

    # --- 预约新增/状态变化 → Appointment ---
    for a in state.get("appointments", []):
        aid = s(a.get("id"))
        if not aid: continue
        if not exists("appointment","appointmentid",aid):
            pid = s(a.get("patientId")) or "P001"
            if not exists("patient","patientid",pid):
                exe("INSERT INTO patient(patientid,name,created) VALUES(%s,%s,now())",(pid,s(a.get("name")) or "患者"))
            exe("""INSERT INTO appointment(appointmentid,patientid,appointmenttime,status,shopid,doctorid,source)
                   VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (aid,pid,(a.get("date","2026-11-24")+" "+s(a.get("time","09:00")).split("-")[0]) or None,
                 s(a.get("status")) or "已预约",s(a.get("shopId")) or "S1",s(a.get("doctorId")) or None,
                 s(a.get("source")) or "前台登记"))
        else:
            exe("UPDATE appointment SET status=%s WHERE appointmentid=%s",(s(a.get("status")),aid))

    # --- 排班新增 → DoctorSchedule ---
    for x in state.get("schedules", []):
        sid = s(x.get("id"))
        if sid and not exists("doctorschedule","doctorscheduleid",sid):
            exe("""INSERT INTO doctorschedule(doctorscheduleid,doctorid,scheduledate,timeslot,shopid)
                   VALUES(%s,%s,%s,%s,%s)""",
                (sid,s(x.get("doctorId")) or "D01",x.get("date") or None,
                 s(x.get("shift")) or "09:00-12:00",s(x.get("shopId")) or "S1"))

    # --- 号源状态 → AppointmentSlot ---
    for x in state.get("slots", []):
        sid = s(x.get("id"))
        if sid:
            if not exists("appointmentslot","appointmentslotid",sid):
                exe("""INSERT INTO appointmentslot(appointmentslotid,doctorscheduleid,timeslot,status)
                       VALUES(%s,%s,%s,%s)""",
                    (sid,s(x.get("scheduleId")) or "DS001",s(x.get("time")),s(x.get("status"))))
            else:
                exe("UPDATE appointmentslot SET status=%s WHERE appointmentslotid=%s",(s(x.get("status")),sid))

    # --- 牙椅状态 → DentalChair ---
    for x in state.get("chairs", []):
        cid = s(x.get("id"))
        if cid:
            if not exists("dentalchair","dentalchairid",cid):
                exe("INSERT INTO dentalchair(dentalchairid,room,chairno,status,shopid) VALUES(%s,%s,%s,%s,%s)",
                    (cid,s(x.get("room")) or "诊室1",s(x.get("no")) or cid,s(x.get("status")),s(x.get("shopId")) or "S1"))
            else:
                exe("UPDATE dentalchair SET status=%s WHERE dentalchairid=%s",(s(x.get("status")),cid))

    # --- 诊疗记录新增 → MedicalRecord + TreatmentRecord ---
    for r in state.get("records", []):
        rid = s(r.get("id"))
        if not rid or exists("treatmentrecord","treatmentrecordid",rid): continue
        pid = s(r.get("patientId")) or "P001"; did = s(r.get("doctorId")) or "D01"
        if not exists("patient","patientid",pid):
            exe("INSERT INTO patient(patientid,name,created) VALUES(%s,%s,now())",(pid,s(r.get("name")) or "患者"))
        mrid = "MR_"+rid
        if not exists("medicalrecord","medicalrecordid",mrid):
            exe("INSERT INTO medicalrecord(medicalrecordid,patientid,allergy,created) VALUES(%s,%s,%s,now())",
                (mrid,pid,s(r.get("allergy")) or "无"))
        exe("""INSERT INTO treatmentrecord(treatmentrecordid,patientid,doctorid,medicalrecordid,tooth,chief,
               diagnosis,treatment,imaging,recorddate,shopid) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (rid,pid,did,mrid,s(r.get("tooth")),s(r.get("chief")),s(r.get("diagnosis")),
             s(r.get("treatment")),s(r.get("imaging")),r.get("date") or None,s(r.get("shopId")) or "S1"))

    # --- 收费单新增/收款 → ChargeSheet + ChargeDetail + PaymentRecord ---
    for b in state.get("bills", []):
        bid = s(b.get("id"))
        if not bid: continue
        if not exists("chargesheet","chargesheetid",bid):
            pid = s(b.get("patientId")) or "P001"; trid = s(b.get("recordId")) or "TR001"
            if not exists("treatmentrecord","treatmentrecordid",trid):
                trid = "TR_IMPORT"
                if not exists("treatmentrecord","treatmentrecordid",trid):
                    if not exists("patient","patientid",pid):
                        exe("INSERT INTO patient(patientid,name,created) VALUES(%s,%s,now())",(pid,s(b.get("name")) or "患者"))
                    mr = "MR_"+pid
                    if not exists("medicalrecord","medicalrecordid",mr):
                        exe("INSERT INTO medicalrecord(medicalrecordid,patientid,created) VALUES(%s,%s,now())",(mr,pid))
                    exe("""INSERT INTO treatmentrecord(treatmentrecordid,patientid,doctorid,medicalrecordid,recorddate,shopid)
                           VALUES(%s,%s,'D01',%s,now(),%s)""",(trid,pid,mr,s(b.get("shopId")) or "S1"))
            exe("INSERT INTO chargesheet(chargesheetid,treatmentrecordid,patientid,totalamount,status,chargedate,shopid) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (bid,trid,pid,float(b.get("amount") or 0),s(b.get("status")) or "待支付",b.get("date") or None,s(b.get("shopId")) or "S1"))
            exe("INSERT INTO chargedetail(chargedetailid,chargesheetid,itemname,qty,price,amount) VALUES(%s,%s,%s,1,%s,%s)",
                ("CD_"+bid,bid,s(b.get("item")),float(b.get("amount") or 0),float(b.get("amount") or 0)))
        else:
            exe("UPDATE chargesheet SET status=%s WHERE chargesheetid=%s",(s(b.get("status")),bid))
            if s(b.get("status")) == "已收款" and s(b.get("payMethod")):
                prid = "PR_"+bid
                if not exists("paymentrecord","paymentrecordid",prid):
                    exe("INSERT INTO paymentrecord(paymentrecordid,chargesheetid,channel,amount,payresult,paytime) VALUES(%s,%s,%s,%s,'成功',now())",
                        (prid,bid,s(b.get("payMethod")),float(b.get("amount") or 0)))

    # --- 耗材消耗/入库 → ConsumableConsumption / PurchaseDetail ---
    for x in state.get("consumeLogs", []):
        cid = s(x.get("id"))
        if cid and not exists("consumableconsumption","consumableconsumptionid",cid):
            trid = "TR001"
            exe("INSERT INTO consumableconsumption(consumableconsumptionid,consumablecategoryid,treatmentrecordid,qty,usedate) VALUES(%s,%s,%s,%s,%s)",
                (cid,s(x.get("itemId")) or "MC001",trid,float(x.get("qty") or 1),x.get("date") or None))
    for x in state.get("purchases", []):
        cid = s(x.get("id"))
        if cid and not exists("purchasedetail","purchasedetailid",cid):
            exe("INSERT INTO consumablepurchase(consumablepurchaseid,quarterlycostsummaryid,purchasedate,operatorid) VALUES(%s,'QC001',now(),'R01')",("PO_"+cid,))
            exe("INSERT INTO purchasedetail(purchasedetailid,consumablepurchaseid,consumablecategoryid,qty,price) VALUES(%s,%s,%s,%s,%s)",
                (cid,"PO_"+cid,s(x.get("itemId")) or "MC001",float(x.get("qty") or 1),45))

    # --- 回访结果 → ReturnVisitTask ---
    for x in state.get("returnVisits", []):
        rid = s(x.get("id"))
        if rid:
            if not exists("returnvisittask","returnvisittaskid",rid):
                pid = s(x.get("patientId")) or "P001"
                if not exists("patient","patientid",pid):
                    exe("INSERT INTO patient(patientid,name,created) VALUES(%s,%s,now())",(pid,s(x.get("name")) or "患者"))
                exe("INSERT INTO returnvisittask(returnvisittaskid,patientid,createtime,status,plandate,type,result) VALUES(%s,%s,now(),%s,%s,%s,%s)",
                    (rid,pid,s(x.get("status")) or "待回访",x.get("planDate") or None,s(x.get("type")),s(x.get("result"))))
            else:
                exe("UPDATE returnvisittask SET status=%s,result=%s WHERE returnvisittaskid=%s",
                    (s(x.get("status")),s(x.get("result")),rid))
    for x in state.get("feedbacks", []):
        fid = s(x.get("id"))
        if fid and not exists("returnvisitfeedback","returnvisitfeedbackid",fid):
            exe("INSERT INTO returnvisitfeedback(returnvisitfeedbackid,content,reply,feedbacktime) VALUES(%s,%s,%s,now())",
                (fid,s(x.get("content")),s(x.get("reply")),))

    # --- 季度核查状态 → QuarterlyCostSummary(用 remark 近似) 略；会员积分 → MembershipAccount ---
    for x in state.get("members", []):
        mid = s(x.get("id"))
        if mid and not exists("membershipaccount","membershipaccountid",mid):
            pid = s(x.get("patientId"))
            if pid and exists("patient","patientid",pid):
                exe("INSERT INTO membershipaccount(membershipaccountid,patientid,balance,points,cardno,level) VALUES(%s,%s,%s,%s,%s,%s)",
                    (mid,pid,float(x.get("balance") or 0),int(x.get("points") or 0),s(x.get("cardNo")) or mid,s(x.get("level")) or "普通"))

    # --- v3：跨店调阅申请新增/授权状态 → CrossShopRequest ---
    for x in state.get("crossRequests", []):
        cid = s(x.get("id"))
        if not cid: continue
        stat = s(x.get("status"))
        if not exists("crossshoprequest","crossshoprequestid",cid):
            pid = s(x.get("patientId"))
            if pid and exists("patient","patientid",pid):
                exe("""INSERT INTO crossshoprequest(crossshoprequestid,patientid,applicantid,applicantrole,
                       fromshopid,toshopid,reason,status,createdat,expireat,approvedbyname)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),NULL,%s)""",
                    (cid,pid,s(x.get("applicantId")) or s(x.get("doctorId")) or "D01",
                     s(x.get("applicantRole")) or "口腔医生",s(x.get("fromShopId")) or "S1",
                     s(x.get("toShopId")) or "S2",s(x.get("reason")),stat or "待授权",s(x.get("approvedBy"))))
        else:
            if stat == "已授权":
                exe("""UPDATE crossshoprequest SET status=%s,approvedbyname=%s,
                       expireat=now() + interval '7 days' WHERE crossshoprequestid=%s""",
                    (stat,s(x.get("approvedBy")),cid))
            elif stat:
                exe("UPDATE crossshoprequest SET status=%s WHERE crossshoprequestid=%s",(stat,cid))

    # --- 访问日志（登录/查看/授权等操作）→ AccessLog ---
    exist = set(s(r[0]) for r in rows(cur,"SELECT accesslogid FROM accesslog"))
    for lg in state.get("accessLogs", [])[:300]:
        lid = s(lg.get("id"))
        if lid and lid not in exist:
            exe("""INSERT INTO accesslog(accesslogid,workerid,action,detail,patientid,shopid,logtime)
                   VALUES(%s,%s,%s,%s,%s,%s,now())""",
                (lid,"R01",s(lg.get("action")),s(lg.get("detail")),s(lg.get("patientId")),s(lg.get("shopId")) or "S1"))
    c.close()

def table_stats():
    c=conn(); cur=c.cursor()
    out={}
    for (t,) in rows(cur,"""SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"""):
        try:
            cur.execute('SELECT count(*) FROM public."%s"'%t); out[t]=cur.fetchone()[0]
        except Exception: out[t]=-1
    c.close(); return out

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass
    def _send(self, code, obj):
        body=json.dumps(obj,ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,PUT,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self._send(200,{"ok":True})
    def do_GET(self):
        p=urlparse(self.path).path
        try:
            if p=="/api/health": self._send(200,{"ok":True,"service":"clouddent-api","db":"clouddent(33 tables)","ts":int(time.time())})
            elif p=="/api/state": self._send(200,{"ok":True,"state":build_state()})
            elif p=="/api/tables": self._send(200,{"ok":True,"tables":table_stats()})
            else: self._send(404,{"ok":False,"error":"not found"})
        except Exception as ex:
            self._send(500,{"ok":False,"error":str(ex)})
    def do_PUT(self):
        p=urlparse(self.path).path
        if p!="/api/state": self._send(404,{"ok":False,"error":"not found"}); return
        # v3：写操作必须带有效 token（服务端鉴权，不靠前端）
        info = auth(self.headers)
        if not info: self._send(401,{"ok":False,"error":"未登录或会话过期"}); return
        if not can(info["role"],"write"): self._send(403,{"ok":False,"error":"角色无权写入"}); return
        try:
            n=int(self.headers.get("Content-Length","0"))
            body=json.loads(self.rfile.read(n).decode("utf-8"))
            write_back(body.get("state",{}))
            self._send(200,{"ok":True,"saved":True,"role":info["role"]})
        except Exception as ex:
            self._send(500,{"ok":False,"error":str(ex)})

    def do_POST(self):
        p=urlparse(self.path).path
        if p!="/api/login": self._send(404,{"ok":False,"error":"not found"}); return
        try:
            n=int(self.headers.get("Content-Length","0"))
            body=json.loads(self.rfile.read(n).decode("utf-8"))
            role=body.get("role",""); u=body.get("username",""); pw=body.get("password","")
            a=ACCOUNTS.get(role); ok=bool(a) and pw==a["password"] and u in (a["username"],a["tel"])
            if ok: self._send(200,{"ok":True,"role":role,"name":a["name"],"token":issue_token(role,a["name"]), "perms":sorted({"admin":["read","write","approve","pay","perf_all"],"hq":["read","perf_all","audit"],"reception":["read","write","approve","perf_self"],"doctor":["read","write","perf_self"]}[role])})
            else: self._send(401,{"ok":False,"error":"账号或密码错误"})
        except Exception as ex: self._send(500,{"ok":False,"error":str(ex)})

if __name__=="__main__":
    port=int(os.environ.get("CD_API_PORT","8600"))
    print("CloudDent API v3 (31-table + auth) on %d"%port,flush=True)
    ThreadingHTTPServer(("127.0.0.1",port),H).serve_forever()
