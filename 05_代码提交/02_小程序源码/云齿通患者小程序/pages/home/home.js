const Store = require('../../utils/store.js');

Page({
  data: {
    name: '', shopName: '', level: '', next: {}, pending: [], notices: [],
    entries: [
      { icon: '约', text: '在线预约', url: '/pages/book/book' },
      { icon: '费', text: '缴费收据', url: '/pages/billing/billing' },
      { icon: '员', text: '会员中心', url: '/pages/member/member' },
      { icon: '录', text: '就诊记录', url: '/pages/records/records' }
    ]
  },
  onShow: function () {
    const s = Store.guard();
    if (!s) return;
    const appts = Store.mine(Store.get('appointments')).map(function (a) {
      return Object.assign({}, a, { shopName: Store.shopName(a.shopId) });
    });
    const bills = Store.mine(Store.get('bills'));
    const mem = (Store.get('members') || []).find(function (m) { return m.patientId === s.patientId; }) || {};
    this.setData({
      name: s.name,
      shopName: Store.shopName(s.shopId),
      level: mem.level || '普通',
      next: appts[0] || {},
      pending: bills.filter(function (b) { return b.status === '待支付'; }),
      notices: Store.get('notices') || []
    });
  },
  go: function (e) { wx.navigateTo({ url: e.currentTarget.dataset.url }); },
  logout: function () {
    Store.log('退出登录', '');
    Store.set('session', {});
    wx.reLaunch({ url: '/pages/login/login' });
  }
});
