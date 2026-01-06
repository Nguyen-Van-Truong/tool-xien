YouTube的链接有点不一样，类似与https://offers.sheerid.com/youtube/student/?yrdup=https%3A%2F%2Fwww.youtube.com%2F%3Fsld%3Dxxxxxxxxxxxxxxxytpid=premium&ytsku=premium&yrsp=https%3A%2F%2Fwww.youtube.com%2Fpremium%2FstudxxxxxxxxxxxxQQBRgO&euid=230493635&locale=en-US&oid=AI97cxxxxxxxxxxxxxxxxxxxxxNT06Nb5kDzo384b8cAu

不存在SheerID的programId和verificationId信息，所以需要你自己抓一下接口

打开网络日志搜索`https://services.sheerid.com/rest/v2/verification/`
获取载荷里面的programId和响应的verificationId

手动组成链接
https://services.sheerid.com/verify/xxxxxxxxxx/?verificationId=yyyyyyyyyyy
这里面的xxx就是programId
yyyy是verificationId