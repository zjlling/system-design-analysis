// 云齿通 CloudDent · 患者端数据层（本机存储 + 云端只读同步）
var PREFIX = 'cdv2_';
var API_BASE = 'http://206.237.21.229/api/state';

var ACCOUNTS = [
  { phone: '13800000001', password: '123456', patientId: 'P001', name: '陈女士', shopId: 'S1' },
  { phone: '13800000002', password: '123456', patientId: 'P004', name: '赵女士', shopId: 'S2' },
  { phone: '13800000003', password: '123456', patientId: 'P006', name: '何女士', shopId: 'S3' }
];

var SEED = {
  shops: [
    { id: 'S1', name: '东方新城店' },
    { id: 'S2', name: '藏珑店' },
    { id: 'S3', name: '北辰三角洲店' }
  ],
  departments: [
    { id: 'DP1', name: '口腔修复科' },
    { id: 'DP2', name: '牙体牙髓科' },
    { id: 'DP3', name: '牙周科' },
    { id: 'DP4', name: '正畸科' }
  ],
  doctors: [
    { id: 'D01', name: '张明远', dept: '口腔修复科', shopId: 'S1' },
    { id: 'D04', name: '陈静怡', dept: '牙周科', shopId: 'S1' },
    { id: 'D05', name: '刘婉清', dept: '牙体牙髓科', shopId: 'S1' },
    { id: 'D06', name: '周正', dept: '正畸科', shopId: 'S1' },
    { id: 'D02', name: '李思颖', dept: '牙体牙髓科', shopId: 'S2' },
    { id: 'D07', name: '吴敏', dept: '口腔修复科', shopId: 'S2' },
    { id: 'D08', name: '郑亦然', dept: '正畸科', shopId: 'S2' },
    { id: 'D03', name: '王浩然', dept: '正畸科', shopId: 'S3' },
    { id: 'D09', name: '孙雅', dept: '牙周科', shopId: 'S3' },
    { id: 'D10', name: '何川', dept: '口腔修复科', shopId: 'S3' }
  ],
  services: [
    { id: 'SV01', name: '口腔检查', price: 180, dept: '口腔修复科' },
    { id: 'SV02', name: '超声波洁牙', price: 320, dept: '牙周科' },
    { id: 'SV03', name: '窝沟封闭', price: 260, dept: '牙体牙髓科' },
    { id: 'SV04', name: '树脂充填', price: 420, dept: '口腔修复科' },
    { id: 'SV05', name: '根管治疗（前牙）', price: 980, dept: '牙体牙髓科' },
    { id: 'SV06', name: '根管治疗（后牙）', price: 1680, dept: '牙体牙髓科' },
    { id: 'SV07', name: '隐形矫正复诊', price: 1200, dept: '正畸科' },
    { id: 'SV08', name: '牙齿美白', price: 1280, dept: '口腔修复科' },
    { id: 'SV09', name: '牙周刮治', price: 560, dept: '牙周科' },
    { id: 'SV10', name: '正畸初诊', price: 300, dept: '正畸科' }
  ],
  appointments: [
    { id: 'AP001', patientId: 'P001', name: '陈女士', shopId: 'S1', date: '2026-11-16', time: '09:00-10:00', doctor: '张明远', item: '口腔检查', status: '已预约', chair: '3 号牙椅' },
    { id: 'AP004', patientId: 'P004', name: '赵女士', shopId: 'S2', date: '2026-11-14', time: '14:00-15:00', doctor: '李思颖', item: '根管治疗（后牙）', status: '已预约', chair: '1 号牙椅' },
    { id: 'AP006', patientId: 'P006', name: '何女士', shopId: 'S3', date: '2026-11-17', time: '15:00-16:00', doctor: '王浩然', item: '隐形矫正复诊', status: '已预约', chair: '2 号牙椅' }
  ],
  bills: [
    { id: 'CS001', billNo: 'CS20261114001', patientId: 'P001', shopId: 'S1', item: '口腔检查 + 全景片', amount: 180, status: '待支付', method: '', receipt: '', date: '2026-11-14' },
    { id: 'CS002', billNo: 'CS20261114002', patientId: 'P001', shopId: 'S1', item: '超声波洁牙', amount: 320, status: '待支付', method: '', receipt: '', date: '2026-11-14' },
    { id: 'CS003', billNo: 'CS20261108001', patientId: 'P001', shopId: 'S1', item: '根管治疗（前牙）', amount: 980, status: '已支付', method: '微信', receipt: 'RCP20261108001', date: '2026-11-08' },
    { id: 'CS005', billNo: 'CS20261114004', patientId: 'P004', shopId: 'S2', item: '根管治疗（后牙）', amount: 1680, status: '待支付', method: '', receipt: '', date: '2026-11-14' },
    { id: 'CS007', billNo: 'CS20261117001', patientId: 'P006', shopId: 'S3', item: '隐形矫正复诊', amount: 1200, status: '已支付', method: '微信', receipt: 'RCP20261117001', date: '2026-11-17' }
  ],
  members: [
    { patientId: 'P001', cardNo: 'VIP 8802 3361', balance: 1280, points: 2360, level: '银卡会员' },
    { patientId: 'P004', cardNo: 'VIP 8801 7735', balance: 3600, points: 5820, level: '金卡会员' },
    { patientId: 'P006', cardNo: 'VIP 8803 2290', balance: 860, points: 940, level: '银卡会员' }
  ],
  feedbacks: [
    { id: 'FB01', patientId: 'P001', date: '2026-11-09', content: '洁牙后牙龈无明显不适，医生讲解很耐心。', reply: '感谢反馈，已为您安排 3 个月后复诊提醒。' },
    { id: 'FB02', patientId: 'P004', date: '2026-11-11', content: '候诊时间比之前短了很多。', reply: '' }
  ],
  records: [
    { id: 'TR001', patientId: 'P001', shopId: 'S1', doctor: '张明远', tooth: '36', chief: '左下后牙冷热刺激痛', diagnosis: '牙髓炎', treatment: '开髓引流 + 根管预备', imaging: '全景片 2026-11-08', date: '2026-11-14' },
    { id: 'TR004', patientId: 'P001', shopId: 'S2', doctor: '李思颖', tooth: '26', chief: '补牙材料脱落', diagnosis: '充填体脱落', treatment: '重新树脂充填', imaging: '根尖片 2026-09-02', date: '2026-09-02' },
    { id: 'TR003', patientId: 'P004', shopId: 'S2', doctor: '李思颖', tooth: '46', chief: '咬合痛一周', diagnosis: '根尖周炎', treatment: '根管治疗（后牙）', imaging: '根尖片 2026-11-14', date: '2026-11-14' },
    { id: 'TR005', patientId: 'P006', shopId: 'S3', doctor: '王浩然', tooth: '11', chief: '矫正复诊', diagnosis: '安氏Ⅱ类错𬌗', treatment: '更换弓丝', imaging: '头颅侧位片 2026-08-20', date: '2026-11-17' }
  ],
  notices: [
    { id: 'N01', text: '东方新城店本周六增设牙周专科门诊', tag: '门诊' },
    { id: 'N02', text: '电子收据已上线，可在缴费记录中查看', tag: '服务' }
  ],
  session: {},
  accessLogs: [],
  role: 'patient',
  staffName: ''
};

function init() {
  Object.keys(SEED).forEach(function (k) {
    if (wx.getStorageSync(PREFIX + k) === '') {
      wx.setStorageSync(PREFIX + k, SEED[k]);
    }
  });
}
function get(k) { return wx.getStorageSync(PREFIX + k); }
function getObj(k) { var v = get(k); return v && typeof v === 'object' ? v : {}; }
function set(k, v) { wx.setStorageSync(PREFIX + k, v); }
function shopName(id) {
  var s = SEED.shops.find(function (x) { return x.id === id; });
  return s ? s.name : (id || '');
}
function toast(title, icon) { wx.showToast({ title: title, icon: icon || 'success' }); }
function log(action, detail) {
  var s = getObj('session'), list = get('accessLogs') || [];
  list.unshift({ time: new Date().toLocaleString('zh-CN'), patientId: s.patientId || '', action: action, detail: detail || '' });
  set('accessLogs', list.slice(0, 50));
}
function guard() {
  var s = getObj('session');
  if (!s || !s.patientId) { wx.reLaunch({ url: '/pages/login/login' }); return null; }
  return s;
}
function mine(list) {
  var s = getObj('session');
  return (list || []).filter(function (x) { return x.patientId === s.patientId; });
}

// —— 云端只读同步：把 32 张表的 state 映射到小程序本地数据层 ——
var DOC_NAME = {
  D01: '张明远', D02: '李思颖', D03: '王浩然', D04: '陈静怡', D05: '刘婉清',
  D06: '周正', D07: '吴敏', D08: '郑亦然', D09: '孙雅', D10: '何川'
};
var CHAIR_NAME = {
  DC001: '1 号牙椅', DC002: '2 号牙椅', DC003: '3 号牙椅', DC004: '4 号牙椅',
  DC005: '5 号牙椅', DC006: '6 号牙椅', DC007: '7 号牙椅'
};
function normAppt(a) {
  var t = a.time || '';
  if (t.indexOf(' ') >= 0) t = t.split(' ').slice(1).join(' ');
  return {
    id: a.id, patientId: a.patientId, name: a.name || '', shopId: a.shopId,
    date: a.date, time: t, doctor: a.doctor || DOC_NAME[a.doctorId] || '',
    item: a.item, status: a.status, chair: CHAIR_NAME[a.chair] || a.chair || '待分配',
    source: a.source || ''
  };
}
function normBill(b) {
  var st = b.status === '已收款' ? '已支付' : b.status;
  return {
    id: b.id, billNo: b.billNo || b.id, patientId: b.patientId, shopId: b.shopId,
    item: b.item, amount: b.amount, status: st, method: b.method || b.payMethod || '',
    receipt: b.receipt || '', date: b.date
  };
}
function normRecord(r) {
  return {
    id: r.id, patientId: r.patientId, shopId: r.shopId,
    doctor: r.doctor || DOC_NAME[r.doctorId] || '', tooth: r.tooth,
    chief: r.chief, diagnosis: r.diagnosis, treatment: r.treatment,
    imaging: r.imaging || '', date: r.date
  };
}
function mergeKey(key, remote) {
  var local = get(key) || [];
  var map = {};
  local.forEach(function (x) { map[x.id] = x; });
  (remote || []).forEach(function (x) { map[x.id] = x; }); // 云端覆盖本地同 id
  var out = [];
  Object.keys(map).forEach(function (id) { out.push(map[id]); });
  set(key, out);
}
function syncCloud(done) {
  wx.request({
    url: API_BASE,
    method: 'GET',
    timeout: 8000,
    success: function (res) {
      try {
        var d = res.data && res.data.data ? res.data.data : res.data;
        var st = d && d.state ? d.state : (d && d.appointments ? d : null);
        if (st && st.appointments) {
          mergeKey('appointments', (st.appointments || []).map(normAppt));
          mergeKey('bills', (st.bills || []).map(normBill));
          mergeKey('records', (st.records || []).map(normRecord));
          mergeKey('feedbacks', st.feedbacks || []);
          wx.setStorageSync(PREFIX + 'cloudConnected', true);
          if (typeof done === 'function') done(true);
          return;
        }
      } catch (e) { /* 解析失败回退本地 */ }
      wx.setStorageSync(PREFIX + 'cloudConnected', false);
      if (typeof done === 'function') done(false);
    },
    fail: function () {
      wx.setStorageSync(PREFIX + 'cloudConnected', false);
      if (typeof done === 'function') done(false);
    }
  });
}

module.exports = {
  ACCOUNTS: ACCOUNTS, SEED: SEED, init: init, get: get, getObj: getObj, set: set,
  shopName: shopName, toast: toast, log: log, guard: guard, mine: mine, syncCloud: syncCloud
};
