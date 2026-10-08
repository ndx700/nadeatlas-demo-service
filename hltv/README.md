# hltv/：战队库数据

由 ali 的抓取程序从 HLTV 抓取后写入，App 的战队库只读这里（经 jsDelivr 镜像，国内可直连）。
格式说明见需求文档；这里的文件现在是模板（index.json 里 "template": true），真实数据写入时去掉这一项。

- index.json：更新时间、战队列表、赛事列表
- teams/<队id>.json、events/<赛事id>.json、matches/<比赛id>.json
- img/teams/<队id>.png、img/players/<选手id>.png
