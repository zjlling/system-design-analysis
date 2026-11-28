const Store = require('../../utils/store.js');

Page({
  data: { phone: '', password: '' },
  onLoad: function () { Store.init(); },
  onShow: function () {
    const s = Store.getObj('session');
    if (s && s.patientId) wx.reLaunch({ url: '/pages/home/home' });
  },
  onPhone: function (e) { this.setData({ phone: e.detail.value }); },
  onPassword: function (e) { this.setData({ password: e.detail.value }); },
  login: function () {
    const phone = (this.data.phone || '').trim();
    const pwd = this.data.password || '';
    if (!phone || !pwd) { Store.toast('请输入手机号和密码', 'none'); return; }
    const u = Store.ACCOUNTS.find(function (x) { return x.phone === phone && x.password === pwd; });
    if (!u) { Store.toast('手机号或密码错误', 'none'); return; }
    Store.set('session', {
      phone: u.phone, patientId: u.patientId, name: u.name, shopId: u.shopId
    });
    Store.set('role', 'patient');
    Store.log('登录', u.name);
    Store.toast('登录成功');
    setTimeout(function () { wx.reLaunch({ url: '/pages/home/home' }); }, 500);
  }
});
