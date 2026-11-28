-- =====================================================================
--  v6 增量：在报告 29 表基础上新增 2 张表（→31 张）
--  1) CrossShopRequest  跨店调阅申请（前台/医生发起 + 前台授权）
--  2) ReceptionistPerformance 前台绩效（与 DoctorPerformance 对称）
--  另扩展 DoctorPerformance 补工资条原始字段；应发/提成/五险一金/实发
--  由 API 用同一套公式装配时计算，库里只存原始输入，保证前后端一致。
-- =====================================================================

-- --- 扩展 DoctorPerformance 原有表（补工资条原始字段） ---
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS visits int;
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS specialtybonus numeric(12,2);
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS fullattendance numeric(12,2);
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS satisfaction numeric(12,2);
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS grade varchar(4);
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS shopid varchar(10);
ALTER TABLE doctorperformance ADD COLUMN IF NOT EXISTS name varchar(50);

-- --- 表 30：CrossShopRequest（跨店调阅申请） ---
CREATE TABLE IF NOT EXISTS crossshoprequest (
  CrossShopRequestID varchar(20) PRIMARY KEY,
  PatientID varchar(20) NOT NULL REFERENCES patient(patientid),
  ApplicantID varchar(20) NOT NULL,
  ApplicantRole varchar(20) NOT NULL,
  FromShopID varchar(10) NOT NULL,
  ToShopID varchar(10) NOT NULL,
  Reason varchar(200),
  Status varchar(20) NOT NULL DEFAULT '待授权',
  CreatedAt timestamp NOT NULL DEFAULT now(),
  ExpireAt timestamp,
  ApproverID varchar(20),
  ApprovedByName varchar(50),
  Note varchar(200)
);
GRANT ALL ON crossshoprequest TO clouddent;

-- --- 表 31：ReceptionistPerformance（前台绩效） ---
CREATE TABLE IF NOT EXISTS receptionistperformance (
  ReceptionistPerformanceID varchar(20) PRIMARY KEY,
  ReceptionistID varchar(20) NOT NULL REFERENCES receptionist(receptionistid),
  QuarterSummaryID varchar(20) NOT NULL REFERENCES quarterlycostsummary(quarterlycostsummaryid),
  Month varchar(10), ShopID varchar(10), Name varchar(50),
  Receptions int, BaseSalary numeric(12,2), ConvertBonus numeric(12,2),
  FullAttendance numeric(12,2), Tax numeric(12,2), Score int, Grade varchar(4)
);
GRANT ALL ON receptionistperformance TO clouddent;

-- --- 清旧数据（保证幂等重跑） ---
DELETE FROM crossshoprequest;
DELETE FROM receptionistperformance;
DELETE FROM doctorperformance;

-- --- 灌数据：跨店调阅申请（申请人均为口腔医生；前台仅在业务侧审核授权） ---
INSERT INTO crossshoprequest
 (CrossShopRequestID,PatientID,ApplicantID,ApplicantRole,FromShopID,ToShopID,Reason,Status,CreatedAt,ExpireAt,ApproverID,ApprovedByName,Note)
VALUES
 ('CR000','P001','D01','口腔医生','S1','S2','复诊需核对藏珑店初诊充填记录','已授权','2026-11-20 10:00','2026-12-27 10:00','R01','林晓','已授权：医生可只读查看藏珑店病历'),
 ('CR001','P001','D01','口腔医生','S1','S2','患者自述曾在藏珑店补牙，需核对既往充填记录','待授权','2026-11-14 09:20',NULL,NULL,NULL,'待授权演示'),
 ('CR002','P004','D01','口腔医生','S2','S1','复诊核对本店初诊记录','待授权','2026-11-22 11:00',NULL,NULL,NULL,'前台授权演示：目标门店S1');
-- CR003 原为“前台发起”演示记录，已按单一主执行者口径移除；前台仅在业务侧审核授权。

-- --- 灌数据：医生绩效 12 条（原始字段，实发由API算） ---
INSERT INTO doctorperformance
 (DoctorPerformanceID,DoctorID,QuarterlyCostSummaryID,Month,Revenue,BaseSalary,SpecialtyBonus,FullAttendance,Satisfaction,Tax,Score,Visits,Grade,ShopID,Name)
VALUES
 ('PF01','D01','QC001','2026-10',148600,6000,2000,300,800,1580,96,186,'A','S1','张明远'),
 ('PF01m9','D01','QC001','2026-09',132400,6000,1500,300,0,1210,94,172,'A','S1','张明远'),
 ('PF01m8','D01','QC001','2026-08',119800,6000,1000,300,0,950,92,161,'A','S1','张明远'),
 ('PF02','D02','QC001','2026-10',112300,5000,1200,300,0,780,92,164,'A','S2','李思颖'),
 ('PF02m9','D02','QC001','2026-09',105600,5000,1000,300,0,640,90,158,'A','S2','李思颖'),
 ('PF02m8','D02','QC001','2026-08',96800,5000,800,300,0,510,89,149,'B','S2','李思颖'),
 ('PF03','D03','QC001','2026-10',98700,5000,600,300,0,410,87,132,'B','S3','王浩然'),
 ('PF03m9','D03','QC001','2026-09',91200,5000,500,300,0,330,85,126,'B','S3','王浩然'),
 ('PF03m8','D03','QC001','2026-08',85600,5000,400,300,0,260,84,118,'B','S3','王浩然'),
 ('PF04','D04','QC001','2026-10',76200,5000,500,300,0,190,89,118,'B','S1','陈静怡'),
 ('PF04m9','D04','QC001','2026-09',70400,5000,400,300,0,130,87,110,'B','S1','陈静怡'),
 ('PF04m8','D04','QC001','2026-08',65800,5000,300,300,0,90,86,104,'B','S1','陈静怡');

-- --- 灌数据：前台绩效 9 条（原始字段） ---
INSERT INTO receptionistperformance
 (ReceptionistPerformanceID,ReceptionistID,QuarterSummaryID,Month,ShopID,Name,Receptions,BaseSalary,ConvertBonus,FullAttendance,Tax,Score,Grade)
VALUES
 ('SPF01','R01','QC001','2026-10','S1','林晓',412,4000,900,200,95,94,'A'),
 ('SPF01m9','R01','QC001','2026-09','S1','林晓',388,4000,750,200,70,92,'A'),
 ('SPF01m8','R01','QC001','2026-08','S1','林晓',365,4000,600,200,50,90,'A'),
 ('SPF02','R02','QC001','2026-10','S2','何静',368,4000,700,200,65,91,'A'),
 ('SPF02m9','R02','QC001','2026-09','S2','何静',350,4000,600,200,45,89,'B'),
 ('SPF02m8','R02','QC001','2026-08','S2','何静',332,4000,500,200,30,88,'B'),
 ('SPF03','R03','QC001','2026-10','S3','郑楠',296,4000,500,200,25,88,'B'),
 ('SPF03m9','R03','QC001','2026-09','S3','郑楠',281,4000,450,200,15,86,'B'),
 ('SPF03m8','R03','QC001','2026-08','S3','郑楠',268,4000,400,200,10,85,'B');

-- --- 校验 ---
SELECT 'crossshoprequest' AS tbl, count(*) AS n FROM crossshoprequest
UNION ALL SELECT 'doctorperformance', count(*) FROM doctorperformance
UNION ALL SELECT 'receptionistperformance', count(*) FROM receptionistperformance;
