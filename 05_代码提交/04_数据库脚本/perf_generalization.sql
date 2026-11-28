-- =====================================================================
--  v6.1：绩效泛化改造（31 表 → 32 表）
--  Performance 父类独立建表；DoctorPerformance / ReceptionistPerformance
--  两个子类主键即父类主键（兼外键），公共字段上移父类。
--  与报告 §4 总实体类图、§5 总ER图及数据库表设计总表一致。
-- =====================================================================

-- 旧表数据可由 add_two_tables.sql / 本脚本重灌，直接重建
DROP TABLE IF EXISTS doctorperformance CASCADE;
DROP TABLE IF EXISTS receptionistperformance CASCADE;
DROP TABLE IF EXISTS performance CASCADE;

-- --- 表 32：Performance（绩效父类） ---
CREATE TABLE Performance (
  PerformanceID varchar(20) PRIMARY KEY,
  QuarterlyCostSummaryID varchar(20) NOT NULL REFERENCES QuarterlyCostSummary(QuarterlyCostSummaryID),
  Month varchar(10),
  ShopID varchar(10),
  Name varchar(50),
  BaseSalary numeric(12,2),
  FullAttendance numeric(12,2),
  Tax numeric(12,2),
  Score int,
  Grade varchar(4)
);
GRANT ALL ON performance TO clouddent;

-- --- 表 7：DoctorPerformance（医生绩效子类） ---
CREATE TABLE DoctorPerformance (
  DoctorPerformanceID varchar(20) PRIMARY KEY REFERENCES Performance(PerformanceID),
  DoctorID varchar(20) NOT NULL REFERENCES Doctor(DoctorID),
  Revenue numeric(12,2),
  SpecialtyBonus numeric(12,2),
  Satisfaction numeric(12,2),
  Visits int
);
GRANT ALL ON doctorperformance TO clouddent;

-- --- 表 31：ReceptionistPerformance（前台绩效子类） ---
CREATE TABLE ReceptionistPerformance (
  ReceptionistPerformanceID varchar(20) PRIMARY KEY REFERENCES Performance(PerformanceID),
  ReceptionistID varchar(20) NOT NULL REFERENCES Receptionist(ReceptionistID),
  Receptions int,
  ConvertBonus numeric(12,2)
);
GRANT ALL ON receptionistperformance TO clouddent;

-- --- 父类数据：医生 12 条 + 前台 9 条（公共字段） ---
INSERT INTO Performance
 (PerformanceID,QuarterlyCostSummaryID,Month,ShopID,Name,BaseSalary,FullAttendance,Tax,Score,Grade)
VALUES
 ('PF01','QC001','2026-10','S1','张明远',6000,300,1580,96,'A'),
 ('PF01m9','QC001','2026-09','S1','张明远',6000,300,1210,94,'A'),
 ('PF01m8','QC001','2026-08','S1','张明远',6000,300,950,92,'A'),
 ('PF02','QC001','2026-10','S2','李思颖',5000,300,780,92,'A'),
 ('PF02m9','QC001','2026-09','S2','李思颖',5000,300,640,90,'A'),
 ('PF02m8','QC001','2026-08','S2','李思颖',5000,300,510,89,'B'),
 ('PF03','QC001','2026-10','S3','王浩然',5000,300,410,87,'B'),
 ('PF03m9','QC001','2026-09','S3','王浩然',5000,300,330,85,'B'),
 ('PF03m8','QC001','2026-08','S3','王浩然',5000,300,260,84,'B'),
 ('PF04','QC001','2026-10','S1','陈静怡',5000,300,190,89,'B'),
 ('PF04m9','QC001','2026-09','S1','陈静怡',5000,300,130,87,'B'),
 ('PF04m8','QC001','2026-08','S1','陈静怡',5000,300,90,86,'B'),
 ('SPF01','QC001','2026-10','S1','林晓',4000,200,95,94,'A'),
 ('SPF01m9','QC001','2026-09','S1','林晓',4000,200,70,92,'A'),
 ('SPF01m8','QC001','2026-08','S1','林晓',4000,200,50,90,'A'),
 ('SPF02','QC001','2026-10','S2','何静',4000,200,65,91,'A'),
 ('SPF02m9','QC001','2026-09','S2','何静',4000,200,45,89,'B'),
 ('SPF02m8','QC001','2026-08','S2','何静',4000,200,30,88,'B'),
 ('SPF03','QC001','2026-10','S3','郑楠',4000,200,25,88,'B'),
 ('SPF03m9','QC001','2026-09','S3','郑楠',4000,200,15,86,'B'),
 ('SPF03m8','QC001','2026-08','S3','郑楠',4000,200,10,85,'B');

-- --- 子类数据：医生绩效 12 条（岗位特有字段） ---
INSERT INTO DoctorPerformance
 (DoctorPerformanceID,DoctorID,Revenue,SpecialtyBonus,Satisfaction,Visits)
VALUES
 ('PF01','D01',148600,2000,800,186),
 ('PF01m9','D01',132400,1500,0,172),
 ('PF01m8','D01',119800,1000,0,161),
 ('PF02','D02',112300,1200,0,164),
 ('PF02m9','D02',105600,1000,0,158),
 ('PF02m8','D02',96800,800,0,149),
 ('PF03','D03',98700,600,0,132),
 ('PF03m9','D03',91200,500,0,126),
 ('PF03m8','D03',85600,400,0,118),
 ('PF04','D04',76200,500,0,118),
 ('PF04m9','D04',70400,400,0,110),
 ('PF04m8','D04',65800,300,0,104);

-- --- 子类数据：前台绩效 9 条（岗位特有字段） ---
INSERT INTO ReceptionistPerformance
 (ReceptionistPerformanceID,ReceptionistID,Receptions,ConvertBonus)
VALUES
 ('SPF01','R01',412,900),
 ('SPF01m9','R01',388,750),
 ('SPF01m8','R01',365,600),
 ('SPF02','R02',368,700),
 ('SPF02m9','R02',350,600),
 ('SPF02m8','R02',332,500),
 ('SPF03','R03',296,500),
 ('SPF03m9','R03',281,450),
 ('SPF03m8','R03',268,400);

-- --- 校验 ---
SELECT 'performance' AS tbl, count(*) AS n FROM performance
UNION ALL SELECT 'doctorperformance', count(*) FROM doctorperformance
UNION ALL SELECT 'receptionistperformance', count(*) FROM receptionistperformance;
