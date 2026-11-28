const Store = require('../../utils/store.js');

Page({
  data: { balance: 0, points: 0, level: '', cardNo: '', shopName: '', content: '', feedbacks: [] },
  onShow: function () {
    const s = Store.guard();
    if (!s) return;
    const m = (Store.get('members') || []).find(function (x) { return x.patientId === s.patientId; }) || {};
    this.setData({
      balance: m.balance || 0, points: m.points || 0, level: m.level || '普通',
      cardNo: m.cardNo || '—', shopName: Store.shopName(s.shopId),
      feedbacks: Store.mine(Store.get('feedbacks'))
    });
  },
  onInput: function (e) { this.setData({ content: e.detail.value }); },
  submit: function () {
    const s = Store.guard();
    const c = (this.data.content || '').trim();
    if (!c) { Store.toast('请填写反馈内容', 'none'); return; }
    const all = Store.get('feedbacks') || [];
    all.unshift({ id: 'FB' + Date.now(), patientId: s.patientId, date: '2026-11-14', content: c, reply: '' });
    Store.set('feedbacks', all);
    Store.log('提交就诊反馈', c.slice(0, 20));
    Store.toast('反馈已提交');
    this.setData({ content: '', feedbacks: Store.mine(all) });
  }
});
