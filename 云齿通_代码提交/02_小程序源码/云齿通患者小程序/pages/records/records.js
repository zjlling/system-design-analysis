const Store = require('../../utils/store.js');

Page({
  data: { list: [] },
  onShow: function () {
    if (!Store.guard()) return;
    const list = Store.mine(Store.get('records')).map(function (r) {
      return Object.assign({}, r, { shopName: Store.shopName(r.shopId) });
    });
    this.setData({ list: list });
    Store.log('查看本人就诊记录', '共 ' + list.length + ' 条');
  }
});
