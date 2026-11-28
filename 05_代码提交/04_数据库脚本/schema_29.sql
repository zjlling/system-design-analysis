-- =====================================================================
--  云齿通系统 · 关系型数据库建库脚本（严格对照 v5 报告 §5 的 29 张表）
--  来源：报告 §5.2「数据库表设计总表」29 表 + 分析类图实体属性
--  规则：泛化=子类主键即外键引用父类；1:*外键放多方；组合=非空+级联；
--        聚合=可空无级联；1:1=外键唯一；*:*=中间表
--  数据库：clouddent  字符集 UTF8
-- =====================================================================
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- 1 Patient（患者）
CREATE TABLE Patient (
  PatientID varchar(20) PRIMARY KEY,
  Name varchar(50) NOT NULL, Gender varchar(4), Age int, Phone varchar(20) UNIQUE,
  IDNo varchar(30) UNIQUE, Allergy varchar(200), Level varchar(20), ShopID varchar(10) DEFAULT 'S1',
  Created date, Remark varchar(200)
);
-- 2 Worker（工作人员父类）
CREATE TABLE Worker (
  WorkerID varchar(20) PRIMARY KEY, Name varchar(50) NOT NULL, WorkerType varchar(20) NOT NULL,
  Phone varchar(20), ShopID varchar(10), OnJob boolean DEFAULT true
);
-- 3 Doctor（医生，泛化子类）
CREATE TABLE Doctor (
  DoctorID varchar(20) PRIMARY KEY REFERENCES Worker(WorkerID) ON DELETE CASCADE,
  Title varchar(30), Dept varchar(30), LicenseNo varchar(40)
);
-- 4 Receptionist（前台导诊，泛化子类）
CREATE TABLE Receptionist (
  ReceptionistID varchar(20) PRIMARY KEY REFERENCES Worker(WorkerID) ON DELETE CASCADE,
  CounterNo varchar(20)
);
-- 5 AllergyRecord（过敏记录，1:* 非空）
CREATE TABLE AllergyRecord (
  AllergyRecordID varchar(20) PRIMARY KEY, PatientID varchar(20) NOT NULL REFERENCES Patient(PatientID),
  Allergen varchar(50), Reaction varchar(100), RecordDate date
);
-- 6 QuarterlyCostSummary（季度成本汇总）
CREATE TABLE QuarterlyCostSummary (
  QuarterlyCostSummaryID varchar(20) PRIMARY KEY, Quarter varchar(10), ShopID varchar(10),
  TotalCost numeric(12,2), StaffCost numeric(12,2), MaterialCost numeric(12,2)
);
-- 7 DoctorPerformance（医生绩效，两外键非空）
CREATE TABLE DoctorPerformance (
  DoctorPerformanceID varchar(20) PRIMARY KEY,
  DoctorID varchar(20) NOT NULL REFERENCES Doctor(DoctorID),
  QuarterlyCostSummaryID varchar(20) NOT NULL REFERENCES QuarterlyCostSummary(QuarterlyCostSummaryID),
  Month varchar(10), Revenue numeric(12,2), BaseSalary numeric(12,2), Commission numeric(12,2),
  Bonus numeric(12,2), SocialInsurance numeric(12,2), Tax numeric(12,2), NetSalary numeric(12,2), Score int
);
-- 8 Supplier（供应商）
CREATE TABLE Supplier (
  SupplierID varchar(20) PRIMARY KEY, Name varchar(50) NOT NULL, Contact varchar(30), Phone varchar(20)
);
-- 9 ConsumableCategory（耗材品类）
CREATE TABLE ConsumableCategory (
  ConsumableCategoryID varchar(20) PRIMARY KEY, Name varchar(50) NOT NULL,
  Spec varchar(50), Unit varchar(10), SafetyThreshold numeric(10,2), Price numeric(10,2)
);
-- 10 ConsumablePurchase（耗材入库单，SupplierID 可空聚合；QuarterlyCostSummaryID 非空）
CREATE TABLE ConsumablePurchase (
  ConsumablePurchaseID varchar(20) PRIMARY KEY,
  SupplierID varchar(20) REFERENCES Supplier(SupplierID),
  QuarterlyCostSummaryID varchar(20) NOT NULL REFERENCES QuarterlyCostSummary(QuarterlyCostSummaryID),
  PurchaseDate date, OperatorID varchar(20), TotalAmount numeric(12,2)
);
-- 11 BatchStock（批次库存，两外键可空聚合）
CREATE TABLE BatchStock (
  BatchStockID varchar(20) PRIMARY KEY,
  ConsumableCategoryID varchar(20) REFERENCES ConsumableCategory(ConsumableCategoryID),
  ConsumablePurchaseID varchar(20) REFERENCES ConsumablePurchase(ConsumablePurchaseID),
  BatchNo varchar(30), Qty numeric(10,2), StockDate date, ExpiryDate date
);
-- 12 StockWarning（库存预警，外键可空聚合）
CREATE TABLE StockWarning (
  StockWarningID varchar(20) PRIMARY KEY,
  ConsumableCategoryID varchar(20) REFERENCES ConsumableCategory(ConsumableCategoryID),
  WarningType varchar(20), WarningStatus varchar(20), WarningDate date
);
-- 13 PurchaseDetail（入库明细，*:*中间表，双外键非空+唯一）
CREATE TABLE PurchaseDetail (
  PurchaseDetailID varchar(20) PRIMARY KEY,
  ConsumablePurchaseID varchar(20) NOT NULL REFERENCES ConsumablePurchase(ConsumablePurchaseID) ON DELETE CASCADE,
  ConsumableCategoryID varchar(20) NOT NULL REFERENCES ConsumableCategory(ConsumableCategoryID),
  Qty numeric(10,2), Price numeric(10,2), BatchNo varchar(30),
  UNIQUE(ConsumablePurchaseID, ConsumableCategoryID)
);
-- 14 MedicalRecord（病历 1:1，患者外键非空唯一）
CREATE TABLE MedicalRecord (
  MedicalRecordID varchar(20) PRIMARY KEY,
  PatientID varchar(20) NOT NULL UNIQUE REFERENCES Patient(PatientID),
  Allergy varchar(200), Summary varchar(500), Created date, Updated date
);
-- 15 TreatmentRecord（诊疗记录，三外键非空）
CREATE TABLE TreatmentRecord (
  TreatmentRecordID varchar(20) PRIMARY KEY,
  PatientID varchar(20) NOT NULL REFERENCES Patient(PatientID),
  DoctorID varchar(20) NOT NULL REFERENCES Doctor(DoctorID),
  MedicalRecordID varchar(20) NOT NULL REFERENCES MedicalRecord(MedicalRecordID),
  Tooth varchar(20), Chief varchar(200), Diagnosis varchar(200), Treatment varchar(300),
  Imaging varchar(200), RecordDate date, ShopID varchar(10)
);
-- 16 ConsumableConsumption（耗材消耗，TreatmentRecordID 非空，耗材可空聚合）
CREATE TABLE ConsumableConsumption (
  ConsumableConsumptionID varchar(20) PRIMARY KEY,
  ConsumableCategoryID varchar(20) REFERENCES ConsumableCategory(ConsumableCategoryID),
  TreatmentRecordID varchar(20) NOT NULL REFERENCES TreatmentRecord(TreatmentRecordID),
  Qty numeric(10,2), UseDate date
);
-- 17 DoctorSchedule（医生排班，外键非空）
CREATE TABLE DoctorSchedule (
  DoctorScheduleID varchar(20) PRIMARY KEY,
  DoctorID varchar(20) NOT NULL REFERENCES Doctor(DoctorID),
  ScheduleDate date, TimeSlot varchar(30), ShopID varchar(10)
);
-- 18 Appointment（预约单，PatientID非空；TreatmentRecordID可空复诊指向既往）
CREATE TABLE Appointment (
  AppointmentID varchar(20) PRIMARY KEY,
  PatientID varchar(20) NOT NULL REFERENCES Patient(PatientID),
  TreatmentRecordID varchar(20) REFERENCES TreatmentRecord(TreatmentRecordID),
  AppointmentTime timestamp, Status varchar(20), Source varchar(20), ShopID varchar(10), DoctorID varchar(20)
);
-- 19 AppointmentSlot（号源，排班非空；AppointmentID可空唯一）
CREATE TABLE AppointmentSlot (
  AppointmentSlotID varchar(20) PRIMARY KEY,
  DoctorScheduleID varchar(20) NOT NULL REFERENCES DoctorSchedule(DoctorScheduleID),
  AppointmentID varchar(20) UNIQUE REFERENCES Appointment(AppointmentID),
  TimeSlot varchar(30), Status varchar(20)
);
-- 20 DentalChair（牙椅）
CREATE TABLE DentalChair (
  DentalChairID varchar(20) PRIMARY KEY, Room varchar(30), ChairNo varchar(20), Status varchar(20), ShopID varchar(10)
);
-- 21 ChairOccupancy（牙椅占用，组合=牙椅非空级联；预约可空唯一）
CREATE TABLE ChairOccupancy (
  ChairOccupancyID varchar(20) PRIMARY KEY,
  DentalChairID varchar(20) NOT NULL REFERENCES DentalChair(DentalChairID) ON DELETE CASCADE,
  AppointmentID varchar(20) UNIQUE REFERENCES Appointment(AppointmentID),
  StartTime timestamp, EndTime timestamp
);
-- 22 ChargeSheet（收费单，TreatmentRecordID非空）
CREATE TABLE ChargeSheet (
  ChargeSheetID varchar(20) PRIMARY KEY,
  TreatmentRecordID varchar(20) NOT NULL REFERENCES TreatmentRecord(TreatmentRecordID),
  PatientID varchar(20) NOT NULL REFERENCES Patient(PatientID),
  TotalAmount numeric(12,2), Status varchar(20), ChargeDate date, ShopID varchar(10)
);
-- 23 ChargeDetail（收费明细，外键非空）
CREATE TABLE ChargeDetail (
  ChargeDetailID varchar(20) PRIMARY KEY,
  ChargeSheetID varchar(20) NOT NULL REFERENCES ChargeSheet(ChargeSheetID) ON DELETE CASCADE,
  ItemName varchar(100), Qty int, Price numeric(10,2), Amount numeric(12,2)
);
-- 24 PaymentRecord（支付记录，外键非空）
CREATE TABLE PaymentRecord (
  PaymentRecordID varchar(20) PRIMARY KEY,
  ChargeSheetID varchar(20) NOT NULL REFERENCES ChargeSheet(ChargeSheetID),
  Channel varchar(20), Amount numeric(12,2), PayResult varchar(20), PayTime timestamp
);
-- 25 ElectronicReceipt（电子收据，外键可空唯一）
CREATE TABLE ElectronicReceipt (
  ElectronicReceiptID varchar(20) PRIMARY KEY,
  ChargeSheetID varchar(20) UNIQUE REFERENCES ChargeSheet(ChargeSheetID),
  ReceiptNo varchar(30), IssueTime timestamp
);
-- 26 MembershipAccount（会员账户，患者外键可空唯一）
CREATE TABLE MembershipAccount (
  MembershipAccountID varchar(20) PRIMARY KEY,
  PatientID varchar(20) UNIQUE REFERENCES Patient(PatientID),
  Balance numeric(12,2), Points int, CardNo varchar(30) UNIQUE, Level varchar(20)
);
-- 27 ReturnVisitTask（回访任务，PatientID非空；会员可空）
CREATE TABLE ReturnVisitTask (
  ReturnVisitTaskID varchar(20) PRIMARY KEY,
  PatientID varchar(20) NOT NULL REFERENCES Patient(PatientID),
  MembershipAccountID varchar(20) REFERENCES MembershipAccount(MembershipAccountID),
  CreateTime timestamp, Status varchar(20), PlanDate date, Type varchar(30), Result varchar(300)
);
-- 28 ReturnVisitFeedback（回访反馈，外键可空唯一 1:0..1）
CREATE TABLE ReturnVisitFeedback (
  ReturnVisitFeedbackID varchar(20) PRIMARY KEY,
  ReturnVisitTaskID varchar(20) UNIQUE REFERENCES ReturnVisitTask(ReturnVisitTaskID),
  Content varchar(500), Reply varchar(500), FeedbackTime timestamp
);
-- 29 AccessLog（访问日志，外键非空）
CREATE TABLE AccessLog (
  AccessLogID varchar(20) PRIMARY KEY,
  WorkerID varchar(20) NOT NULL REFERENCES Worker(WorkerID),
  Action varchar(100), Detail varchar(300), PatientID varchar(20), ShopID varchar(10), LogTime timestamp
);

-- 权限
GRANT ALL ON ALL TABLES IN SCHEMA public TO clouddent;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO clouddent;
