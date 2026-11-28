const Store = require('../../utils/store.js');

Page({
  data: { pending: [], paid: [] },
  onShow: function () {
    if (!Store.guard()) return;
    this.refresh();
  },
  refresh: function () {
    const all = Store.mine(Store.get('bills')).map(function (b) {
      return Object.assign({}, b, { shopName: Store.shopName(b.shopId) });
    });
    this.setData({
      pending: all.filter(function (b) { return b.status === '待支付'; }),
      paid: all.filter(function (b) { return b.status === '已支付'; })
    });
  },
  pay: function (e) {
    const id = e.currentTarget.dataset.id;
    const method = e.currentTarget.dataset.method;
    const all = Store.get('bills') || [];
    const b = all.find(function (x) { return x.id === id; });
    if (!b) return;
    b.status = '已支付';
    b.method = method;
    b.receipt = 'RCP' + Date.now();
    Store.set('bills', all);
    Store.log('线上支付', b.billNo + ' · ' + method + ' · ¥' + b.amount);
    Store.toast('支付成功，收据已生成');
    this.refresh();
  }
});
