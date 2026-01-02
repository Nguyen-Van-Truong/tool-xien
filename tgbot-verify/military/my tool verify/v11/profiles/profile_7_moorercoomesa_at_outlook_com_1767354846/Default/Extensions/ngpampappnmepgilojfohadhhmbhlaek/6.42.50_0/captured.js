
let agent = typeof browser == 'undefined' ? chrome : browser;
let param = {};

for (let item of location.search.slice(1).split('&'))
{
    item = item.split('=', 2);
    param[item[0]] = item[1];
}

let back  = param.back;
let istop = window.self === window.top;

if (param.register && location.hash.length > 1)
{
    agent.runtime.sendMessage([ 44, location.hash.slice(1) ]);
    
    let url  = new URL(location);
    url.hash = '';
    
    history.replaceState(null, '', url);
    back = true;
}

if (back && istop)
{
    history.length > 1 ? history.back() : agent.runtime.sendMessage([ 38 ]);
}

function onContentLoad(event)
{
    if (param.register)
    {
        msgDownload.style.display = 'none';
        msgRegister.style.display = '';
    }
    else if (param.host)
    {
        strHostname.innerText = param.host;
        msgDownload.style.display = 'none';
        msgDnldFrom.style.display = '';
    }

    textThisYear.innerText = new Date().getFullYear();
}

document.addEventListener('DOMContentLoaded', onContentLoad);
