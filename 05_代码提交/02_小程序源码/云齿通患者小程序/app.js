// 云齿通 CloudDent · 患者端小程序
const Store = require('./utils/store.js');

App({
  globalData: { appName: '云齿通 CloudDent', cloudConnected: false },
  onLaunch: function () {
    Store.init();
    // 开发者工具中勾选"不校验合法域名"后可拉取云端真实数据；失败自动用本地种子
    Store.syncCloud(function (ok) {
      Store.log(ok ? '云端数据同步成功' : '云端未连接，使用本地演示数据', '');
    });
  }
});
