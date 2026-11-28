-- 门店（Shop）：DenUC018 维护门店基础信息所操作的实体
CREATE TABLE Shop (
    ShopID varchar(10) PRIMARY KEY,
    Name varchar(50) NOT NULL UNIQUE,
    Address varchar(150) NOT NULL,
    Tel varchar(30) NOT NULL UNIQUE,
    ChairCount int NOT NULL,
    Status varchar(10) NOT NULL
);

INSERT INTO Shop (ShopID, Name, Address, Tel, ChairCount, Status) VALUES
('S1', '东方新城店', '长沙市芙蓉区东方新城 1 栋', '0731-8866 1201', 6, '营业中'),
('S2', '藏珑店', '长沙市开福区藏珑路 88 号', '0731-8866 1202', 4, '营业中'),
('S3', '北辰三角洲店', '长沙市开福区北辰三角洲 A2', '0731-8866 1203', 5, '营业中');
