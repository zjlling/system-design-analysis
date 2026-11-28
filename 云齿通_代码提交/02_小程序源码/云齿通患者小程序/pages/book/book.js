const Store = require('../../utils/store.js');

Page({
  data: {
    shopNames: [], deptNames: [], doctorNames: [], serviceNames: [], dates: [], times: [],
    shopIndex: 0, deptIndex: 0, doctorIndex: 0, serviceIndex: 0, dateIndex: 0, timeIndex: 0,
    doctors: [], services: [], list: []
  },
  onLoad: function () {
    const shops = Store.get('shops') || [];
    const dates = ['2026-11-15', '2026-11-16', '2026-11-17', '2026-11-18'];
    const times = ['09:00-10:00', '10:00-11:00', '14:00-15:00', '15:00-16:00'];
    this.setData({
      shopNames: shops.map(function (x) { return x.name; }),
      dates: dates, times: times
    });
    this.pickDepts(0);
  },
  onShow: function () {
    if (!Store.guard()) return;
    this.refresh();
  },
  pickDepts: function (shopIndex) {
    const shops = Store.get('shops') || [];
    const sid = shops[shopIndex] ? shops[shopIndex].id : '';
    const ds = (Store.get('doctors') || []).filter(function (d) { return d.shopId === sid; });
    const seen = {};
    var depts = [];
    ds.forEach(function (d) { if (!seen[d.dept]) { seen[d.dept] = 1; depts.push(d.dept); } });
    if (!depts.length) {
      depts = (Store.get('departments') || []).map(function (x) { return x.name; });
    }
    this.setData({ deptNames: depts, deptIndex: 0 });
    this.pickDoctors(shopIndex, depts[0]);
  },
  pickDoctors: function (shopIndex, dept) {
    const shops = Store.get('shops') || [];
    const sid = shops[shopIndex] ? shops[shopIndex].id : '';
    const ds = (Store.get('doctors') || []).filter(function (d) {
      return d.shopId === sid && (!dept || d.dept === dept);
    });
    this.setData({
      doctors: ds,
      doctorNames: ds.map(function (d) { return d.name + ' · ' + d.dept; }),
      doctorIndex: 0
    });
    this.pickServices(dept);
  },
  pickServices: function (dept) {
    const all = Store.get('services') || [];
    const svs = dept ? all.filter(function (x) { return x.dept === dept; }) : all;
    const list = svs.length ? svs : all;
    this.setData({
      services: list,
      serviceNames: list.map(function (x) { return x.name + ' ¥' + x.price; }),
      serviceIndex: 0
    });
  },
  refresh: function () {
    const list = Store.mine(Store.get('appointments')).map(function (a) {
      return Object.assign({}, a, {
        shopName: Store.shopName(a.shopId),
        canCancel: a.status === '已预约' || a.status === '待到诊'
      });
    });
    this.setData({ list: list });
  },
  onShop: function (e) {
    const i = Number(e.detail.value);
    this.setData({ shopIndex: i });
    this.pickDepts(i);
  },
  onDept: function (e) {
    const i = Number(e.detail.value);
    this.setData({ deptIndex: i });
    this.pickDoctors(this.data.shopIndex, this.data.deptNames[i]);
  },
  onDoctor: function (e) { this.setData({ doctorIndex: Number(e.detail.value) }); },
  onService: function (e) { this.setData({ serviceIndex: Number(e.detail.value) }); },
  onDate: function (e) { this.setData({ dateIndex: Number(e.detail.value) }); },
  onTime: function (e) { this.setData({ timeIndex: Number(e.detail.value) }); },
  submit: function () {
    const s = Store.guard();
    if (!s) return;
    const shops = Store.get('shops') || [];
    const shop = shops[this.data.shopIndex];
    const doc = this.data.doctors[this.data.doctorIndex];
    const svc = this.data.services[this.data.serviceIndex];
    if (!shop || !doc || !svc) { Store.toast('请完整选择预约信息', 'none'); return; }
    const date = this.data.dates[this.data.dateIndex];
    const time = this.data.times[this.data.timeIndex];
    const all = Store.get('appointments') || [];
    const dup = all.some(function (a) {
      return a.patientId === s.patientId && a.date === date && a.time === time && a.status !== '已取消';
    });
    if (dup) { Store.toast('该时段已有预约', 'none'); return; }
    all.unshift({
      id: 'AP' + Date.now(), patientId: s.patientId, name: s.name, shopId: shop.id,
      dept: doc.dept, date: date, time: time, doctor: doc.name, item: svc.name,
      status: '已预约', chair: '待分配', source: '小程序'
    });
    Store.set('appointments', all);
    Store.log('提交预约', shop.name + ' ' + doc.dept + ' ' + date + ' ' + time + ' ' + svc.name);
    Store.toast('预约成功');
    this.refresh();
  },
  cancel: function (e) {
    const id = e.currentTarget.dataset.id;
    const all = Store.get('appointments') || [];
    const a = all.find(function (x) { return x.id === id; });
    if (a) { a.status = '已取消'; }
    Store.set('appointments', all);
    Store.log('取消预约', id);
    Store.toast('预约已取消');
    this.refresh();
  }
});
